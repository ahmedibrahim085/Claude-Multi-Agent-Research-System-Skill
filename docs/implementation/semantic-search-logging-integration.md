# Semantic-Search Logging Integration

**Date**: 2025-12-01
**File Modified**: `.claude/utils/session_logger.py`
**Purpose**: Integrate semantic-search skill and agents into existing logging/tracking infrastructure

---

## Implementation Summary

Semantic-search skill and its 2 agents (semantic-search-reader, semantic-search-indexer) are now fully integrated into the logging and tracking system used by multi-agent-researcher and spec-workflow-orchestrator skills.

## Changes Made

### Change 1: Orchestrator Detection
**Location**: Lines 85-86 in `identify_agent()` function
**Purpose**: Detect when semantic-search skill is active

```python
elif skill_name == 'semantic-search':
    return 'semantic-search-orchestrator'
```

**Impact**: When semantic-search skill is active, tool calls will be attributed to 'semantic-search-orchestrator' instead of generic 'orchestrator'.

---

### Change 2: Agent Detection from Task Tool
**Location**: Lines 103-109 in `identify_agent()` function
**Priority**: 4 (before generic Task tool detection)
**Purpose**: Detect specific semantic-search agents by analyzing Task tool prompts

```python
# Priority 4: Detect semantic-search agents from Task tool prompt
if tool_name == 'Task' and tool_input.get('prompt'):
    prompt = tool_input['prompt']
    if 'You are the semantic-search-reader agent' in prompt:
        return 'semantic-search-reader'
    if 'You are the semantic-search-indexer agent' in prompt:
        return 'semantic-search-indexer'
```

**Impact**: When semantic-search skill spawns agents via Task tool, they will be correctly identified as 'semantic-search-reader' or 'semantic-search-indexer'.

**Critical Design Note**: This check is placed at Priority 4, BEFORE the generic Task tool detection at Priority 5. This ensures specific agent detection takes precedence over generic orchestrator detection.

---

### Change 3: Agent ID Mappings
**Location**: Lines 164-177 in `get_agent_id()` function
**Purpose**: Map agent types to readable IDs for session logs

```python
if agent_type == 'research-orchestrator':
    return 'RESEARCH-ORCHESTRATOR'

if agent_type == 'spec-orchestrator':
    return 'SPEC-ORCHESTRATOR'

if agent_type == 'semantic-search-orchestrator':
    return 'SEMANTIC-SEARCH'

if agent_type == 'semantic-search-reader':
    return 'SEMANTIC-READER'

if agent_type == 'semantic-search-indexer':
    return 'SEMANTIC-INDEXER'
```

**Impact**: Session logs will display clear agent identifiers:
- `SEMANTIC-SEARCH` for skill orchestrator
- `SEMANTIC-READER` for search operations agent
- `SEMANTIC-INDEXER` for indexing operations agent

**Bonus**: Also added explicit mappings for `research-orchestrator` and `spec-orchestrator` for consistency (previously relied on fallback `agent_type.upper()`).

---

### Bonus: Priority Numbering Fix
**Location**: Line 115
**Purpose**: Fix duplicate "Priority 5" comment

```python
# Priority 6: Check if we're in an active research session
```

**Reason**: After adding Priority 4 (semantic-search agent detection), the research session check was still labeled "Priority 5" when it's actually Priority 6.

---

## Detection Priority Order

The `identify_agent()` function now uses this priority order:

1. **Priority 1**: Active skill orchestrator (research, spec, semantic-search)
2. **Priority 2**: Environment variable `CLAUDE_AGENT_TYPE`
3. **Priority 3**: File path detection (researcher writes to research_notes/, report-writer writes to reports/)
4. **Priority 4**: Semantic-search agents from Task tool prompt (NEW)
5. **Priority 5**: Generic Task tool detection (orchestrator spawning subagents)
6. **Priority 6**: Active research session phase detection
7. **Default**: Assume 'orchestrator'

---

## What Semantic-Search Doesn't Need

Unlike research and spec skills, semantic-search is a **stateless utility skill**, so it does NOT need:

