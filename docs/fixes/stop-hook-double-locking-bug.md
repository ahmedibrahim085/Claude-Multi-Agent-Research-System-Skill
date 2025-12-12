# Stop Hook Double Locking Bug - Root Cause Analysis & Fix

**Date**: 2025-12-11
**Session**: session_20251211_145530
**Severity**: CRITICAL - Prevents stop hook reindex from working

---

## Executive Summary

**Bug**: Stop hook claims "reindex_success" but no actual reindex occurs.
**Root Cause**: Double locking - parent process acquires lock, subprocess also tries to acquire lock, sees it's held, skips work but returns success code.
**Impact**: Auto-reindex on stop hook is completely non-functional.
**Fix**: Add `--skip-lock` flag to incremental_reindex.py script.

---

## Evidence Timeline

**Test Session**: 2025-12-11 14:46:56 - 15:05:55

### Observation 1: Stop Hook Claims Success
```
[2025-12-11T15:00:36.317533] Stop hook STARTED
[2025-12-11T15:00:38.514265] reindex_on_stop() returned: run - reindex_success
```
- Duration: ~2 seconds
- Claimed: "reindex_success"

### Observation 2: Index Updated Much Later
```json
{
  "last_incremental_index": "2025-12-11T14:02:15.009099+00:00"
}
```
- Index timestamp: 14:02:15 UTC (15:02:15 local)
- Stop hook ran at: 14:00:38 UTC (15:00:38 local)
- Gap: **1 minute 37 seconds AFTER** stop hook claimed success

### Observation 3: Missing DEBUG Logs
Expected (from reindex_manager.py lines 690-692):
```python
print(f"DEBUG: Attempting to acquire lock for {project_path}", file=sys.stderr)
print(f"DEBUG: Lock acquired = {lock_acquired}", file=sys.stderr)
```

**Not seen in any logs** - because subprocess stderr is PIPED, not printed.

---

## Root Cause Analysis

### The Double Locking Problem

**Parent Process** (`reindex_manager.run_incremental_reindex_sync`):
```python
# Line 691: Acquire lock
lock_acquired = _acquire_reindex_lock(project_path)  # kill_if_held=True (default)

if not lock_acquired:
    return None

# Line 706-712: Launch subprocess
proc = subprocess.Popen(
    [str(script), str(project_path)],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,  # ← Captures stderr, never shown
    text=True,
    start_new_session=True
)

# Line 716: Wait for subprocess
stdout, stderr = proc.communicate(timeout=50)

# Line 718: Check return code
if proc.returncode == 0:
    return True  # ← Claims success

# Line 744: Release lock (finally block)
_release_reindex_lock(project_path)
```

**Subprocess** (`incremental_reindex.py`):
```python
# Line 673: Try to acquire lock
lock_acquired = reindex_manager._acquire_reindex_lock(project_path, kill_if_held=False)

if not lock_acquired:
    # Lock already held (by parent!)
    result = {
        'success': True,  # ← Says "success"
        'skipped': True,  # ← But actually skipped!
        'reason': 'Another reindex process is running'
    }
    print(json.dumps(result, indent=2))  # ← To stdout (captured by parent)
    sys.exit(0)  # ← Exit code 0 (success)
```

**Parent Continues**:
```python
# Line 718: Sees returncode 0
if proc.returncode == 0:
    return True  # ← Thinks reindex succeeded!
```

**Result**:
1. Parent acquires lock
2. Parent launches subprocess
3. Subprocess sees lock held (by parent!), skips, returns code 0
4. Parent sees code 0, thinks success
5. **No actual reindex occurred**
6. Stop hook logs "reindex_success" (FALSE CLAIM)

---

## Why Cooldown Check Kept Failing

**Expected**: After 5+ minutes, cooldown should expire and reindex should run.

**Actual**: Stop hook at 15:05:55 (317 seconds elapsed) still skipped with "cooldown_active".

**Explanation**: The cooldown check reads `last_incremental_index` from `index_state.json`, which still shows 15:02:15 because:
1. The stop hook at 15:00:38 CLAIMED success but did NO work
2. The actual reindex happened at 15:02:15 (triggered by something else, probably first-prompt)
3. So at 15:05:55, elapsed time since REAL last reindex (15:02:15) is only **3 min 40 sec**
4. Cooldown (5 minutes) not expired → Skip

---

## The Fix (UPDATED - Original --skip-lock approach was wrong)

### ❌ WRONG Solution: Add `--skip-lock` Flag (Attempted but failed)

