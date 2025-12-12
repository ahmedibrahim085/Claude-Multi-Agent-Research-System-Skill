# Stop Hook Early Exit Bug - Fix

**Date:** 2025-12-11
**Issue:** Stop hook not logging "COMPLETED" or running cleanup when no active skill
**Root Cause:** Early exits before cleanup code
**Solution:** Move cleanup code BEFORE early exits

---

## The Bug

**Symptom:** Stop hook debug log shows entries like:
```
[2025-12-11T23:07:12.616227] Stop hook STARTED
[2025-12-11T23:07:12.616381] stdin read successfully
[2025-12-11T23:07:12.616427] Starting auto-reindex section
[2025-12-11T23:07:12.617177] reindex_on_stop() returned: skip - concurrent_reindex
```

**Missing:** No "Stop hook COMPLETED" line at the end!

**Impact:**
- ❌ Can't verify stop hook completed successfully
- ❌ Session reindex state NOT cleared between sessions
- ❌ May prevent first-prompt reindex from triggering on next session

---

## Root Cause

The stop hook had this code flow:

```python
# Section 1: Auto-reindex (ALWAYS runs)
reindex_manager.reindex_on_stop()

# Section 2: Skill completion tracking
current_skill = state_manager.get_current_skill()

if not current_skill:
    sys.exit(0)  # ← EARLY EXIT! Skips cleanup!

if current_skill.get('endTime'):
    sys.exit(0)  # ← EARLY EXIT! Skips cleanup!

# ... skill completion logic ...

# Section 3: Cleanup (NEVER REACHED if no skill!)
reindex_manager.clear_session_reindex_state()
with open(debug_log, 'a') as f:
    f.write("Stop hook COMPLETED\n\n")
```

**Problem:** When there's no active skill (common case!), the hook exits at line 150 BEFORE reaching the cleanup code at the end.

**Why this wasn't noticed earlier:** The early exits were always there, but became problematic when we added the `clear_session_reindex_state()` call that MUST run on every stop.

---

## The Solution

**Move cleanup code BEFORE early exits**, ensuring it ALWAYS runs:

```python
# Section 1: Auto-reindex (ALWAYS runs)
reindex_manager.reindex_on_stop()

# Section 2: Cleanup (ALWAYS runs, BEFORE early exits)
reindex_manager.clear_session_reindex_state()
with open(debug_log, 'a') as f:
    f.write("Stop hook COMPLETED\n\n")

# Section 3: Skill completion tracking (ONLY if skill active)
current_skill = state_manager.get_current_skill()

if not current_skill:
    sys.exit(0)  # Now OK - cleanup already done

if current_skill.get('endTime'):
    sys.exit(0)  # Now OK - cleanup already done

# ... skill completion logic ...
```

**Key Change:** Cleanup code moved from AFTER skill tracking to BEFORE it.

---

## Files Modified

**`.claude/hooks/stop.py`**

1. **Moved cleanup code** from lines 196-207 to lines 144-157
2. **Removed duplicate code** at the end
3. **Updated section comments** to reflect new order:
   - Section 1: Auto-reindex
   - Section 2: Cleanup (ALWAYS)
   - Section 3: Skill completion tracking (CONDITIONAL)

---

## Verification

After restarting Claude Code, the next stop hook execution should show:

```
[TIMESTAMP] Stop hook STARTED
[TIMESTAMP] stdin read successfully
[TIMESTAMP] Starting auto-reindex section
[TIMESTAMP] reindex_on_stop() returned: skip/run - REASON
[TIMESTAMP] Stop hook COMPLETED  ← THIS LINE MUST APPEAR!
```

✅ COMPLETED line appears even when no skill is active
✅ Session state is cleared on every stop
✅ First-prompt reindex will trigger on next session

---

## Impact

### Before Fix

- ❌ COMPLETED line missing when no active skill
- ❌ Session state NOT cleared (causes first-prompt reindex bug)
- ❌ Hard to debug hook execution issues

### After Fix

- ✅ COMPLETED line ALWAYS appears
- ✅ Session state ALWAYS cleared
- ✅ Clean state for next session guaranteed
- ✅ Better debugging visibility

---

## Related Issues

This bug was discovered while fixing the "first-prompt reindex not starting" bug. The `clear_session_reindex_state()` call was added as part of that fix, but was placed AFTER the early exits, making it ineffective.

This fix ensures the cleanup code runs ALWAYS, not just when there's an active skill.
