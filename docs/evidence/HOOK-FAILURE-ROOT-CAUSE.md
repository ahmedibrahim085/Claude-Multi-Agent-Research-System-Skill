# Hook Failure Root Cause Analysis
**Investigation Date**: 2025-12-15 11:35 UTC
**Investigator**: Claude (evidence-based git forensics)

## Executive Summary

**ROOT CAUSE FOUND**: `.claude/settings.json` was deleted on Dec 13, 21:16 UTC (commit 9d5c2ac), breaking hook registrations for `first-prompt-reindex.py` and `stop.py`.

---

## Timeline of Events (Evidence-Based)

### Dec 12, 16:32 UTC - Commit f053892
**What happened**: First-prompt architecture implemented
- Created: `first-prompt-reindex.py`
- Updated: `stop.py` for background mode
- Updated: `session-start.py` for state init only
- `.claude/settings.json` **EXISTED** with full hook registrations

**Git Evidence**:
```bash
$ git show f053892 --stat
.claude/hooks/first-prompt-reindex.py |   86 ++
.claude/hooks/stop.py                 |   79 +-
.claude/utils/reindex_manager.py      | 1542 ++++++++++++
```

### Dec 13, 15:23 UTC - Last Working Stop Hook
**What happened**: Stop hook executed successfully
**Log Evidence** (`logs/stop-hook-debug.log`):
```
[2025-12-13T15:23:33.201203] Stop hook STARTED
[2025-12-13T15:23:33.201305] stdin read successfully
[2025-12-13T15:23:33.201335] Starting auto-reindex section
[2025-12-13T15:23:33.206192] reindex_on_stop_background() returned: run - reindex_spawned
[2025-12-13T15:23:33.206442] Stop hook COMPLETED
```

**Status**: ✅ All hooks working at this time

### Dec 13, 21:16 UTC - Commit 9d5c2ac (6 hours later)
**What happened**: `.claude/settings.json` DELETED

**Git Evidence**:
```bash
$ git show 9d5c2ac --stat -- .claude/settings.json
.claude/settings.json | 69 ---------------------------------------------------
1 file changed, 69 deletions(-)
```

**Commit Message** (MISLEADING):
```
Files Removed:
- .claude/settings.json: Claude-mem project-specific config (plugin bug prevents it working)
```

