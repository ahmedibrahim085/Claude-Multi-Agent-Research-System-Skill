# Stop-Hook Migration - Testing Checklist
**Date:** 2025-12-12
**Status:** Ready for User Testing
**Completion:** Phase 1 ✅ | Phase 2 ⏳ | Phase 3 ⏳

---

## Implementation Summary

### ✅ Completed Work
1. **NEW:** Created `reindex_on_stop_background()` with 8 sections (lines 1168-1369)
2. **UPDATED:** stop.py calls new function (line 117)
3. **UPDATED:** stop.py message handling for "reindex_spawned" (lines 129-141)
4. **FIXED:** Claim file path bug (uses correct storage_dir)
5. **REMOVED:** 277 lines of dead code (3 functions)

### ⏳ Pending: Systematic Testing

---

## Phase 2: Systematic Testing (60-90 minutes)

### Test 1: Background Spawn Verification
**Objective:** Verify stop hook returns immediately (<5s) and spawns background process

**Steps:**
1. Make a trivial file change (add comment to test file)
2. Stop Claude Code session
3. Check logs immediately

**Expected Results:**
```bash
# logs/stop-hook-debug.log
[timestamp] Stop hook STARTED
[timestamp] reindex_on_stop_background() returned: run - reindex_spawned
[timestamp] Stop hook COMPLETED
# Duration: <5 seconds

# Console output
✅ Stop hook: Index update spawned in background

# logs/reindex-operations.jsonl
{"event": "start", "trigger": "stop-hook", "mode": "background", "pid": XXXXX}
```

**Success Criteria:**
- ✅ Stop hook completes in <5 seconds
- ✅ Decision is "run - reindex_spawned"
- ✅ START event logged in forensic logs
- ✅ Process appears in `ps aux | grep incremental`

**If Failed:**
- Check logs/stop-hook-debug.log for errors
- Verify spawn_background_reindex() is working
- Check if script path is correct

---

### Test 2: Concurrent Detection
**Objective:** Verify stop hook detects running reindex and prevents orphaned START events

**Steps:**
1. Start long-running manual reindex:
   ```bash
   bash .claude/skills/semantic-search/scripts/incremental-reindex . &
   ```
2. While running, stop Claude Code session
3. Check logs

**Expected Results:**
```bash
# logs/stop-hook-debug.log
[timestamp] reindex_on_stop_background() returned: skip - concurrent_reindex

# logs/reindex-operations.jsonl
{"event": "start", "trigger": "stop-hook", "skipped": true, "skip_reason": "concurrent_reindex"}
# NO orphaned START event (has skip_reason)

# Console output
⏭️  Stop hook: Auto-reindex skipped (concurrent_reindex)
```

**Success Criteria:**
- ✅ Decision is "skip - concurrent_reindex"
- ✅ START event has skipped=true and skip_reason
- ✅ NO orphaned START event (verify END event later)
- ✅ Manual reindex continues uninterrupted

**If Failed:**
- Check claim file path (should be ~/.claude_code_search/.../reindex_claim)
- Verify PID verification logic in Section 4
- Check if get_project_storage_dir() returns correct path

---

### Test 3: Cooldown Enforcement
**Objective:** Verify stop hook respects 300s cooldown between reindexes

**Steps:**
1. Trigger stop hook (stop Claude Code)
2. Wait 10 seconds (< 300s cooldown)
3. Restart and immediately stop Claude Code again
4. Check logs

**Expected Results:**
```bash
# First call
[timestamp] reindex_on_stop_background() returned: run - reindex_spawned

# Second call (10s later)
[timestamp] reindex_on_stop_background() returned: skip - cooldown_active

# Second call details should show:
{
  "decision": "skip",
  "reason": "cooldown_active",
  "details": {
    "cooldown_seconds": 300,
    "elapsed_seconds": 10,
    "remaining_seconds": 290
  }
}
```

**Success Criteria:**
- ✅ First call spawns successfully
- ✅ Second call skips with cooldown_active
- ✅ elapsed_seconds ~10, remaining_seconds ~290
- ✅ No second reindex spawned

**If Failed:**
- Check get_reindex_config() returns correct cooldown
- Verify should_reindex_after_cooldown() logic
- Check last_reindex timestamp calculation

---

### Test 4: Background Completion
**Objective:** Verify background reindex completes successfully in 200-350s

**Steps:**
1. Trigger stop hook (spawns background reindex)
2. Note START event PID and timestamp
3. Wait 6 minutes (allow completion)
4. Check forensic logs for END event

**Expected Results:**
```bash
# logs/reindex-operations.jsonl
{"event": "start", "trigger": "stop-hook", "pid": XXXXX, "timestamp": "12:00:00"}
# ... 200-350 seconds later ...
{"event": "end", "operation_id": "reindex_..._XXXXX", "status": "completed", "duration_seconds": 210.5}
```

**Success Criteria:**
- ✅ START event logged with mode=background
- ✅ END event logged after 200-350 seconds
- ✅ Status is "completed" (not failed or timeout)
- ✅ Duration matches expected range (3-6 minutes)
- ✅ Process no longer in `ps aux` after completion

**If Failed:**
- Check if process timed out (no 50s limit in background mode)
- Verify script's finally block runs (logs END event)
- Check for errors in process output

---

## Phase 3: Final Verification (20-30 minutes)

### End-to-End Integration Test
**Objective:** Verify complete workflow from first-prompt through stop-hook

**Scenario:**
```
1. Start fresh session → First-prompt reindex (background)
   ↓
2. Stop hook during first-prompt → skip (concurrent)
   ↓
3. Wait for first-prompt completion → END event
   ↓
4. Stop again → spawns successfully
   ↓
5. Wait for completion → END event
```