This was my first attempt, which made things WORSE:
- Added --skip-lock flag to skip lock acquisition
- Subprocess did full reindex work (3-10 min)
- Timed out after 50 seconds
- Result: Failure instead of false success

### ✅ CORRECT Solution: Skip-If-Running Mode

**File 1**: `.claude/skills/semantic-search/scripts/incremental_reindex.py`

Add argument:
```python
parser.add_argument('--skip-lock', action='store_true',
                   help='Skip lock acquisition (used when parent process holds lock)')
```

Modify lock acquisition:
```python
if not args.skip_lock:
    lock_acquired = reindex_manager._acquire_reindex_lock(project_path, kill_if_held=False)

    if not lock_acquired:
        result = {
            'success': True,
            'skipped': True,
            'reason': 'Another reindex process is running'
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)
else:
    # Parent holds lock, skip acquisition
    lock_acquired = True
```

**File 2**: `.claude/utils/reindex_manager.py`

Modify subprocess call (line 707):
```python
proc = subprocess.Popen(
    [str(script), str(project_path), '--skip-lock'],  # ← Add flag
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    start_new_session=True
)
```

---

## Testing Plan

### Test 1: Verify Fix Works
1. Clear cooldown: `rm ~/.claude_code_search/projects/*/index_state.json`
2. Trigger stop hook (send message, wait for response)
3. Check logs: Should see "run - reindex_success"
4. Check timestamp: Should be updated IMMEDIATELY (not 1.5 min later)
5. Verify elapsed calculation uses correct timestamp

### Test 2: Verify Cooldown Works
1. Wait 5+ minutes after reindex
2. Trigger stop hook
3. Should run reindex (cooldown expired)
4. Log should show "run - reindex_success"

### Test 3: Verify Background Mode Still Works
1. Trigger first-prompt reindex (background)
2. Immediately trigger Write operation
3. Second reindex should skip (lock held by background)
4. Log should show "skip - concurrent_reindex"

---

## Expected Behavior After Fix

### Timeline 1: Stop Hook Runs Reindex
```
[15:00:36] Stop hook STARTED
[15:00:36] Acquiring lock (kill-and-restart mode)
[15:00:36] Lock acquired, launching subprocess with --skip-lock
[15:00:36] Subprocess sees --skip-lock, skips lock acquisition
[15:00:36] Subprocess performs actual reindex work...
[15:00:38] Subprocess completes, updates index_state.json timestamp
[15:00:38] Subprocess exits with code 0
[15:00:38] Parent sees success, releases lock
[15:00:38] Stop hook logs: reindex_on_stop() returned: run - reindex_success
```

**Verification**: `index_state.json` timestamp should be 15:00:38 (or very close)

### Timeline 2: Stop Hook Skips (Cooldown Active)
```
[15:03:00] Stop hook STARTED
[15:03:00] Check cooldown: last reindex 15:00:38, elapsed 2min 22sec
[15:03:00] Cooldown (5min) not expired, skip
[15:03:00] Stop hook logs: reindex_on_stop() returned: skip - cooldown_active
```

**Verification**: No subprocess launched, no lock acquisition

---

## Additional Fixes Needed

### Fix 1: Show stderr from subprocess

Current code captures stderr but only shows it on error. For debugging, we should always show it:

```python
stdout, stderr = proc.communicate(timeout=50)

# ALWAYS show stderr for visibility
if stderr:
    print(stderr, file=sys.stderr, end='')

if proc.returncode == 0:
    return True
```

### Fix 2: Validate subprocess output

Current code trusts returncode 0. Should parse stdout JSON to verify actual success:

```python
if proc.returncode == 0:
    try:
        result = json.loads(stdout)
        if result.get('skipped'):
            # Subprocess skipped work but returned 0
            print(f"⚠️  Subprocess skipped: {result.get('reason')}", file=sys.stderr)
            return None
        return True
    except json.JSONDecodeError:
        # No JSON output, assume success
        return True
```

---

## Lessons Learned

1. **Never trust exit codes alone** - Validate actual work was done
2. **Don't hide subprocess stderr** - Always show for debugging
3. **Test end-to-end** - Unit tests passed, but integration failed
4. **Verify timestamps** - Use utility scripts, never mental math
5. **Double locking is subtle** - Parent and child both trying to lock

---

## Status

- [x] Root cause identified
- [ ] Fix designed
- [ ] Fix implemented
- [ ] Tests written
- [ ] Tests passed
- [ ] Deployed to production
- [ ] Verified in real session
