# Compaction Bug Fix - Session State Management

## Problem Statement

**Bug:** First-prompt hook incorrectly triggered reindex on compaction/continuation sessions.

**Root Cause:** Context compaction creates new session_id, causing `initialize_session_state()` to reset `first_semantic_search_shown = False`, which triggered first-prompt reindex even though it wasn't a fresh restart.

## Solution

Differentiate between fresh restart and compaction using SessionStart's `source` parameter.

### Source Parameter Values

From Claude Code hooks documentation:
- `source='startup'` → Fresh Claude Code launch
- `source='clear'` → User used `/clear` command
- `source='resume'` → Session resumed/compacted

### Fix Logic

**Reset flag (trigger reindex):**
- `source='startup'` → Fresh restart
- `source='clear'` → User cleared, fresh start

**Preserve flag (no reindex):**
- `source='resume'` → Compaction/continuation
- `source='unknown'` → Unknown state (safe default)

## Implementation

### File: `.claude/utils/reindex_manager.py`

**Function:** `initialize_session_state(source: str = 'unknown')`

**Key Changes:**
```python
# Determine if we should reset the first-prompt flag
should_reset = source in ['startup', 'clear']

if is_new_session:
    state["session_id"] = session_id

    if should_reset:
        # Fresh restart - reset flag to allow first-prompt reindex
        state["first_semantic_search_shown"] = False
    else:
        # Compaction/resume - preserve existing flag state
        if "first_semantic_search_shown" not in state:
            state["first_semantic_search_shown"] = True  # Safe default
```

### File: `.claude/hooks/session-start.py`

**Changes:**
```python
# Extract source parameter
source = input_data.get('source', 'unknown')

# Pass to initialize_session_state
reindex_manager.initialize_session_state(source=source)
```

## Edge Cases Handled

| Scenario | is_new_session | source | should_reset | Result |
|----------|----------------|--------|--------------|--------|
| First time ever | True | startup | True | Reset flag ✅ |
| Fresh restart | True | startup | True | Reset flag ✅ |
| Compaction | True | resume | False | Preserve flag ✅ |
| User /clear | True | clear | True | Reset flag ✅ |
| Unknown source | True | unknown | False | Preserve flag (safe) ✅ |
| Same session | False | (any) | (n/a) | No change ✅ |
| Missing flag | True | resume | False | Default to True (safe) ✅ |

## Verification

### Test Scenario 1: Fresh Restart
```bash
# Start Claude Code fresh
claude

# Check state file
cat logs/state/session-reindex-tracking.json
# Should show: "first_semantic_search_shown": false

# First prompt should trigger reindex
# Check logs/reindex-operations.jsonl for:
{"trigger": "first-prompt", ...}
```

### Test Scenario 2: Compaction
```bash
# Continue conversation until compaction happens
# (context reaches ~95% capacity)

# After compaction, check state file
cat logs/state/session-reindex-tracking.json
# Should show: "first_semantic_search_shown": true (preserved)

# Next prompt should NOT trigger reindex
# logs/reindex-operations.jsonl should NOT have new first-prompt entry
```

### Test Scenario 3: /clear Command
```bash
# Use /clear during session
/clear

# Check state file
cat logs/state/session-reindex-tracking.json
# Should show: "first_semantic_search_shown": false (reset like startup)

# First prompt after clear should trigger reindex
```

## Debug Logging

The fix includes debug logging to stderr:

**On reset:**
```
DEBUG: Session state reset (source=startup, session=session_20251211_205800)
```

**On preserve:**
```
DEBUG: Session state preserved (source=resume, session=session_20251211_210500, shown=true)
```

Check stderr output to verify correct behavior.

## Impact

**Before Fix:**
- Compaction → New session_id → Flag reset → Spurious reindex ❌
- User confused: "Why is it reindexing again?"
- Wasted resources on unnecessary reindex

**After Fix:**
- Compaction → New session_id → Flag preserved → No reindex ✅
- Only fresh restart triggers reindex
- Clean separation of concerns

## Related Documentation

- [Reindex Operation Logging](../diagnostics/reindex-operation-logging.md) - Track all reindex operations
- [SessionStart Hook Reference](https://code.claude.com/docs/en/hooks) - Official hook documentation
