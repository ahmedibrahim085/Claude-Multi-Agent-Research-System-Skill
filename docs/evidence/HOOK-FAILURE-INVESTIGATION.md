# Hook Failure Investigation Report
**Date**: 2025-12-15 11:26 UTC
**Session**: Current session (started ~01:52 UTC)
**Investigator**: Claude (evidence-based analysis)

## Executive Summary

**CRITICAL FINDING**: Automatic reindex hooks (first-prompt, stop) have STOPPED WORKING.

- ✅ **user-prompt-submit.py**: Working (confirmed by system reminders)
- ❌ **first-prompt-reindex.py**: NOT firing
- ❌ **stop.py**: NOT firing since Dec 13, 15:23 UTC
- ❓ **post-write hook**: Deprecated, needs removal

---

## Evidence Timeline

### Last 20 Reindex Operations (from logs/reindex-operations.jsonl)

```
2025-12-14 12:08:42 UTC | start | trigger=script-direct
2025-12-14 12:15:27 UTC | start | trigger=script-direct
2025-12-14 12:23:01 UTC | start | trigger=script-direct
2025-12-14 12:27:16 UTC | end   | (corresponding)
2025-12-14 12:27:49 UTC | start | trigger=script-direct
2025-12-14 12:32:07 UTC | end   | (corresponding)
2025-12-14 20:22:12 UTC | start | trigger=script-direct
2025-12-14 20:26:46 UTC | end   | (corresponding)
2025-12-14 23:16:08 UTC | start | trigger=script-direct
2025-12-14 23:16:11 UTC | end   | (corresponding)
2025-12-15 00:54:40 UTC | start | trigger=script-direct  ← Agent spawn (me)
2025-12-15 00:59:19 UTC | end   | (corresponding)
2025-12-15 09:50:09 UTC | start | trigger=script-direct  ← My test
2025-12-15 09:50:15 UTC | end   | (corresponding)
2025-12-15 09:50:23 UTC | start | trigger=script-direct  ← My test
2025-12-15 09:50:28 UTC | end   | (corresponding)
2025-12-15 10:10:57 UTC | start | trigger=script-direct  ← My test
2025-12-15 10:10:59 UTC | end   | (corresponding)
2025-12-15 10:11:07 UTC | start | trigger=script-direct  ← My test
2025-12-15 10:11:08 UTC | end   | (corresponding)
```

**Key Finding**: ALL 20 recent triggers are `script-direct`
- **ZERO** `first-prompt` triggers
- **ZERO** `stop-hook` triggers
- **ZERO** `session-start` triggers

### Last Stop Hook Execution (from logs/stop-hook-debug.log)

```
[2025-12-13T15:02:36] Stop hook STARTED
[2025-12-13T15:02:36] reindex_on_stop_background() returned: run - reindex_spawned

[2025-12-13T15:07:26] Stop hook STARTED
[2025-12-13T15:07:26] reindex_on_stop_background() returned: skip - cooldown_active

[2025-12-13T15:23:33] Stop hook STARTED  ← LAST EXECUTION
[2025-12-13T15:23:33] reindex_on_stop_background() returned: run - reindex_spawned
```

**Last stop hook execution**: Dec 13, 15:23:33 UTC
**Current time**: Dec 15, 11:26 UTC
**Time since last execution**: **44 hours** (1 day, 20 hours)

**Expected**: Stop hook should fire after every assistant response
**Actual**: No stop hook executions for 44 hours

### Current Session Evidence

**Session Start Time**: ~01:52 UTC (Dec 15)
**Current Time**: 11:26 UTC (Dec 15)
**Session Duration**: ~9.5 hours

**Expected Behavior**:
1. First prompt should trigger `first-prompt-reindex.py`
2. Stop hook should trigger after each response

**Actual Behavior**:
1. NO first-prompt trigger in logs
2. NO stop hook executions in 44 hours
3. Only manual script calls (`trigger=script-direct`)

### User-Prompt-Submit Hook

**Status**: ✅ WORKING

**Evidence**: System reminders in conversation:
```
<system-reminder>
UserPromptSubmit:Callback hook success: Success
</system-reminder>
```

This proves user-prompt-submit.py IS being called, but first-prompt-reindex.py is NOT.

---

## Root Cause Analysis

### Hypothesis 1: Hooks Not Configured

**Checked**:
- ✅ Hook files exist in `.claude/hooks/`
- ❌ No `hooks_config.json` found
- ❌ No Claude Code settings.json found
- ✅ HOOKS_SETUP.md exists with configuration instructions

