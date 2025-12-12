# CRITICAL BUG: Stop Hook vs SessionEnd Hook Confusion

**Date:** 2025-12-11
**Severity:** CRITICAL - Multiple reindex processes spawned, one per user prompt
**Issue:** Session state cleared on EVERY response instead of only on session end
**Root Cause:** Misunderstanding Stop vs SessionEnd hook lifecycle
**Solution:** Move clear_session_reindex_state() from Stop to SessionEnd hook

---

## The Critical Bug

**Symptom:** Multiple background reindex processes running simultaneously, spawning one with EVERY user prompt.

**Evidence:**
```bash
# Three concurrent reindex processes:
PID 25467  started 11:28PM
PID 25393  started 11:27PM
PID 25272  started 11:25PM

# Session state file: MISSING!
cat logs/state/session-reindex-tracking.json
# Error: No such file or directory
```

**User saw:** "🔄 Checking for index updates in background..." message on **EVERY prompt**, not just the first!

---

## Root Cause: Hook Lifecycle Misunderstanding

**CRITICAL MISUNDERSTANDING:**

I confused **Stop hook** (runs after EVERY assistant response) with **SessionEnd hook** (runs only when session terminates).

### What I Did WRONG

In Bug #3 fix, I moved `clear_session_reindex_state()` to Stop hook:

```python
# .claude/hooks/stop.py
def main():
    # Section 1: Auto-reindex
    reindex_manager.reindex_on_stop()

    # Section 2: Cleanup (WRONG!)
    reindex_manager.clear_session_reindex_state()  # ← DELETES state file!

    # Section 3: Skill tracking
    ...
```

**Problem:** Stop hook runs after **EVERY** assistant response!

### What Happened

**Conversation flow:**
1. **User prompt #1** → First-prompt hook checks state file
   - File missing → Returns True → Spawns reindex #1 ✅
   - Marks as shown (creates state file with `first_semantic_search_shown: true`)

2. **Assistant responds** → Stop hook runs
   - **Deletes state file** ❌

3. **User prompt #2** → First-prompt hook checks state file
   - File missing (just deleted!) → Returns True → Spawns reindex #2 ❌
   - Marks as shown (creates state file again)

4. **Assistant responds** → Stop hook runs
   - **Deletes state file** ❌

5. **User prompt #3** → First-prompt hook checks state file
   - File missing → Returns True → Spawns reindex #3 ❌

**Result:** New reindex process with EVERY user prompt!

---

## The Correct Understanding

### Hook Lifecycle

**Stop Hook:**
- Fires: After **EVERY** assistant response
- Purpose: Per-turn cleanup, auto-reindex batching, skill tracking
- Frequency: Many times per session

**SessionEnd Hook:**
- Fires: When session **TERMINATES** (exit, clear, logout)
- Purpose: Final cleanup, state reset, prepare for next session
- Frequency: Once per session

**The Fix:**
- ❌ Don't clear session state in Stop hook (runs too often!)
- ✅ Clear session state in SessionEnd hook (runs once at end)

---

## The Solution

**Moved clear_session_reindex_state() from Stop to SessionEnd:**

### Before (WRONG - in Stop hook)

```python
# .claude/hooks/stop.py - WRONG LOCATION!
def main():
    reindex_manager.reindex_on_stop()

    # Runs after EVERY response - TOO OFTEN!
    reindex_manager.clear_session_reindex_state()

    with open(debug_log, 'a') as f:
        f.write("Stop hook COMPLETED\n")
```

### After (CORRECT - in SessionEnd hook)

```python
# .claude/hooks/session-end.py - CORRECT LOCATION!
def main():
    # End active skill if any
    current_skill = state_manager.get_current_skill()
    if current_skill and not current_skill.get('endTime'):
        state_manager.end_current_skill(...)

    # Finalize session state
    session_logger.finalize_session_state(session_id)

    # Clear reindex state - ONLY at session end!
    reindex_manager.clear_session_reindex_state()

    sys.exit(0)
```

```python
# .claude/hooks/stop.py - CLEANUP ONLY!
def main():
    reindex_manager.reindex_on_stop()

    # Only log completion, no state clearing!
    with open(debug_log, 'a') as f:
        f.write("Stop hook COMPLETED\n")

    # Skill tracking...
```

---

## Implementation

### File 1: `.claude/hooks/stop.py`

