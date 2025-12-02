# Token Savings Guide
## Why Semantic Search Saves 5,000-10,000 Tokens Per Task

This guide explains the token economics of semantic search vs traditional Grep exploration, with real-world examples showing 90%+ token savings.

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

**❌ WRONG #1** (~8,000 tokens wasted): User asks "how does authentication work?"
- I run 20 Grep searches: `"login"`, `"auth"`, `"authenticate"`, `"verify"`
- I read 26 files trying to find the right code
- **VIOLATION**: Wasted 8,000 tokens on exploration instead of 600 tokens with semantic-search

**❌ WRONG #2** (Tool misuse): User asks "find the orchestrator pattern"
- I run: `~/.claude/skills/semantic-search/scripts/search --query "..."`
- **VIOLATION**: Ran bash scripts directly - skill should orchestrate this

**❌ WRONG #3** (Skipped hierarchy): I need to find error handling code
- I use Grep without trying semantic-search first
- **VIOLATION**: Didn't follow search hierarchy

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

## Summary: Token Savings Breakdown

| Scenario | Traditional Grep | Semantic Search | Savings |
|----------|-----------------|-----------------|---------|
| Find authentication | ~8,000 tokens | ~600 tokens | **7,400 tokens (92%)** |
| Find retry mechanisms | ~10,000 tokens | ~700 tokens | **9,300 tokens (93%)** |
| Explore unfamiliar code | ~12,000 tokens | ~800 tokens | **11,200 tokens (93%)** |
| Find error handling | ~6,000 tokens | ~500 tokens | **5,500 tokens (92%)** |

**Average savings per exploratory task**: **5,000-10,000 tokens (90%+)**
