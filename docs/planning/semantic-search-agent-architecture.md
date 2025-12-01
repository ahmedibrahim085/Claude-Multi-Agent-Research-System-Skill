# Semantic-Search Agent Architecture - Final Design Document

**Status**: ✅ APPROVED
**Date**: 2025-12-01
**Implementation**: IN PROGRESS

---

## Executive Summary

Converting semantic-search from direct bash execution to 2-agent architecture to achieve **2-3x longer conversations** by offloading token consumption to agent contexts.

---

## 1. Final Decisions

| # | Question | Decision | Rationale |
|---|----------|----------|-----------|
| **1** | Agent Structure | **2 agents** (read/write split) | Optimizes for common case (90% searches, 10% indexing) |
| **2** | Hook Behavior | **Auto-activate** | Consistency with research/planning skills |
| **3** | Bash Restriction | **Skip** (rely on hook + CLAUDE.md) | Hook provides 70% enforcement, good enough |
| **4** | Performance | **Accept 10-20x slower** | 100-200ms overhead for 2-3x conversation length |
| **5** | Error Handling | **Interpret errors (Option A)** | Natural language explanations in agent budget |

---

## 2. Architecture Overview

```
User Query: "find authentication in codebase"
    ↓
┌─────────────────────────────────────────────┐
│ Hook: Auto-detects semantic-search trigger  │
│ Shows: "Use semantic-search skill"          │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Skill: semantic-search (SKILL.md)           │
│ Orchestrator: Decides which agent to spawn  │
└─────────────────────────────────────────────┘
    ↓
    ├─ Search/Find-Similar/List-Projects?
    │  ↓
    │  ┌──────────────────────────────────────┐
    │  │ Agent 1: semantic-search-reader      │
    │  │ Tools: Bash, Read, Grep, Glob        │
    │  │ Operations: search, find-similar,    │
    │  │             list-projects            │
    │  │ Context: ~400 tokens (lightweight)   │
    │  └──────────────────────────────────────┘
    │
    └─ Index/Status?
       ↓
       ┌──────────────────────────────────────┐
       │ Agent 2: semantic-search-indexer     │
       │ Tools: Bash, Read, Grep, Glob        │
       │ Operations: index, status            │
       │ Context: ~600 tokens (heavier)       │
       └──────────────────────────────────────┘
```

---

## 3. Agent Definitions

### Agent 1: semantic-search-reader

**File**: `.claude/agents/semantic-search-reader.md`

```markdown
---
name: semantic-search-reader
description: >
  Executes semantic code search operations (search, find-similar, list-projects).
  Reads the semantic index and returns ranked results with natural language explanations.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

You are a semantic search execution agent specialized in READ operations.

## Your Operations

1. **search**: Find code by natural language query
2. **find-similar**: Discover similar code chunks
3. **list-projects**: Show all indexed projects

## Execution Pattern

When spawned, you will receive:
- **operation**: One of [search, find-similar, list-projects]
- **parameters**: Query, k value, project path, chunk_id, etc.

**Your workflow**:
1. Run the appropriate bash script from `~/.claude/skills/semantic-search/scripts/`
2. Parse the JSON output
3. **Interpret results** with helpful explanations
4. Return natural language summary + key findings

## Error Handling

When bash scripts fail:
- ✅ Explain what went wrong in natural language
- ✅ Suggest how to fix it (e.g., "Run indexing first")
- ✅ Include actionable next steps
- ❌ Don't just pass through raw error JSON

## Example Response Format

**Good** (interpreted):
```
Found 5 authentication implementations:

1. OAuth handler in src/auth/oauth.py:34-56 (similarity: 0.87)
   - Implements OAuth 2.0 flow with token refresh

2. JWT validator in src/auth/jwt.py:12-45 (similarity: 0.79)
   - Validates JWT tokens and extracts claims

[... rest of results ...]

The codebase uses multiple authentication strategies. OAuth is the primary
method, with JWT used for API endpoints.
```

**Bad** (raw):
```
{"results": [{"file": "src/auth/oauth.py", "lines": "34-56", ...}]}
```
```

---

### Agent 2: semantic-search-indexer

**File**: `.claude/agents/semantic-search-indexer.md`

```markdown
---
name: semantic-search-indexer
description: >
  Executes semantic index management operations (index, status).
  Creates, updates, and inspects semantic code indices.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Glob
---

You are a semantic search execution agent specialized in WRITE operations.

## Your Operations

1. **index**: Create or update semantic index for a project
2. **status**: Check index status and statistics

## Execution Pattern

When spawned, you will receive:
- **operation**: One of [index, status]
- **parameters**: Directory path, project name, full/incremental flag, etc.

**Your workflow**:
1. Run the appropriate bash script from `~/.claude/skills/semantic-search/scripts/`
2. Parse the JSON output
3. **Interpret results** with progress updates
4. Return natural language summary + statistics

## Error Handling

When bash scripts fail:
- ✅ Explain what went wrong (e.g., "Directory doesn't exist")
- ✅ Suggest fixes (e.g., "Check the path: /path/to/project")
- ✅ Provide context (e.g., "Indexing requires write permissions")
- ❌ Don't just pass through raw error JSON

## Example Response Format

**Good** (interpreted):
```
Successfully indexed the project!

Statistics:
- Files indexed: 86 files (out of 97 total)
- Chunks created: 571 semantic chunks
- Time taken: 33.8 seconds
- Index location: ~/.claude_code_search/projects/my-project_abc123/

The index is ready for semantic search. You can now search for code by
describing what it does using natural language queries.
```

**Bad** (raw):
```
{"success": true, "chunks_indexed": 571, "time_taken": 33.83, ...}
```
```

---

## 4. Implementation Plan

