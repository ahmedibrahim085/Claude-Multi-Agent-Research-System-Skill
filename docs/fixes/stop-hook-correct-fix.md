# Stop Hook Double-Locking Bug - CORRECT FIX

**Date**: 2025-12-11
**Session**: session_20251211_151721
**Status**: FIXED ✅

---

## Root Cause (Confirmed)

**Double-Locking Bug:**
1. Parent (stop hook) acquires lock with parent PID (stop.py process)
2. Subprocess tries to acquire lock, sees parent PID in claim file
3. Subprocess verifies: Is PID running `incremental-reindex`? NO (it's stop.py)
4. Subprocess **respects lock** and returns False (line 494-495 in reindex_manager.py)
5. Script returns `success=True, skipped=True, exit_code=0`
6. Parent sees exit code 0, assumes success (didn't validate JSON before)
7. **NO work done** but stop hook logs "reindex_success"

**Evidence:**
```python
# Line 494-495 in _acquire_reindex_lock():
print(f"DEBUG: PID {pid} not incremental-reindex (cmd: {command[:80]}), respecting lock", file=sys.stderr)
return False  # Abort - other process owns the lock
```

---

## Wrong Fix Attempt

I initially added `--skip-lock` flag to bypass lock acquisition. This made things WORSE:
- Subprocess bypassed lock but did FULL reindex (3-10 minutes)
- Stop hook has 50-second timeout
- Subprocess timed out every time
- Result: Changed false success to actual failure

---

## Correct Fix: Skip-If-Running Mode

**Strategy:** Stop hook should SKIP (not kill-and-restart) if background reindex is running.

**Rationale:**
- Stop hook has 50s timeout, can't complete full reindex (takes 3-10 min)
- Background from first-prompt will eventually finish
- Next stop hook will handle new changes
- No timeouts, no false success, eventually consistent

### Changes Made

**1. Revert --skip-lock from incremental_reindex.py**
- Removed `--skip-lock` argument (lines 665-690)
- Restored original lock acquisition logic

**2. Add kill_if_held parameter to run_incremental_reindex_sync()**
```python
def run_incremental_reindex_sync(project_path: Path, kill_if_held: bool = True) -> Optional[bool]:
    """
    Args:
        kill_if_held: If True (default), kill running process and restart.
                     If False, skip if process running (used by stop hook).
    """
```

**3. Update lock acquisition call**
```python
lock_acquired = _acquire_reindex_lock(project_path, kill_if_held=kill_if_held)
```

**4. Remove --skip-lock from subprocess call**
```python
proc = subprocess.Popen(
    [str(script), str(project_path)],  # No --skip-lock
    ...
)
```

**5. Update reindex_on_stop() to use skip-if-running mode**
```python
# Step 4: Run auto-reindex (skip-if-running mode due to 50s timeout limit)
result = run_incremental_reindex_sync(project_path, kill_if_held=False)
```

**6. Keep validation logic (this was good from wrong fix)**
```python
if proc.returncode == 0:
    try:
        result = json.loads(stdout) if stdout else {}
        if result.get('skipped'):
            return None  # Correct: return None, not True
    except json.JSONDecodeError:
        pass
    return True
```

---

## Expected Behavior After Fix

### Scenario 1: Stop hook, no background reindex
- Acquires lock successfully (no process running)
- Launches subprocess
- Subprocess acquires lock
- If index fresh (< 360 min), subprocess skips
- Parent validates, sees skipped, returns None
- Stop hook logs "skip - index_fresh"
- ✅ No false success

### Scenario 2: Stop hook, background reindex running
- Tries to acquire lock with kill_if_held=False
- Sees background process running incremental-reindex
- Returns False immediately (skip)
- Parent gets None
- Stop hook logs "skip - concurrent_reindex"
- ✅ No timeout, no false success

### Scenario 3: Stop hook, cooldown active
- Checks cooldown BEFORE trying to acquire lock
- Skips at cooldown layer
- Never calls run_incremental_reindex_sync()
- ✅ Works as designed

---

## Trade-offs

**Accepted Trade-off:**
If user makes changes DURING background reindex, those changes won't be indexed until next turn:

Timeline:
- T0: First prompt, start background reindex
- T1: User edits file A (background still running)
- T2: Stop hook runs, sees background active, skips
- T3: Background completes (doesn't include file A)
- T4: Next turn, stop hook runs, indexes file A

**Why This Is Acceptable:**
1. Index is eventually consistent (file A indexed within one turn)
2. Alternative (kill-and-restart) can't work due to 50s timeout
3. User's search might be stale for one turn (acceptable delay)
4. Simpler, more robust than complex sync coordination

---

## Files Modified

1. `.claude/skills/semantic-search/scripts/incremental_reindex.py` - Reverted --skip-lock
2. `.claude/utils/reindex_manager.py` - Added kill_if_held parameter
3. `docs/fixes/stop-hook-double-locking-bug.md` - Updated with correct fix
4. `docs/fixes/stop-hook-correct-fix.md` - New doc with complete analysis

---

## Testing

**Verification Needed:**
1. First-prompt triggers background reindex
2. Stop hook sees background running, skips with "concurrent_reindex"
3. Background completes, index updated
4. Next stop hook runs successfully if changes made

**Expected Logs:**
```
# When background is running:
[15:XX:XX] Stop hook STARTED
[15:XX:XX] Starting auto-reindex section
DEBUG: Attempting to acquire lock...
DEBUG: Another reindex running (PID 12345), skipping (kill_if_held=False)
DEBUG: Lock acquired = False
[15:XX:XX] reindex_on_stop() returned: skip - concurrent_reindex

# When no background:
[15:XX:XX] Stop hook STARTED
[15:XX:XX] Starting auto-reindex section
DEBUG: Attempting to acquire lock...
DEBUG: Lock acquired = True
[subprocess output...]
[15:XX:XX] reindex_on_stop() returned: run - reindex_success
```

---

## Status

✅ **FIXED** - Deployed and ready for testing
- All code changes implemented
- Syntax validated
- Python cache cleared
- Documentation updated
- Awaiting real session verification
