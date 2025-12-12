# Session ID Change Bug Fix

**Date:** 2025-12-12
**Severity:** CRITICAL
**Symptom:** Multiple concurrent reindex processes spawning on restarts
**Root Cause:** `initialize_session_state()` preserving flag when session_id changes
**Fix:** Always reset flag when session_id changes, regardless of source parameter

---

## The Problem

When user restarts Claude Code:
1. Claude Code calls SessionStart hook with `source='resume'`
2. Session ID changes: `session_20251212_153542` → `session_20251212_154437`
3. `initialize_session_state()` sees:
   - `is_new_session = True` (session_id changed)
   - `source = 'resume'` (Claude Code parameter)
   - OLD LOGIC: "resume + old session exists → preserve flag"
4. Flag stays `true` → `should_show_first_prompt_status()` returns `False`
5. **BUG:** First-prompt hook doesn't trigger on NEW sessions
6. **WORSE:** Stop-hook triggers instead, spawning multiple processes

## Evidence

```bash
# State file had OLD session
$ cat logs/state/session-reindex-tracking.json
{
  "session_id": "session_20251212_153542",
  "first_semantic_search_shown": true
}

# But actual current session was DIFFERENT
$ python3 -c "import session_logger; print(session_logger.get_session_id())"
session_20251212_154437

# Result: Flag never reset, first-prompt never triggered
```

## The Flaw in Old Logic

```python
# OLD (WRONG) - Line 1819
should_reset = source in ['startup', 'clear', 'unknown'] or old_session_id is None

if is_new_session:
    if should_reset:
        state["first_semantic_search_shown"] = False  # Reset
    else:
        # WRONG: Preserving flag for NEW session!
        # This happens when source='resume' and old_session exists
        pass  # Flag stays True
```

**The mistake:** Treated `source='resume'` as "same session continuation" even when `session_id` changed.

**Why it's wrong:**
- `source='resume'` means "context continuation" (e.g., from compaction)
- But if `session_id` changed, it's a NEW session, not a continuation
- NEW session should ALWAYS reset flag, regardless of how Claude Code labels it

## The Fix

```python
# NEW (CORRECT) - Line 1817-1821
if is_new_session:
    # CRITICAL FIX: If session_id changed, ALWAYS reset flag
    # - New session = fresh start, regardless of source parameter
    # - source='resume' just means "context continuation", but if session_id changed,
    #   it's still a NEW session that should trigger first-prompt reindex
    state["session_id"] = session_id
    state["first_semantic_search_shown"] = False  # ALWAYS reset
    print(f"DEBUG: Session state reset - NEW SESSION (source={source}, old={old_session_id}, new={session_id})", file=sys.stderr)
```

**Why it's correct:**
- `session_id` change = NEW session (definitive proof)
- Source parameter is just Claude Code's label (not authoritative)
- First-prompt should trigger once per session (session_id defines session)

## Impact

**Before fix:**
- Multiple restarts → flag stuck at `True`
- First-prompt never triggers
- Stop-hook spawns processes instead
- **Result:** 3+ concurrent processes running simultaneously

**After fix:**
- Each restart with new session_id → flag resets to `False`
- First-prompt triggers exactly once per session
- Stop-hook sees concurrent process → skips correctly
- **Result:** Only ONE reindex process at a time

## Testing

```bash
# Test session-start hook manually
$ python3 .claude/hooks/session-start.py <<'EOF'
{"source": "resume"}
EOF

# Output (after fix):
DEBUG: Session state reset - NEW SESSION (source=resume, old=session_20251212_153542, new=session_20251212_154451)

# Verify state file
$ cat logs/state/session-reindex-tracking.json
{
  "session_id": "session_20251212_154451",
  "first_semantic_search_shown": false  ✅ RESET!
}
```

## Related Bugs

This fix also resolves:
1. **Multiple first-prompt triggers** - Flag was stuck, so multiple prompts thought they were "first"
2. **Concurrent process spam** - Stop-hook became the trigger instead of first-prompt
3. **Session state desync** - State file had wrong session_id

## Files Changed

- `.claude/utils/reindex_manager.py` (lines 1808-1821)
  - Removed complex `should_reset` logic
  - Simplified: new session_id = always reset

---

**Status:** ✅ FIXED
**Testing:** Manual verification successful
**User Testing:** Awaiting restart test
