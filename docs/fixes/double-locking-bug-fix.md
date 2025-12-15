# Double-Locking Bug Fix - Clean Architectural Solution

> **📜 HISTORICAL DOCUMENT**
>
> **Status**: References deleted code from PostToolUse auto-reindex feature
>
> **Deleted (2025-12-15)**:
> - PostToolUse hook (`.claude/hooks/post-tool-use-track-research.py`)
> - Functions: `run_incremental_reindex_sync()`, `reindex_after_write()`, `should_reindex_after_write()`
> - Functions: `save_state()`, `validate_quality_gate()`, `set_current_skill()`, `identify_current_agent()`
>
> **Why Deleted**: Fast-fail optimization made post-write auto-reindex unnecessary
>
> **This Document**: Preserved for historical reference. Content below describes architecture/testing/analysis that existed before 2025-12-15.

---


**Date:** 2025-12-11
**Issue:** False "concurrent_reindex" detection in stop hook
**Root Cause:** Parent and subprocess both trying to manage the same lock
**Solution:** Clean separation of concerns - subprocess is sole lock owner

---

## The Bug

**Symptom:** Stop hook logs "concurrent_reindex" even when NO actual concurrent process is running.

**Evidence:**
- Forensic log shows NO concurrent operations
- No claim files exist
- No processes running incremental-reindex
- Yet stop-hook-debug.log shows: `reindex_on_stop() returned: skip - concurrent_reindex`

**User Impact:** Confusing logs, unclear why reindex is being skipped

---

## Root Cause Analysis

### Broken Architecture (BEFORE Fix)

**Two entities managing the SAME lock:**

1. **Parent** (`run_incremental_reindex_sync`):
   ```python
   lock_acquired = _acquire_reindex_lock(project_path, kill_if_held=kill_if_held)
   # Creates claim file with parent's PID

   proc = subprocess.Popen([script, project_path], ...)  # Spawns subprocess

   _release_reindex_lock(project_path)  # Releases lock
   ```

2. **Subprocess** (`incremental_reindex.py`):
   ```python
   lock_acquired = reindex_manager._acquire_reindex_lock(project_path, kill_if_held=False)
   # Tries to acquire SAME lock, sees parent's PID!

   if not lock_acquired:
       return {'skipped': True, 'reason': 'Another reindex running'}  # ← FALSE POSITIVE!
   ```

