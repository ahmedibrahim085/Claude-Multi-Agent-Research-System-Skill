# Semantic Search Hierarchy Workflow
## Project Content Search with Token Savings

This workflow documents the absolute search hierarchy for finding content in the project using semantic search to save 5,000-10,000 tokens per task.

---

## WHY This Matters: Token Economics

**Problem**: Traditional exploration wastes 5,000-10,000 tokens per task:
- Grep for "auth", "login", "verify", "authenticate" → 15+ searches
- Read 20+ files to find the right implementation
- Multiple failed attempts before finding correct code

**Solution**: Semantic search finds functionality in 1 search by understanding MEANING:
- Query: "user authentication logic" → Direct hit in 1 search
- **Token Savings**: ~90% reduction in exploration overhead
- **Speed**: Instant vs 5-10 minutes of trial-and-error

---

## ABSOLUTE SEARCH HIERARCHY

**BEFORE using Grep/Glob to find functionality or content, ask yourself:**

1. **Am I searching for WHAT content describes** (not exact keywords)? → Use semantic-search
2. **Do I know the exact function/variable name**? → Use Grep
3. **Do I know the exact file path**? → Use Read
4. **Am I searching for file name patterns**? → Use Glob

---

## ALWAYS Use semantic-search Skill When:

**Trigger Keywords - When I Need To**:
- **Search/Find**: "search", "find", "locate", "look for", "discover", "where is", "show me", "find in codebase", "search codebase", "find in code"
- **Understanding**: "how does this work", "how is X implemented", "where is Y handled", "explain the content about"
- **Similarity**: "find similar", "similar to", "like this", "related to", "find other implementations"
- **Patterns**: "discover patterns", "identify instances", "all occurrences of"
- **Cross-Reference**: "where else", "find related", "show all references", "used by"
- **Documentation/Config**: "find documentation", "search documentation", "find config", "search config", "locate guide", "deployment documentation"

**Total**: ~52 keywords + 14 intent patterns (see `.claude/skills/skill-rules.json` for complete list)

---

## ABSOLUTE PROHIBITION

- ❌ NEVER use Grep/Glob as first attempt for functionality/content searches
- ❌ NEVER search the project without trying semantic-search first
- ❌ NEVER run bash scripts directly - activate skill and let it orchestrate

---

## MANDATORY Workflow

1. **STOP** - Do NOT use Grep/Glob/Read for functionality searches
2. **INVOKE**: Activate semantic-search skill FIRST
3. **SKILL SPAWNS AGENT**:
   - Reader agent for searches (90% of cases - search, find-similar, list-projects)
   - Indexer agent for indexing (10% of cases - index, status)
4. **AGENT EXECUTES**: Bash scripts run in agent's separate token budget
5. **AGENT RETURNS**: Interpreted results in natural language (not raw JSON)
6. **TOKEN SAVINGS**: Agent context separate from yours = 2-3x longer conversations
7. **ONLY IF SKILL FAILS**: Then fallback to Grep/Glob

---

## Why This Saves Tokens

Semantic search reduces exploration overhead by **90%+ (~5,000-10,000 tokens per task)** compared to traditional Grep-based searching.

**Quick Example:**
- **Traditional approach**: Finding authentication code requires 15+ Grep searches (`"auth"`, `"login"`, `"verify"`, etc.), reading 26 files across multiple attempts → ~8,000 tokens, 5-10 minutes
- **Semantic search**: Query `"user authentication logic"` → Get ranked results → Read 2 relevant files → ~600 tokens, 30 seconds
- **Savings**: 7,400 tokens (92% reduction)

**For comprehensive token economics, detailed cost comparisons, violation examples, and tool selection guidelines, see:**
→ [Token Savings Guide](../guides/token-savings-guide.md)

---

## Self-Check Before Acting

**Before searching/finding ANYTHING in this project, ask yourself**:
1. Did I try semantic-search skill? → NO? STOP and use skill first
2. Did the skill fail? → NO? Then don't do it yourself
3. Am I about to run Grep/Glob/bash? → YES? STOP and use skill first
4. Do I need to search/find/locate anything? → YES? Use semantic-search skill first

---

## Prerequisites

**Required**:
- Global installation: `~/.local/share/claude-context-local` (macOS/Linux) or `%LOCALAPPDATA%\claude-context-local` (Windows)
- Index created using `scripts/index` command (or auto-created by SessionStart hook)

**Auto-Reindex (v3.0.0)**:
- **Session-start trigger**: Reindexes on startup/resume (smart change detection, 60-min cooldown)
- **Post-modification trigger**: Reindexes after Write/Edit operations (5-min cooldown)
- **Incremental reindex**: ~5 seconds (42x faster than full reindex)
- **Decision tracing**: All skip reasons logged to session transcript for debugging
- Prerequisites checked before enforcement (`logs/state/semantic-search-prerequisites.json`)
- If prerequisites FALSE: Gracefully falls back to Grep/Glob (no errors, no blocking)
- Synchronous process: Reindex completes before returning control (2-5s typical, hook overhead <20ms)

**If index missing or prerequisites not ready**:
- **Check prerequisites**: Run `scripts/check-prerequisites` to validate 23 checks (MCP, model, scripts, etc.)
- **Manual index**: Use `scripts/index /path/to/project --full` to create index (~3 min first time)
- **Verify status**: Use `scripts/status --project /path/to/project` to check index statistics
- **Set prerequisites**: Use `scripts/set-prerequisites-ready` to manually enable enforcement
- **Graceful fallback**: System works with Grep/Glob until prerequisites ready (no blocking)

---

## Usage Examples

**Create/Update Index**:
```bash
~/.claude/skills/semantic-search/scripts/index /path/to/project --full
```

**List Indexed Projects**:
```bash
~/.claude/skills/semantic-search/scripts/list-projects
```

**Check Index Status**:
```bash
~/.claude/skills/semantic-search/scripts/status --project /path/to/project
```

**Basic Search**:
```bash
~/.claude/skills/semantic-search/scripts/search --query "user authentication logic" --k 10 --project /path/to/project
```

**Find Similar Content**:
```bash
# After getting chunk_id from search results
~/.claude/skills/semantic-search/scripts/find-similar --chunk-id "src/auth.py:45-67:function:authenticate" --k 5 --project /path/to/project
```

---

## Performance Guidelines

- **Default k=5**: Fast, usually sufficient
- **k=10-20**: Thorough search, moderate speed
- **k>50**: Slow, use only when comprehensive coverage needed
- **Index on SSD**: 5-10x faster than HDD

---

## When NOT to Use

**Do NOT use semantic search when**:
- You know the exact file name (use Read)
- You know the exact function/variable name (use Grep)
- You want file patterns (use Glob)
- Index doesn't exist and you need immediate results (use Grep/Glob)
- Searching for exact strings like import statements (use Grep)

---

**For detailed token savings examples and comparative analysis, see**: [Token Savings Guide](../guides/token-savings-guide.md)