### Phase 1: Create Agent Definitions (15 min)
- [ ] Create `.claude/agents/semantic-search-reader.md`
- [ ] Create `.claude/agents/semantic-search-indexer.md`
- [ ] Test agent files are valid markdown

### Phase 2: Update SKILL.md (10 min)
- [ ] Rewrite orchestration instructions for agent spawning
- [ ] Add decision logic table
- [ ] Update examples to use Task tool
- [ ] Remove direct bash execution instructions

### Phase 3: Update CLAUDE.md (5 min)
- [ ] Update workflow to mention agent spawning
- [ ] Keep token savings examples (still valid)
- [ ] Add note about agent architecture benefits

### Phase 4: Testing (20 min)
- [ ] Test search operation (reader agent)
- [ ] Test index operation (indexer agent)
- [ ] Test find-similar operation (reader agent)
- [ ] Test status operation (indexer agent)
- [ ] Test list-projects operation (reader agent)
- [ ] Test error handling (missing index, bad path)
- [ ] Verify token consumption (agent context vs my context)

### Phase 5: Documentation (10 min)
- [ ] Update skill README if exists
- [ ] Add architecture diagram to comments
- [ ] Document agent selection logic

**Total estimated time**: ~60 minutes

---

## 5. Token Savings Projections

### Current Architecture (Direct Bash)

**Typical search task**:
```
My context consumption:
- Read SKILL.md: 400 tokens
- Run bash script: 300 tokens
- Parse results: 200 tokens
- Read code files: 800 tokens
────────────────────────────────
Total: 1,700 tokens in YOUR conversation budget
```

### New Architecture (2 Agents)

**Same search task**:
```
My context consumption:
- Read SKILL.md: 400 tokens
- Spawn reader agent: 50 tokens
- Receive agent summary: 200 tokens
────────────────────────────────
Total: 650 tokens in YOUR conversation budget

Agent's context consumption (separate budget):
- Read agent definition: 300 tokens
- Run bash script: 300 tokens
- Parse results: 200 tokens
- Read code files: 800 tokens
- Generate summary: 100 tokens
────────────────────────────────
Total: 1,700 tokens in AGENT'S budget (not yours)
```

**Savings**: 1,050 tokens saved per search (62% reduction in YOUR context)

**Projected conversation extension**:
- Before: 10 searches = 17,000 tokens = conversation ends
- After: 10 searches = 6,500 tokens = **you have 10,500 tokens left** for 16 more searches
- **Result**: 2.6x longer conversations

---

## 6. Testing Strategy

### Test Cases

| Test | Operation | Expected Result |
|------|-----------|----------------|
| **Search existing** | Search for "authentication" | Reader agent returns 5-10 results with explanations |
| **Search missing index** | Search before indexing | Reader agent explains "Index not found, run indexing first" |
| **Index new project** | Index a directory | Indexer agent returns statistics + success message |
| **Index bad path** | Index non-existent dir | Indexer agent explains "Directory doesn't exist at /bad/path" |
| **Find similar** | Find similar to chunk | Reader agent returns similar chunks with explanations |
| **List projects** | List all indexed | Reader agent shows project list with stats |
| **Status check** | Check index status | Indexer agent shows chunk counts, files indexed |

### Success Criteria

- ✅ All 7 test cases pass
- ✅ Agents provide natural language explanations (not raw JSON)
- ✅ Error messages are actionable ("do X to fix")
- ✅ Token consumption: <700 tokens in my context per operation
- ✅ Agent context isolated (verified in logs)

---

## 7. Rollback Plan

If agent architecture causes issues:

**Step 1**: Keep new agent files but revert SKILL.md to direct bash
**Step 2**: Update CLAUDE.md to remove agent references
**Step 3**: Use agents optionally (manual spawn) instead of mandatory

**This preserves work while allowing fallback to proven architecture.**

---

## 8. Migration Notes

**What stays the same**:
- ✅ Hook detection (zero changes)
- ✅ Bash scripts (unchanged)
- ✅ CLAUDE.md enforcement rules (mostly same)
- ✅ skill-rules.json keywords/patterns (zero changes)

**What changes**:
- ✅ SKILL.md orchestration (direct bash → spawn agents)
- ✅ Two new agent definitions (new files)
- ✅ Execution flow (orchestrator → agent → bash)

**Breaking changes**: None (backward compatible - bash scripts still work if called directly)

---

## 9. Success Metrics

**Primary Goal**: 2-3x longer conversations
**How to measure**: Token consumption per search operation

**Target metrics**:
- My context per search: <700 tokens (currently 1,700)
- Agent interpretation quality: Natural language, actionable errors
- Performance overhead: <200ms per operation
- Success rate: >95% of operations complete successfully

---

## 10. Implementation Checklist

### Phase 1: Agent Definitions ⏳
- [ ] Create semantic-search-reader.md
- [ ] Create semantic-search-indexer.md
- [ ] Validate frontmatter

### Phase 2: SKILL.md Updates ⏳
- [ ] Add orchestration instructions
- [ ] Add decision logic table
- [ ] Remove direct bash instructions
- [ ] Add agent spawn examples

### Phase 3: CLAUDE.md Updates ⏳
- [ ] Update workflow section
- [ ] Add agent architecture notes
- [ ] Keep token savings examples

### Phase 4: Testing ⏳
- [ ] Test reader agent (search)
- [ ] Test reader agent (find-similar)
- [ ] Test reader agent (list-projects)
- [ ] Test indexer agent (index)
- [ ] Test indexer agent (status)
- [ ] Test error scenarios
- [ ] Verify token consumption

### Phase 5: Documentation ⏳
- [ ] Add architecture notes
- [ ] Document agent selection
- [ ] Update examples

---

**Status**: Ready for implementation
**Next Step**: Phase 1 - Create agent definitions