- ❌ **Multi-phase workflow tracking** - Each operation is atomic (search, index, status)
- ❌ **Session resumption logic** - Operations complete in one agent invocation
- ❌ **Quality gates** - No enforcement like "synthesis must be by report-writer"
- ❌ **workflow_state.sh** - No project modes (fresh vs refinement)
- ❌ **Separate state file** - No equivalent to research-workflow-state.json or spec-workflow-state.json

---

## What Already Worked (No Changes Needed)

These infrastructure components work for ALL skills (research, spec, semantic-search) without modification:

✅ **Skill Invocation Tracking** - post-tool-use hook tracks all Skill tool calls
✅ **Session Logging** - All tool calls logged to `logs/session_*_{transcript.txt,tool_calls.jsonl}`
✅ **Crash Recovery** - session-start hook detects orphaned skills from crashes
✅ **Skill Start Messages** - Generic "🎯 SKILL START: {skill_name}" works for all skills

---

## Testing Verification

### Expected Behavior After Changes

When semantic-search skill is invoked and spawns agents, session logs should show:

**Before Agent Spawn**:
```
[HH:MM:SS] SEMANTIC-SEARCH → Skill
  Input: {"skill": "semantic-search"}
  Output: Success
```

**Agent Execution**:
```
[HH:MM:SS] SEMANTIC-SEARCH → Task
  Input: {
    "subagent_type": "general-purpose",
    "description": "Search codebase semantically",
    "prompt": "You are the semantic-search-reader agent..."
  }
  Output: Success
```

**Agent Tool Calls** (detected from prompt):
```
[HH:MM:SS] SEMANTIC-READER → Bash
  Input: {"command": "~/.claude/skills/semantic-search/scripts/search --query..."}
  Output: Success (1.2 KB)
```

### Verification in Session Logs

Check `logs/session_*_tool_calls.jsonl`:
```json
{"ts": "2025-12-01T...", "agent": "SEMANTIC-SEARCH", "tool": "Skill", ...}
{"ts": "2025-12-01T...", "agent": "SEMANTIC-SEARCH", "tool": "Task", ...}
{"ts": "2025-12-01T...", "agent": "SEMANTIC-READER", "tool": "Bash", ...}
```

---

## Architecture Benefits

### Token Separation
- Orchestrator runs in main conversation context
- Agents run in separate subprocess contexts
- Agent execution doesn't consume orchestrator's token budget
- Enables 2.6x longer conversations (per token analysis)

### Visibility & Debugging
- Clear attribution of tool calls to specific agents
- Session logs show which agent performed which operation
- Crash recovery works for semantic-search skill
- Easy to trace execution flow across orchestrator → agents

### Consistency with Existing Infrastructure
- Follows same patterns as research and spec skills
- Uses existing hooks (no new hooks needed)
- Reuses session_logger and state_manager utilities
- No duplicate infrastructure

---

## Related Documentation

- **Session Logging**: `.claude/utils/session_logger.py` (THIS FILE - now modified)
- **State Management**: `.claude/utils/state_manager.py`
- **Post-Tool-Use Hook**: `.claude/hooks/post-tool-use-track-research.py`
- **Session Start Hook**: `.claude/hooks/session-start.py`
- **Semantic-Search Skill**: `.claude/skills/semantic-search/SKILL.md`
- **Agent Definitions**: `.claude/agents/{semantic-search-reader,semantic-search-indexer}.md`

---

## Commit Message (Suggested)

```
FEAT: Integrate semantic-search skill into logging infrastructure

Add semantic-search skill and agent tracking to session_logger.py:

1. Orchestrator detection: semantic-search → semantic-search-orchestrator
2. Agent detection: Task prompts → semantic-search-reader/indexer
3. Agent ID mappings: SEMANTIC-SEARCH, SEMANTIC-READER, SEMANTIC-INDEXER
4. Priority numbering fix: Research session check is Priority 6

Impact:
- Session logs now correctly attribute tool calls to semantic-search agents
- Debugging improved with clear agent identification
- Consistent with research/spec skill infrastructure
- No new hooks needed (reuses existing infrastructure)

Files changed: .claude/utils/session_logger.py (+21 lines)
```

---

**Status**: ✅ Complete - Ready for testing