**Likely Cause**: Hooks may need to be manually configured in Claude Code settings.

### Hypothesis 2: Hook Event Subscription Issue

**Theory**: first-prompt-reindex.py and stop.py may not be subscribed to their events.

**Evidence**:
- user-prompt-submit.py fires (UserPromptSubmit event)
- first-prompt-reindex.py doesn't fire (should fire on UserPromptSubmit)
- stop.py doesn't fire (should fire on Stop event)

**Conclusion**: Event subscription is broken or hooks are not registered.

### Hypothesis 3: Hook Naming Convention Changed

**Checked**:
- first-prompt-reindex.py (exists, executable)
- stop.py (exists, executable)

**Note**: First-prompt hook may need to be named differently or registered separately.

---

## Impact Assessment

### Severity: **CRITICAL**

**What's Broken**:
1. ❌ **No automatic reindexing** since Dec 13
2. ❌ **First-prompt background reindex** not working
3. ❌ **Stop hook reindex** not working
4. ❌ **6-hour cooldown system** untested (hooks not firing)
5. ❌ **Kill-and-restart protection** untested (hooks not firing)

**What Still Works**:
1. ✅ Manual reindex via script
2. ✅ Incremental reindex logic
3. ✅ Cache system
4. ✅ user-prompt-submit.py hook
5. ✅ Index creation and search

**User Impact**:
- Index is 44 hours out of date (last automatic update: Dec 13)
- No automatic updates on code changes
- Manual intervention required for every reindex

---

## Deprecated Hooks (User Report)

### Post-Write Hook

**Status**: Deprecated
**Reason**: Too aggressive (triggered on every file write)
**Replacement**: Stop hook (triggers after assistant completes)
**Action Required**: Remove if exists

**Search Result**: No `post-write` hooks found in logs/reindex-operations.jsonl

---

## Recommended Actions

### Immediate (P0)

1. **Verify hook configuration** in Claude Code settings
   - Check if hooks need manual registration
   - Verify event subscriptions

2. **Add debug logging** to first-prompt-reindex.py
   - Create logs/first-prompt-debug.log
   - Track why hook isn't firing

3. **Test hook execution manually**
   - Run first-prompt-reindex.py with mock input
   - Run stop.py with mock input
   - Verify they can execute successfully

### Short-term (P1)

4. **Remove deprecated post-write hooks** (if any exist)

5. **Create integration test** for hooks
   - Test first-prompt trigger
   - Test stop hook trigger
   - Test cooldown mechanism

6. **Document hook configuration** requirements
   - Update HOOKS_SETUP.md with troubleshooting
   - Add verification script

### Long-term (P2)

7. **Add health checks** for hook system
   - Verify hooks fire as expected
   - Alert if hooks stop working
   - Self-healing mechanism

---

## Test Plan

### Test 1: Manual Hook Execution

```bash
# Test first-prompt hook
echo '{}' | python3 .claude/hooks/first-prompt-reindex.py

# Test stop hook
echo '{"transcript": "test"}' | python3 .claude/hooks/stop.py

# Check for errors
```

### Test 2: Event Trigger Verification

1. Start new session
2. Check if first-prompt hook fires
3. Complete a response
4. Check if stop hook fires
5. Verify logs/stop-hook-debug.log updates

### Test 3: Cooldown Mechanism

1. Trigger stop hook multiple times rapidly
2. Verify cooldown prevents spam
3. Check logs for cooldown messages

---

## Next Steps

1. ✅ Document evidence (this file)
2. ⏳ Test hooks manually (in progress)
3. ⏳ Fix hook registration
4. ⏳ Verify end-to-end
5. ⏳ Create commit with fixes
6. ⏳ Run integration tests

---

## Appendix: File Locations

```
Hooks:
- .claude/hooks/first-prompt-reindex.py
- .claude/hooks/stop.py
- .claude/hooks/user-prompt-submit.py
- .claude/hooks/session-start.py
- .claude/hooks/session-end.py
- .claude/hooks/post-tool-use-track-research.py

Logs:
- logs/reindex-operations.jsonl
- logs/stop-hook-debug.log
- logs/state/semantic-search-prerequisites.json

Scripts:
- .claude/skills/semantic-search/scripts/incremental-reindex
- .claude/utils/reindex_manager.py
```

---

**Conclusion**: Automatic hooks have failed. Manual reindexing still works. Need to fix hook registration/configuration and add comprehensive tests before claiming system is operational.