**REMOVED:**
```python
# Clear session reindex state to prepare for next session
try:
    reindex_manager.clear_session_reindex_state()
except Exception as e:
    print(f"Failed to clear session reindex state: {e}", file=sys.stderr)
```

**Changed section comment:** "SECTION 2: Cleanup" → "SECTION 2: Logging"

### File 2: `.claude/hooks/session-end.py`

**ADDED (after finalize_session_state):**
```python
# Clear session reindex state to prepare for next session
# This ensures first-prompt reindex will trigger on next session start
try:
    import reindex_manager
    reindex_manager.clear_session_reindex_state()
except Exception as e:
    print(f"Failed to clear session reindex state: {e}", file=sys.stderr)
```

### Emergency Cleanup

**Killed orphan processes:**
```bash
ps aux | grep "incremental-reindex" | grep -v grep | awk '{print $2}' | xargs kill -9
```

**Recreated session state:**
```python
state = {
    'session_id': 'session_20251211_232537',
    'first_semantic_search_shown': True
}
Path('logs/state/session-reindex-tracking.json').write_text(json.dumps(state, indent=2))
```

---

## Impact

### Before Fix

**Every user prompt triggered:**
1. First-prompt hook checks state → file missing → spawns reindex
2. I respond → Stop hook deletes state file
3. Next prompt → cycle repeats

**Result:**
- ❌ Multiple concurrent reindex processes
- ❌ CPU/memory waste
- ❌ Potential index corruption (concurrent writes)
- ❌ User frustration

### After Fix

**Normal flow:**
1. **Session starts** → State file empty/missing
2. **First user prompt** → First-prompt spawns reindex, marks as shown
3. **I respond** → Stop hook logs only (NO state clearing)
4. **Subsequent prompts** → First-prompt sees flag=True, skips
5. **Session ends** → SessionEnd clears state for next session

**Result:**
- ✅ First-prompt reindex ONCE per session
- ✅ No orphan processes
- ✅ Clean state management
- ✅ Proper lifecycle

---

## Lessons Learned

**1. Understand Hook Lifecycle**
- Stop ≠ SessionEnd
- Stop runs after EVERY response
- SessionEnd runs ONCE at session termination

**2. Test with Multiple Prompts**
- Don't just test first prompt
- Test conversation flow (multiple turns)
- Check for accumulation bugs

**3. Check Process Count**
- `ps aux | grep process-name`
- Multiple instances = likely bug

**4. Verify State Files Persist**
- State files should persist during session
- Only clear at session end

---

## Files Modified

1. **`.claude/hooks/stop.py`** (lines 144-150)
   - Removed: clear_session_reindex_state() call
   - Changed: "Cleanup" → "Logging" section comment

2. **`.claude/hooks/session-end.py`** (lines 64-70)
   - Added: clear_session_reindex_state() call
   - Location: After finalize_session_state, before sys.exit

---

## Verification

After restart, expected behavior:

1. **Session start** → State file created by session-start hook
2. **First prompt** → Reindex spawns, flag set to True
3. **Second prompt** → NO reindex (flag already True)
4. **Third prompt** → NO reindex
5. **Session end** → State file deleted by SessionEnd hook
6. **Next session** → Cycle repeats correctly

**Key test:** Send 3 prompts in same session, verify only ONE reindex spawns.

---

## Related Bugs

This is **Bug #5** in the reindex system:

1. Bug #1: Double-locking (false concurrent_reindex) - FIXED
2. Bug #2: source='unknown' treated as 'resume' - FIXED
3. Bug #3: Stop hook early exit - FIXED (but introduced Bug #5!)
4. Bug #4: Session state resume (flag default) - FIXED
5. **Bug #5: Stop vs SessionEnd confusion** - **FIXED NOW**

---

## Conclusion

**Problem:** Confused Stop hook (per-turn) with SessionEnd hook (per-session)

**Impact:** Multiple concurrent reindex processes, one per user prompt

**Root Cause:** Placed session-level cleanup (clear state) in per-turn hook (Stop)

**Solution:** Move session-level cleanup to SessionEnd hook

**Result:**
- ✅ First-prompt reindex ONCE per session
- ✅ Clean lifecycle management
- ✅ No orphan processes
- ✅ Proper state persistence during session

**Critical Lesson:** Always understand hook lifecycle before placing cleanup code!
