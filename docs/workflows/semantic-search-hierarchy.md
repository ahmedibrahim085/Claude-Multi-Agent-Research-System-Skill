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

## Token Cost Examples (WHY This Saves Tokens)

### ❌ BAD: Traditional Grep Exploration (~8,000 tokens wasted)

**User**: "Find where authentication is handled"

**My Wrong Approach**:
```
1. Grep for "auth" → 200 matches → Read 5 files → Wrong code
2. Grep for "login" → 150 matches → Read 7 files → Still wrong
3. Grep for "authenticate" → 80 matches → Read 4 files → Getting closer
4. Grep for "session" → 300 matches → Read 10 files → Found it!

Total: 26 file reads, 4 Grep searches, 5-10 minutes
Token cost: ~8,000 tokens (file reads + failed attempts)
```

### ✅ GOOD: Semantic Search (~600 tokens saved)

**User**: "Find where authentication is handled"

**My Correct Approach**:
```
1. Invoke semantic-search skill
2. Query: "user authentication and credential verification"
3. Get ranked results with exact file:line locations
4. Read 1-2 most relevant files → Found it!

Total: 1 semantic search, 2 file reads, 30 seconds
Token cost: ~600 tokens (search overhead + targeted reads)
SAVINGS: 7,400 tokens (92% reduction)
```

---

## Direct Tool Use vs Semantic Search

### Use semantic-search Skill for (TOKEN SAVINGS):
- Finding content by describing WHAT it does (not exact keywords)
- Searching for "authentication logic" (could be named anything)
- Discovering patterns like "retry mechanisms" across project
- Finding similar implementations or documentation
- Understanding unfamiliar projects
- Cross-language/format searches (same concept, different syntax)
- **ANY exploratory task where you'd try multiple Grep searches**

### Use Grep ONLY for (Known Targets):
- Exact string matching (e.g., `"import React"`)
- Known variable/function names (e.g., `"getUserById"`)
- Regex patterns (e.g., `"function.*export"`)
- File content search with known keywords
- **When you KNOW exactly what string to match**

### Use Glob ONLY for (File Navigation):
- Finding files by name pattern (e.g., `"**/*.test.js"`)
- Locating configuration files (e.g., `"**/config.yml"`)
- File system navigation (e.g., `"src/components/**/*.tsx"`)

### Use Read ONLY for (Known Files):
- Reading specific known files
- Examining files after semantic-search narrows results

---

## Example Violations to AVOID

❌ **WRONG #1** (~8,000 tokens wasted): User asks "how does authentication work?"
- I run 20 Grep searches: `"login"`, `"auth"`, `"authenticate"`, `"verify"`
- I read 26 files trying to find the right code
- **VIOLATION**: Wasted 8,000 tokens on exploration instead of 600 tokens with semantic-search

❌ **WRONG #2** (Tool misuse): User asks "find the orchestrator pattern"
- I run: `~/.claude/skills/semantic-search/scripts/search --query "..."`
- **VIOLATION**: Ran bash scripts directly - skill should orchestrate this

❌ **WRONG #3** (Skipped hierarchy): I need to find error handling code
- I use Grep without trying semantic-search first
- **VIOLATION**: Didn't follow search hierarchy

✅ **CORRECT** (~600 tokens, saved 7,400): User asks "how does authentication work?"
- I activate semantic-search skill
- Skill executes: `scripts/search --query "user authentication logic" --k 10`
- Get ranked results with exact locations
- Read 2 most relevant files
- Deliver answer
- **Token savings: 92%**

✅ **ALSO CORRECT** (Proper fallback): I need to find authentication code
- I activate semantic-search skill first
- If index missing or search fails, THEN use Grep/Glob
- Always try semantic-search before manual exploration

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
- Index created using `scripts/index` command

**If index missing**:
- Use `scripts/index /path/to/project --full` to create index
- Or inform user to create index first
- Fallback to Grep/Glob for keyword-based search

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