**Steps:**
1. Start fresh Claude Code session (triggers first-prompt)
2. Send one message, immediately stop (triggers stop hook)
3. Check logs: stop hook should skip (concurrent with first-prompt)
4. Wait 6 minutes, check: first-prompt END event
5. Restart, stop immediately (triggers stop hook again)
6. Check logs: stop hook should spawn (no concurrent, cooldown may apply)
7. Wait 6 minutes, check: stop hook END event

**Expected Log Sequence:**
```jsonl
{"event": "start", "trigger": "first-prompt", "pid": 1001, "timestamp": "T+0s"}
{"event": "start", "trigger": "stop-hook", "skipped": true, "skip_reason": "concurrent_reindex", "timestamp": "T+10s"}
{"event": "end", "operation_id": "...1001", "status": "completed", "duration": 210, "timestamp": "T+220s"}
{"event": "start", "trigger": "stop-hook", "pid": 1002, "timestamp": "T+240s"}
{"event": "end", "operation_id": "...1002", "status": "completed", "duration": 205, "timestamp": "T+445s"}
```

**Success Criteria:**
- ✅ No orphaned START events (every START has END or skip_reason)
- ✅ Concurrent detection works (stop hook skips during first-prompt)
- ✅ Background completion works (both reindexes complete)
- ✅ No 50s timeout failures
- ✅ All business logic preserved (prerequisites, cooldown, concurrent)

---

### Performance Verification
**Objective:** Verify no performance regression

**Metrics to Check:**
```bash
# Stop hook execution time (should be <5s)
grep "Stop hook STARTED" logs/stop-hook-debug.log -A 2 | tail -10

# Background reindex duration (should be 200-350s)
grep "event.*end.*stop-hook" logs/reindex-operations.jsonl | tail -5
```

**Expected Results:**
- ✅ Stop hook: <5 seconds (not 50 seconds)
- ✅ Background reindex: 200-350 seconds
- ✅ No timeout failures in logs
- ✅ User sees immediate "spawned in background" message

---

## Code Review Checklist

### Implementation Fidelity
- ✅ Uses `get_project_root()` NOT `Path.cwd()` (line 1236)
- ✅ Uses `get_reindex_config()` NOT hardcoded `300` (line 1237)
- ✅ Structured details dicts (not plain strings)
- ✅ Calculates `elapsed_seconds` and `remaining_seconds` (lines 1243-1256)
- ✅ Error `print()` statement in exception handler (line 1363)
- ✅ Concurrent PID check uses correct path (lines 1267-1268)

### Dead Code Removal
- ✅ Old `reindex_on_stop()` removed (was lines 1828-1955)
- ✅ `auto_reindex_on_session_start()` removed (was lines 1646-1713)
- ✅ `_reindex_on_session_start_core()` removed (was lines 1962-2021)
- ✅ No orphaned references remain (grep verified)

### Hook Integration
- ✅ stop.py line 117 calls `reindex_on_stop_background()`
- ✅ stop.py lines 129-141 handle "reindex_spawned" code
- ✅ Debug logging updated (line 121)

---

## Testing Status

| Test | Status | Notes |
|------|--------|-------|
| Background Spawn | ⏳ Pending | User testing required |
| Concurrent Detection | ⏳ Pending | User testing required |
| Cooldown Enforcement | ⏳ Pending | User testing required |
| Background Completion | ⏳ Pending | User testing required |
| End-to-End Integration | ⏳ Pending | User testing required |
| Performance Verification | ⏳ Pending | User testing required |

---

## Quick Test Commands

```bash
# Test 1: Background spawn
# (Stop Claude Code session, check logs)
tail -20 logs/stop-hook-debug.log
tail -10 logs/reindex-operations.jsonl

# Test 2: Concurrent detection
bash .claude/skills/semantic-search/scripts/incremental-reindex . &
# (Stop Claude Code, check logs)
tail -20 logs/stop-hook-debug.log | grep concurrent

# Test 3: Cooldown
# (Stop twice rapidly, check second call)
tail -20 logs/stop-hook-debug.log | grep cooldown

# Test 4: Background completion
# (Wait 6 minutes after spawn)
grep "event.*end.*stop-hook" logs/reindex-operations.jsonl | tail -1

# Check running reindex processes
ps aux | grep incremental

# Check claim file
cat ~/.claude_code_search/projects/Claude-Multi-Agent-Research-System-Skill_*/\.reindex_claim
```

---

## Success Criteria Summary

### Must Have (All Required)
- ✅ No 50s timeout failures
- ✅ Background reindex completes successfully (200-350s)
- ✅ No orphaned START events in forensic logs
- ✅ Concurrent detection prevents duplicate spawns
- ✅ Cooldown prevents spam on rapid restarts
- ✅ All business logic preserved
- ✅ Dead code removed (277 lines)

### Nice to Have
- ✅ Performance: <5s stop hook execution
- ✅ Clear user messages
- ✅ Clean forensic logs

---

## Next Steps for User

1. **Review** this checklist
2. **Execute** Test 1 (Background Spawn) - simplest verification
3. **Execute** Test 2 (Concurrent Detection) - critical for preventing bugs
4. **Execute** Test 3 (Cooldown) - verify business logic
5. **Execute** Test 4 (Background Completion) - verify no timeout
6. **Execute** End-to-End test - complete workflow
7. **Report** any failures or unexpected behavior
8. **Approve** migration if all tests pass

---

**Testing Prepared By:** Claude (Self-Review)
**User Action Required:** Execute testing checklist above
**Estimated Testing Time:** 90-120 minutes (includes waiting for background completion)