**The Problem:**
- Parent acquires lock (claim file contains parent's PID)
- Parent spawns subprocess
- Subprocess checks lock file, sees parent's PID
- Subprocess thinks another process is running
- Subprocess returns `skipped=True`
- Parent interprets this as "concurrent_reindex"
- **Result:** FALSE POSITIVE - no actual concurrent process!

### Architectural Flaw

**Violation of Single Responsibility Principle:**
- Lock ownership split between two processes
- Parent acquires lock → subprocess can't acquire it
- Subprocess sees parent's lock as "another process"

---

## The TRUE Solution: Clean Separation of Concerns

### New Architecture (AFTER Fix)

**Single lock owner: Subprocess only!**

**Parent's Responsibilities:**
1. Decide whether to kill existing processes (based on `kill_if_held` parameter)
2. Spawn subprocess
3. Wait for result
4. **NOT** acquire or manage locks

**Subprocess's Responsibilities:**
1. Acquire lock (atomic, single owner)
2. Run reindex
3. Release lock
4. Return result

**NO shared lock ownership!**

---

## Implementation Details

### 1. New Function: `_kill_existing_reindex_process()`

**Location:** `.claude/utils/reindex_manager.py` lines 393-558

**Purpose:** Parent-only function to kill existing processes WITHOUT acquiring lock

**Logic:**
```python
def _kill_existing_reindex_process(project_path: Path) -> bool:
    # Check if claim file exists
    if not claim_file.exists():
        return True  # No process running

    # Read PID from claim file
    pid = parse_pid_from_claim_file()

    # Verify process is incremental-reindex (safety check)
    if not verify_process(pid):
        return False  # Not our process, don't kill

    # Kill process (SIGTERM + SIGKILL)
    kill_process(pid)

    # Remove claim file
    claim_file.unlink()

    # Do NOT acquire new lock - subprocess will do that!
    return True
```

**Key Point:** This function kills the process and removes the claim file, but does NOT acquire a new lock. The subprocess will acquire the lock after being spawned.

### 2. Modified: `run_incremental_reindex_sync()`

**Location:** `.claude/utils/reindex_manager.py` lines 804-1036

**Changes:**

**REMOVED:**
- ❌ Lock acquisition (`_acquire_reindex_lock`)
- ❌ Lock release (`_release_reindex_lock`)

**ADDED:**
- ✅ Check if claim file exists
- ✅ If `kill_if_held=True`: Call `_kill_existing_reindex_process()`
- ✅ If `kill_if_held=False`: Skip if claim file exists

**New Logic:**
```python
def run_incremental_reindex_sync(project_path, kill_if_held=True, trigger='unknown'):
    # Check if claim file exists
    if claim_file.exists():
        if kill_if_held:
            # Kill existing process (does NOT acquire lock)
            killed = _kill_existing_reindex_process(project_path)
            if not killed:
                log_skip('failed_to_kill_existing')
                return None
            # Process killed, continue to spawn
        else:
            # Skip if process running
            log_skip('concurrent_reindex')
            return None

    # Spawn subprocess (subprocess will acquire lock)
    proc = subprocess.Popen([script, project_path], ...)

    # Wait for result
    stdout, stderr = proc.communicate(timeout=50)

    # No lock release needed - subprocess owns the lock!
```

### 3. Subprocess Lock Management (UNCHANGED)

**Location:** `.claude/skills/semantic-search/scripts/incremental_reindex.py` lines 679-756

**Subprocess correctly:**
```python
# Acquire lock with kill_if_held=False (skip if held)
lock_acquired = reindex_manager._acquire_reindex_lock(project_path, kill_if_held=False)

if not lock_acquired:
    # Another process has lock, skip
    print(json.dumps({'skipped': True}))
    sys.exit(0)

# Lock acquired - run reindex
try:
    result = indexer.auto_reindex()
finally:
    # Always release lock
    reindex_manager._release_reindex_lock(project_path)
```

---

## How It Works Now

### Scenario 1: No Existing Process (Normal Case)

**Stop hook calls with `kill_if_held=False`:**

1. Parent checks if claim file exists → NO
2. Parent spawns subprocess
3. Subprocess acquires lock (creates claim file with subprocess PID)
4. Subprocess runs reindex
5. Subprocess releases lock (removes claim file)
6. Subprocess returns result
7. Parent returns result to stop hook

**Result:** ✅ Reindex runs successfully, NO false positives!

### Scenario 2: Existing Process Running (kill_if_held=False)

**Stop hook calls with `kill_if_held=False`:**

1. Parent checks if claim file exists → YES
2. Parent sees `kill_if_held=False` → Skip immediately
3. Parent logs skip with reason='concurrent_reindex'
4. Parent returns None
5. Stop hook logs "skip - concurrent_reindex"

**Result:** ✅ Correctly skips when actual process is running!

### Scenario 3: Existing Process Running (kill_if_held=True)

**Post-tool-use calls with `kill_if_held=True`:**

1. Parent checks if claim file exists → YES
2. Parent sees `kill_if_held=True` → Calls `_kill_existing_reindex_process()`
3. Kill function: Verifies PID, kills process, removes claim file
4. Parent spawns subprocess
5. Subprocess acquires lock (claim file now available)
6. Subprocess runs reindex
7. Subprocess releases lock
8. Parent returns result

**Result:** ✅ Existing process killed, new reindex runs successfully!

---

## Verification

### Test 1: No Concurrent Process (Bug Case)

**Before Fix:**
```
Parent: Acquires lock (PID 12345)
Parent: Spawns subprocess
Subprocess: Tries to acquire lock, sees PID 12345
Subprocess: Returns {'skipped': True, 'reason': 'Another reindex running'}
Parent: Returns None
Stop hook: "skip - concurrent_reindex"  ← FALSE POSITIVE!
```

**After Fix:**
```
Parent: Checks claim file → NOT EXISTS
Parent: Spawns subprocess
Subprocess: Acquires lock (PID 12346)
Subprocess: Runs reindex
Subprocess: Releases lock
Subprocess: Returns {'success': True}
Parent: Returns True
Stop hook: "run - reindex_success"  ← CORRECT!
```

### Test 2: Actual Concurrent Process

**Before Fix:**
```
Process A: Running (PID 99999)
Parent: Tries to acquire lock → FAILS (Process A holds it)
Parent: Returns None
Stop hook: "skip - concurrent_reindex"  ← CORRECT
```

**After Fix:**
```
Process A: Running (PID 99999, claim file exists)
Parent: Checks claim file → EXISTS
Parent: kill_if_held=False → Skip
Parent: Returns None
Stop hook: "skip - concurrent_reindex"  ← CORRECT
```

**Both work correctly, but AFTER fix has cleaner architecture!**

---

## Benefits

### 1. Clean Separation of Concerns

**Parent:**
- ✅ Handles kill decisions
- ✅ Spawns subprocess
- ✅ Waits for result
- ❌ Does NOT manage locks

**Subprocess:**
- ✅ Acquires lock
- ✅ Runs reindex
- ✅ Releases lock
- ❌ Does NOT handle kill logic

### 2. No False Positives

- ✅ Subprocess can now acquire lock (parent doesn't hold it)
- ✅ "concurrent_reindex" only logged when ACTUAL concurrent process exists
- ✅ Forensic logs match reality

### 3. No Workarounds

- ❌ No `--skip-lock` parameters
- ❌ No parent PID checking
- ❌ No ignoring locks
- ✅ Pure architectural fix

### 4. Maintains All Features

- ✅ kill_if_held=True still works (post-tool-use)
- ✅ kill_if_held=False still works (stop hook)
- ✅ Concurrent process detection still works
- ✅ Lock safety maintained

---

## Code Changes Summary

### Files Modified

1. **`.claude/utils/reindex_manager.py`**
   - **Added:** `_kill_existing_reindex_process()` (lines 393-558)
   - **Modified:** `run_incremental_reindex_sync()` (lines 804-1036)
     - Removed lock acquisition/release
     - Added kill logic using new function
     - Added claim file check for skip logic

### Files Unchanged

2. **`.claude/skills/semantic-search/scripts/incremental_reindex.py`**
   - No changes needed!
   - Subprocess lock management already correct

---

## Testing

### Manual Test Commands

```bash
# Test 1: Normal reindex (should work without false positive)
# In one terminal:
python3 .claude/utils/reindex_manager.py  # Simulate stop hook call

# Test 2: Concurrent reindex (should correctly detect)
# In terminal 1:
.claude/skills/semantic-search/scripts/incremental-reindex . &
# In terminal 2:
python3 .claude/utils/reindex_manager.py  # Should skip correctly

# Test 3: kill-if-held (should kill and restart)
# In terminal 1:
.claude/skills/semantic-search/scripts/incremental-reindex . &
# In terminal 2:
python3 -c "from pathlib import Path; import sys; sys.path.insert(0, '.claude/utils'); import reindex_manager; reindex_manager.run_incremental_reindex_sync(Path.cwd(), kill_if_held=True)"
# Should kill process from terminal 1 and run new reindex
```

### Expected Results

**Test 1:** ✅ Reindex runs successfully, NO "concurrent_reindex" false positive
**Test 2:** ✅ Correctly skips with "concurrent_reindex" (real concurrent process)
**Test 3:** ✅ Kills existing process, runs new reindex

---

## Conclusion

**Problem:** Double-locking bug caused false "concurrent_reindex" detection

**Root Cause:** Parent and subprocess both managing the same lock

**Solution:** Clean architectural separation - subprocess is sole lock owner

**Result:**
- ✅ No false positives
- ✅ Clean code architecture
- ✅ All features maintained
- ✅ No workarounds needed

This is the TRUE architectural fix!
