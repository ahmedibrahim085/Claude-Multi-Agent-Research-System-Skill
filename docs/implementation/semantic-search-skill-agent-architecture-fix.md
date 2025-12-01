# Semantic-Search Skill & Agent Architecture Fix

**Date**: 2025-12-01
**Issue**: Skill was using old bash orchestration instead of agent architecture
**Root Cause**: User-level skill (`~/.claude/skills/semantic-search`) had outdated orchestration instructions

---

## Problem Identified

1. **Claude Code loaded user-level skill**, not project-level skill
2. **User-level skill had OLD bash orchestration** (direct script execution)
3. **I (Claude) was spawning agents**, not the skill orchestrator
4. **Agent names were inconsistent** (using "general-purpose" instead of actual agent names)
5. **Orchestrator naming inconsistent** with research/spec skills

---

## Files Modified

### 1. User-Level Skill: `~/.claude/skills/semantic-search/SKILL.md`

**Changes**:
- ✅ Replaced bash orchestration with agent architecture (lines 20-106)
- ✅ Added decision table for which agent to spawn
- ✅ Added 4 spawn examples with correct patterns
- ✅ Updated `allowed-tools` from `Bash, Read, Glob, Grep` to `Task, Read, Glob`
- ✅ Fixed all spawn examples to use correct `subagent_type` names:
  - ❌ OLD: `subagent_type="general-purpose"`
  - ✅ NEW: `subagent_type="semantic-search-reader"` or `subagent_type="semantic-search-indexer"`

### 2. Project-Level Skill: `./.claude/skills/semantic-search/SKILL.md`

**Changes**:
- ✅ Fixed spawn examples to use correct `subagent_type` names (4 examples)

### 3. Session Logger: `.claude/utils/session_logger.py`

**Changes**:
- ✅ Fixed orchestrator agent ID naming (line 171):
  - ❌ OLD: `return 'SEMANTIC-SEARCH'`
  - ✅ NEW: `return 'SEMANTIC-SEARCH-ORCHESTRATOR'`

---

## Correct Agent Naming

### Agent Types (internal identifiers)
- `semantic-search-orchestrator` - Skill orchestrator
- `semantic-search-reader` - READ operations agent
- `semantic-search-indexer` - WRITE operations agent

### Agent IDs (display in logs)
- `SEMANTIC-SEARCH-ORCHESTRATOR` - Skill orchestrator
- `SEMANTIC-READER` - READ operations agent
- `SEMANTIC-INDEXER` - WRITE operations agent

**Consistency with Other Skills**:
- ✅ Research: `RESEARCH-ORCHESTRATOR` → `RESEARCHER-1`, `RESEARCHER-2`, `REPORT-WRITER`
- ✅ Spec: `SPEC-ORCHESTRATOR` → `spec-analyst`, `spec-architect`, `spec-planner`
- ✅ Semantic-Search: `SEMANTIC-SEARCH-ORCHESTRATOR` → `SEMANTIC-READER`, `SEMANTIC-INDEXER`

---

## Correct Workflow (How It Should Work)

### User Invokes Skill
```
User: "find the function responsible for getting indexing status"
```

### Skill Orchestrator Activates
```
[Skill loads from ~/.claude/skills/semantic-search/SKILL.md]
Agent: SEMANTIC-SEARCH-ORCHESTRATOR
Instructions: "Spawn semantic-search-reader agent for search operations"
```

### Skill Spawns Agent
```
Tool: Task
Subagent: semantic-search-reader
Description: "Search codebase semantically"
Prompt: "You are the semantic-search-reader agent. Operation: search..."
```

**Logged as**:
```json
{"agent": "SEMANTIC-SEARCH-ORCHESTRATOR", "tool": "Task", "input": {...}}
```

### Agent Executes
```
Agent: SEMANTIC-READER (runs in subprocess)
Tool: Bash → runs ~/.claude/skills/semantic-search/scripts/search
Returns: Natural language summary (not raw JSON)
```

**Logged as**:
```json
{"agent": "SEMANTIC-READER", "tool": "Bash", "input": {"command": "scripts/search..."}}
```

### Skill Returns to User
```
Agent: SEMANTIC-SEARCH-ORCHESTRATOR
Action: Deliver agent's results to user
```

---

## Decision Table (Which Agent to Spawn)

| User Request Contains | Operation | Agent |
|----------------------|-----------|-------|
| "find X", "search for Y", "where is Z" | search | semantic-search-reader |
| "find similar to...", "similar chunks" | find-similar | semantic-search-reader |
| "what projects", "list indexed", "show projects" | list-projects | semantic-search-reader |
| "index this", "create index", "reindex" | index | semantic-search-indexer |
| "check index", "index status", "is it indexed" | status | semantic-search-indexer |

---

## Expected Session Logs (After Fix)

### Before Fix (WRONG)
```json
{"agent": "SEMANTIC-SEARCH", "tool": "Task", ...}
// No agent execution visible - I spawned it directly
```

### After Fix (CORRECT)
```json
{"agent": "SEMANTIC-SEARCH-ORCHESTRATOR", "tool": "Task", "input": {"subagent_type": "semantic-search-reader", ...}}
{"agent": "SEMANTIC-READER", "tool": "Bash", "input": {"command": "scripts/search --query ..."}}
```

---

## Testing Instructions

1. **Restart Claude Code** to reload the updated user-level skill
2. **Invoke semantic-search**: Ask "find the indexing status function"
3. **Verify skill spawns agent**: Look for Task tool call in conversation
4. **Check session logs**: `cat logs/session_*_tool_calls.jsonl | grep SEMANTIC`
5. **Expected output**:
   ```json
   {"agent": "SEMANTIC-SEARCH-ORCHESTRATOR", "tool": "Task", ...}
   {"agent": "SEMANTIC-READER", "tool": "Bash", ...}
   ```

---

## Key Learnings

1. **Claude Code loads user-level skills** (`~/.claude/skills/`) over project-level (`./.claude/skills/`)
2. **Skills must use correct `subagent_type`** - use actual agent names, not "general-purpose"
3. **Orchestrator naming convention**: All skills use `{SKILL-NAME}-ORCHESTRATOR` for consistency
4. **Agent architecture requires Task tool** in skill's `allowed-tools`
5. **Skills spawn agents**, not Claude directly - the skill orchestrator manages agent lifecycle

---

## Related Changes

- **session_logger.py**: Already updated with semantic-search detection (lines 85-86, 103-109, 164-177)
- **Agent definitions**: Already exist at project level (`.claude/agents/semantic-search-{reader,indexer}.md`)
- **No hook changes needed**: Existing hooks already track all Skill invocations generically

---

**Status**: ✅ Complete - Ready for testing after restart

**Next Steps**: User should restart Claude Code to reload the updated user-level skill, then test by invoking semantic-search
