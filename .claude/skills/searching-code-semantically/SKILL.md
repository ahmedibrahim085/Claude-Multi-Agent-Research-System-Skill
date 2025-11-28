---
name: searching-code-semantically
description: >
  Semantic code search using natural language queries to find code by functionality rather than exact text matching.
  Wraps the claude-context-local MCP server's intelligent search capabilities in lightweight Python scripts.
  Use when searching for "how authentication works" or "error handling patterns" where Grep/Glob would require
  guessing exact variable names. Requires global installation of claude-context-local. Best for understanding
  unfamiliar codebases, finding similar implementations, or locating functionality across multiple files.
  NOT for simple keyword searches (use Grep) or finding files by name (use Glob). Works by querying a
  pre-built semantic index stored in .code-search-index/ directory.
---

# Semantic Code Search Skill

**Progressive Search from Keyword → Semantic → Similarity**

This skill enables semantic code search using natural language queries. Unlike traditional text-based search (Grep) or pattern matching (Glob), semantic search understands the **meaning** of code, finding functionally similar implementations even when they use different variable names, syntax, or patterns.

## 🎯 When to Use This Skill

### ✅ Use Semantic Search When:

**1. Exploring Unfamiliar Codebases**
- "How does this codebase handle user authentication?"
- "Where is database connection pooling implemented?"
- "Show me error handling patterns in this project"

**2. Finding Functionality Without Keywords**
- Looking for implementations but don't know the exact function names
- Need to find code that "does X" without knowing how it's named
- Searching across multiple languages/frameworks with different conventions

**3. Discovering Similar Code**
- "Find code similar to this payment processing logic"
- "Are there other implementations of rate limiting?"
- "What other modules use this pattern?"

**4. Cross-Reference Discovery**
- Finding all authentication methods in a polyglot codebase
- Locating retry logic across different services
- Identifying validation patterns in various modules

### ❌ Do NOT Use Semantic Search When:

**Use Grep instead** for:
- Exact string matching: `"import React"`
- Known variable/function names: `"getUserById"`
- Regex patterns: `"function.*export"`
- File content search with known keywords

**Use Glob instead** for:
- Finding files by name pattern: `"**/*.test.js"`
- Locating configuration files: `"**/config.yml"`
- File system navigation: `"src/components/**/*.tsx"`

**Use Read instead** for:
- Reading specific known files
- Examining file contents after Grep/Glob narrowed results
- Sequential file analysis

## 📋 Prerequisites

**Required: Global Installation**

This skill wraps the `claude-context-local` MCP server, which must be globally installed:

```bash
curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash
```

Installation location:
- **macOS/Linux**: `~/.local/share/claude-context-local`
- **Windows**: `%LOCALAPPDATA%\claude-context-local`

**Required: Pre-Built Index**

Before searching, the codebase must be indexed. This skill does NOT handle indexing (that's the MCP server's responsibility). Verify index exists:

```bash
# Check for index directory
ls -la .code-search-index/

# Expected: vector_store.db, file_mappings.json, metadata.json
```

If index doesn't exist, you must use the MCP server directly to create it (outside this skill).

## 🚀 Quick Start

### Operation 1: Search by Natural Language Query

**When to use**: Find code by describing what it does

```bash
# Basic search (returns top 5 results)
python scripts/search.py --query "user authentication logic"

# More results
python scripts/search.py --query "error handling patterns" --k 10

# Custom index location
python scripts/search.py --query "database queries" --storage-dir /path/to/index
```

**Output**: JSON with ranked results including file paths, line numbers, similarity scores, and code snippets.

### Operation 2: Find Similar Code Chunks

**When to use**: Discover code functionally similar to a reference chunk

```bash
# Find similar implementations
python scripts/find-similar.py --chunk-id "src/auth.py:45-67"

# More results
python scripts/find-similar.py --chunk-id "lib/utils.py:120-145" --k 10
```

**Output**: JSON with chunks ranked by semantic similarity to the reference.

### Operation 3: Check Index Status

**When to use**: Verify index exists and inspect statistics

```bash
# Default location (.code-search-index/)
python scripts/status.py

# Custom location
python scripts/status.py --storage-dir /path/to/index
```

**Output**: JSON with index statistics (chunk count, file count, last updated, model info).

## 📊 JSON Output Format

All scripts output standardized JSON:

**Success**:
```json
{
  "success": true,
  "data": {
    "results": [...],
    "query": "user authentication",
    "total_results": 5
  }
}
```

**Error**:
```json
{
  "success": false,
  "error": "Index not found",
  "suggestion": "Run indexing first or check storage-dir path",
  "path": ".code-search-index"
}
```

## 🔄 Typical Workflow

**Step 1: Verify Index Exists**
```bash
python scripts/status.py
```

**Step 2: Broad Semantic Search**
```bash
python scripts/search.py --query "authentication methods" --k 10
```

**Step 3: Find Similar Implementations**
```bash
# Using chunk_id from search results
python scripts/find-similar.py --chunk-id "src/auth/oauth.py:34-56"
```

**Step 4: Narrow with Traditional Tools**
```bash
# After identifying relevant files, use Read/Grep for details
```

## 📚 Reference Documentation

For detailed guidance, see the `references/` directory:

- **[effective-queries.md](references/effective-queries.md)**: Query patterns, good/bad examples, domain-specific tips
- **[troubleshooting.md](references/troubleshooting.md)**: Common errors, corner cases, compatibility notes
- **[performance-tuning.md](references/performance-tuning.md)**: Optimizing k values, large codebase strategies

## ⚙️ Arguments Reference

### search.py
- `--query` (required): Natural language search query
- `--k` (optional, default: 5): Number of results (5-50 recommended)
- `--storage-dir` (optional, default: `.code-search-index`): Index directory path

### find-similar.py
- `--chunk-id` (required): Reference chunk identifier from search results
- `--k` (optional, default: 5): Number of similar chunks to return
- `--storage-dir` (optional, default: `.code-search-index`): Index directory path

### status.py
- `--storage-dir` (optional, default: `.code-search-index`): Index directory path

## 🎓 Learning Path

**Beginners**: Start with `effective-queries.md` to learn query patterns
**Troubleshooting**: Consult `troubleshooting.md` for common issues
**Performance**: Read `performance-tuning.md` for large codebases (>10k files)

## 🔒 Design Rationale

**Why Separate Scripts Instead of Direct MCP Usage?**

1. **Token Efficiency**: MCP server loads ~10k tokens. Scripts use progressive disclosure (30-50 tokens when inactive).
2. **Composability**: Scripts output JSON, enabling shell pipelines and automation.
3. **Testability**: Scripts can be unit tested independently of MCP server state.
4. **Stability**: Script API remains stable even if MCP server internals change.

See `README.md` for full architectural decisions and API stability policy.

## 📝 Notes

- Scripts use `pathlib.Path` for cross-platform compatibility (Windows/macOS/Linux)
- All errors output JSON to stderr for programmatic error handling
- Scripts follow Unix philosophy: do one thing well, compose via pipes
- Chunk IDs are stable only within a single index build (reindexing may change IDs)

---

**Next Steps**: Read `references/effective-queries.md` to learn how to craft effective semantic search queries.
