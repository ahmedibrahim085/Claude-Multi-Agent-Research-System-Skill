# Reindex Operation Logging System

## Overview

Comprehensive forensic diagnostic logging system for tracking all reindex operations across the project.

## Log File

**Location:** `logs/reindex-operations.jsonl`
**Format:** JSONL (one JSON object per line)
**Purpose:** Track every reindex operation from start to finish with full diagnostic information

## Event Types

### START Event
Logged when a reindex operation begins (or is skipped).

**Fields:**
- `timestamp`: ISO 8601 UTC timestamp
- `event`: "start"
- `operation_id`: Unique ID (format: `reindex_{YYYYMMDD_HHMMSS}_{trigger}_{pid}`)
- `trigger`: Source that initiated the reindex
  - `first-prompt`: First user prompt after session start
  - `stop-hook`: Conversation turn ended
  - `post-tool-use`: File Write/Edit operation
  - `session-start`: Session start hook (deprecated, use first-prompt)
  - `script-direct`: Manual script invocation
- `session_id`: Session ID (e.g., `session_20251211_205800`)
- `pid`: Process ID
- `ppid`: Parent process ID
- `mode`: Execution mode (`background` or `sync`)
- `kill_if_held`: Lock mode flag
- `skipped`: Boolean - whether operation was skipped
- `skip_reason`: Reason for skipping (if skipped=true)
  - `concurrent_reindex`: Another reindex already running
  - `cooldown_active`: Too soon after last reindex
  - `prerequisites_not_ready`: Setup not complete
  - `index_not_found`: No existing index

### END Event
Logged when a reindex operation completes (success, failure, or timeout).

**Fields:**
- `timestamp`: ISO 8601 UTC timestamp
- `event`: "end"
- `operation_id`: Matches START event operation_id
- `session_id`: Session ID when operation ended (may differ from start for long operations)
- `start_timestamp`: ISO timestamp when operation started
- `duration_seconds`: Total duration in seconds
- `status`: Final status
  - `completed`: Finished successfully
  - `failed`: Error occurred
  - `timeout`: Exceeded 50-second timeout
- `exit_code`: Process exit code (0=success, 1=error, -1=killed)
- `index_updated`: Boolean - whether index was successfully updated
- `files_changed`: Number of files changed (if available)
- `error_message`: Error description (if status=failed)

## Trigger Points

### 1. First-Prompt Hook
- **File:** `.claude/hooks/first-prompt-reindex.py`
- **Trigger:** First user prompt after session start
- **Mode:** Background
- **Logging:** START event with trigger='first-prompt'

### 2. Stop Hook
- **File:** `.claude/hooks/stop.py` (via `reindex_on_stop()`)
- **Trigger:** Conversation turn ended
- **Mode:** Sync (50s timeout)
- **Logging:** START + END events with trigger='stop-hook'

### 3. Post-Tool-Use Hook
- **File:** `.claude/hooks/post-tool-use-track-research.py` (via `reindex_after_write()`)
- **Trigger:** Write/Edit/NotebookEdit operations
- **Mode:** Sync (50s timeout)
- **Logging:** START + END events with trigger='post-tool-use'

### 4. Direct Script Invocation
- **File:** `.claude/skills/semantic-search/scripts/incremental_reindex.py`
- **Trigger:** Manual `./incremental-reindex PROJECT_PATH` command
- **Mode:** Background
- **Logging:** START + END events with trigger='script-direct'

## Log Analysis

### Find Active Operations
```python
import reindex_manager

active_ops = reindex_manager.get_active_reindex_operations()
for op in active_ops:
    print(f"PID {op['pid']}: {op['trigger']} (started {op['timestamp']})")
```

### Query Operations by Trigger
```bash
grep '"trigger": "first-prompt"' logs/reindex-operations.jsonl
```

### Find Failed Operations
```bash
grep '"status": "failed"' logs/reindex-operations.jsonl | python3 -m json.tool
```

### Track Operation Lifecycle
```bash
# Find START event
grep '"operation_id": "reindex_20251211_205800_first-prompt_12345"' logs/reindex-operations.jsonl | grep '"event": "start"'

# Find matching END event
grep '"operation_id": "reindex_20251211_205800_first-prompt_12345"' logs/reindex-operations.jsonl | grep '"event": "end"'
```

### Check Session Continuity
```bash
# Find all operations started in one session but ended in another
python3 << 'PYEOF'
import json
from pathlib import Path

log_file = Path("logs/reindex-operations.jsonl")
operations = {}

with open(log_file) as f:
    for line in f:
        event = json.loads(line)
        op_id = event['operation_id']

        if event['event'] == 'start':
            operations[op_id] = {'start_session': event['session_id']}
        elif event['event'] == 'end' and op_id in operations:
            operations[op_id]['end_session'] = event['session_id']

# Find cross-session operations
for op_id, sessions in operations.items():
    if 'end_session' in sessions and sessions['start_session'] != sessions['end_session']:
        print(f"{op_id}:")
        print(f"  Started: {sessions['start_session']}")
        print(f"  Ended: {sessions['end_session']}")
PYEOF
```

## Diagnostic Scenarios

### "Why did my reindex not run?"
Check for skip events:
```bash
grep '"skipped": true' logs/reindex-operations.jsonl | tail -5 | python3 -m json.tool
```

### "Which hook triggered this reindex?"
```bash
grep '"pid": 12345' logs/reindex-operations.jsonl | grep '"event": "start"' | python3 -c "import json, sys; print(json.load(sys.stdin)['trigger'])"
```

### "How long did the reindex take?"
```bash
grep '"operation_id": "YOUR_OP_ID"' logs/reindex-operations.jsonl | grep '"event": "end"' | python3 -c "import json, sys; print(f\"{json.load(sys.stdin)['duration_seconds']:.1f} seconds\")"
```

### "Did the operation complete in the same session?"
```bash
# Compare session_id in START vs END events
grep '"operation_id": "YOUR_OP_ID"' logs/reindex-operations.jsonl | python3 -c "
import json, sys
events = [json.loads(line) for line in sys.stdin]
start = next(e for e in events if e['event'] == 'start')
end = next((e for e in events if e['event'] == 'end'), None)
print(f\"Started: {start['session_id']}\")
if end:
    print(f\"Ended: {end['session_id']}\")
    print(f\"Same session: {start['session_id'] == end['session_id']}\")
"
```

## Integration with Existing Logs

This logging system complements existing logs:
- **Session Logs:** `logs/session_{id}_tool_calls.jsonl` - Tool call history
- **Stop Hook Log:** `logs/stop-hook-debug.log` - Stop hook decisions
- **Reindex Operations:** `logs/reindex-operations.jsonl` - Complete reindex lifecycle (NEW)

Together, these provide complete forensic traceability of all reindex operations.