**Reality**: This file was NOT just for claude-mem! It contained ALL hook registrations:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-submit.py\""
          },
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/first-prompt-reindex.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop.py\""
          }
        ]
      }
    ],
    ...
  }
}
```

### Dec 13-15 - No Hook Executions
**What happened**: 44 hours with NO stop hook executions

**Log Evidence** (`logs/reindex-operations.jsonl` - last 20 operations):
```
ALL triggers: "script-direct" (manual)
ZERO triggers: "first-prompt"
ZERO triggers: "stop-hook"
```

**Last reindex**:
```json
{
  "timestamp": "2025-12-13T15:23:33+00:00",  ← Last stop hook
  "event": "start",
  "trigger": "stop-hook"
}
```

**No more automatic triggers** since deletion.

---

## What Was Lost

### Before Deletion (Working Configuration)

```json
{
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:github.com)",
      "WebFetch(domain:www.anthropic.com)",
      "WebFetch(domain:medium.com)",
      "WebFetch(domain:claude.com)"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-submit.py\""
          },
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/first-prompt-reindex.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-track-research.py\""
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop.py\""
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session-end.py\""
          }
        ]
      }
    ]
  }
}
```

### After Deletion (Broken)

**File**: None (deleted)
**Hooks working**: ❓ Unclear (possibly auto-discovery for some hooks)
**Hooks broken**: first-prompt-reindex.py, stop.py

---

## Why User-Prompt-Submit Still Works

**Mystery**: System reminders show:
```
<system-reminder>
UserPromptSubmit:Callback hook success: Success
</system-reminder>
```

**Possible explanations**:
1. ✅ **Auto-discovery**: Claude Code auto-discovers `user-prompt-submit.py` by filename
2. ❓ **Global config**: Registered in global Claude Code settings (but ~/.config/claude-code/ is empty)
3. ❓ **Fallback mechanism**: Claude Code has fallback for UserPromptSubmit hook

**Evidence needed**: Test if other hooks work with just filename, or if registration is required.

---

## Impact Assessment

### What's Broken

| Hook | File Exists | Before Deletion | After Deletion | Impact |
|------|-------------|----------------|----------------|---------|
| **first-prompt-reindex.py** | ✅ | ✅ Working | ❌ Not firing | No auto-reindex on first prompt |
| **stop.py** | ✅ | ✅ Working | ❌ Not firing | No auto-reindex after responses |
| **user-prompt-submit.py** | ✅ | ✅ Working | ✅ Still works? | Skill enforcement working |
| **session-start.py** | ✅ | ✅ Working | ✅ Still works? | Session init working |
| **post-tool-use-track-research.py** | ✅ | ✅ Working | ❓ Unknown | Research tracking unknown |
| **session-end.py** | ✅ | ✅ Working | ❓ Unknown | Session end unknown |

### What Still Works

- ✅ Manual reindex (`./scripts/incremental-reindex`)
- ✅ Incremental reindex logic
- ✅ Cache system
- ✅ Search functionality
- ✅ Skill enforcement (user-prompt-submit.py)

### What's Missing

- ❌ **Automatic background reindex** on first prompt (44 hours without)
- ❌ **Automatic reindex** after assistant responses (44 hours without)
- ❌ **Cooldown protection** (untested - hooks not firing)
- ❌ **Concurrent execution prevention** (untested - hooks not firing)

---

## Fix Required

### Immediate Action

**Restore settings.json** from commit 9d5c2ac^:
```bash
git show 9d5c2ac^:.claude/settings.json > .claude/settings.json
```

### Validation Required

After restore:
1. ✅ Test first-prompt hook fires (new session)
2. ✅ Test stop hook fires (after response)
3. ✅ Verify log entries appear
4. ✅ Test cooldown mechanism (5 minutes)
5. ✅ Test concurrent protection
6. ✅ Run end-to-end integration test

---

## Lessons Learned

### What Went Wrong

1. ❌ **Misunderstood file purpose**: Thought settings.json was only for claude-mem
2. ❌ **No testing after deletion**: Didn't verify hooks still worked
3. ❌ **No end-to-end tests**: Would have caught this immediately
4. ❌ **No monitoring**: Hook failures went unnoticed for 44 hours

### What Should Have Happened

1. ✅ **Check file content** before deletion (contains 5 hook registrations!)
2. ✅ **Test after changes** (run session, verify hooks fire)
3. ✅ **Monitor logs** (check reindex-operations.jsonl for triggers)
4. ✅ **Have integration tests** (automated verification)

---

## Evidence Checklist

| Evidence Type | Source | Status | Finding |
|---------------|--------|--------|---------|
| Git history | `git log -- .claude/settings.json` | ✅ Found | Deleted Dec 13, 21:16 UTC |
| File content | `git show 9d5c2ac^:.claude/settings.json` | ✅ Found | Full hook configuration |
| Stop hook log | `logs/stop-hook-debug.log` | ✅ Found | Last execution Dec 13, 15:23 UTC |
| Reindex log | `logs/reindex-operations.jsonl` | ✅ Found | No auto triggers since deletion |
| Commit message | `git show 9d5c2ac` | ✅ Found | Misleading ("claude-mem only") |
| Timeline | Log timestamps vs commit time | ✅ Verified | 6 hour gap confirms causation |

---

## Next Steps

1. ⏳ **Restore settings.json** (in progress)
2. ⏳ **Test restored hooks**
3. ⏳ **Run integration tests**
4. ⏳ **Add monitoring**
5. ⏳ **Create commit** with evidence
6. ⏳ **Update documentation**

---

**Conclusion**: The deletion of `.claude/settings.json` on Dec 13 broke hook registrations for first-prompt and stop hooks, causing 44 hours of no automatic reindexing. The file must be restored to fix the issue.
