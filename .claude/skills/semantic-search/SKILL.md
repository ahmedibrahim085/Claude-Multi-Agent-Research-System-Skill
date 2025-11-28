---
name: semantic-search
description: >
  Semantic search using natural language queries to find content by meaning rather than exact text matching.
  Orchestrates the claude-context-local MCP server's CodeSearchServer class via bash scripts that call Python methods directly.
  Use when searching for "how authentication works" or "error handling patterns" where Grep/Glob would require
  guessing exact keywords. Works on any text (code, documentation, markdown, comments, configs). Best for understanding
  unfamiliar codebases, finding similar implementations, or locating functionality across multiple files.
  NOT for simple keyword searches (use Grep) or finding files by name (use Glob). Provides indexing, searching,
  status checking, and similarity finding capabilities.
---

# Semantic Search Skill

**Bash Orchestrators for Semantic Intelligence**

This skill provides bash scripts that orchestrate the claude-context-local MCP server's CodeSearchServer class. Each script calls Python methods directly using the venv Python interpreter, enabling semantic search, indexing, and similarity finding across any text content (code, docs, markdown, configs). Unlike traditional text-based search (Grep) or pattern matching (Glob), semantic search understands the **meaning** of content, finding functionally similar text even when using different wording, variable names, or patterns.

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

**Index Creation**

This skill provides an `index` script that creates and updates the semantic code index. The index is stored in `~/.claude_code_search/projects/{project_name}_{hash}/` and contains:
- `code.index` - FAISS vector index
- `metadata.db` - SQLite database with chunk metadata
- `chunk_ids.pkl` - Chunk ID mappings
- `stats.json` - Index statistics

You can verify an index exists using the `status` script or the `list-projects` script.

## 🚀 Quick Start

### Operation 1: Index a Codebase

**When to use**: Create or update the semantic index for a project

```bash
# Full index (recommended on first run or after major changes)
scripts/index /path/to/project --full

# Incremental index (faster, only processes changed files)
scripts/index /path/to/project

# Custom project name
scripts/index /path/to/project --project-name my-project --full
```

**Output**: JSON with indexing statistics (files added/modified/removed, chunks indexed, time taken).

### Operation 2: List Indexed Projects

**When to use**: See all projects that have been indexed

```bash
scripts/list-projects
```

**Output**: JSON with array of projects including paths, hashes, creation dates, and index statistics.

### Operation 3: Check Index Status

**When to use**: Verify index exists and inspect statistics for a project

```bash
scripts/status --project /path/to/project
```

**Output**: JSON with index statistics (chunk count, embedding dimension, files indexed, top folders, chunk types).

### Operation 4: Search by Natural Language Query

**When to use**: Find code by describing what it does

```bash
# Basic search (returns top 5 results)
scripts/search --query "user authentication logic" --project /path/to/project

# More results
scripts/search --query "error handling patterns" --k 10 --project /path/to/project

# Search across all indexed projects (omit --project)
scripts/search --query "database queries" --k 5
```

**Output**: JSON with ranked results including file paths, line numbers, kind, similarity scores, chunk IDs, and snippets.

### Operation 5: Find Similar Code Chunks

**When to use**: Discover code functionally similar to a reference chunk

```bash
# Find similar implementations (use chunk_id from search results)
scripts/find-similar --chunk-id "src/auth.py:45-67:function:authenticate" --project /path/to/project

# More results
scripts/find-similar --chunk-id "lib/utils.py:120-145:method:retry" --k 10 --project /path/to/project
```

**Output**: JSON with reference chunk and array of similar chunks ranked by semantic similarity.

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

**Step 1: Index the Codebase (One-Time Setup)**
```bash
scripts/index /path/to/project --full
```

**Step 2: Verify Index Status**
```bash
scripts/status --project /path/to/project
# or
scripts/list-projects
```

**Step 3: Broad Semantic Search**
```bash
scripts/search --query "authentication methods" --k 10 --project /path/to/project
```

**Step 4: Find Similar Implementations**
```bash
# Using chunk_id from search results
scripts/find-similar --chunk-id "src/auth/oauth.py:34-56:function:oauth_login" --project /path/to/project
```

**Step 5: Reindex After Changes**
```bash
# Incremental reindex (fast, only changed files)
scripts/index /path/to/project

# Full reindex (after major refactoring)
scripts/index /path/to/project --full
```

**Step 6: Narrow with Traditional Tools**
```bash
# After identifying relevant files, use Read/Grep for details
```

## 📚 Reference Documentation

For detailed guidance, see the `references/` directory:

- **[effective-queries.md](references/effective-queries.md)**: Query patterns, good/bad examples, domain-specific tips
- **[troubleshooting.md](references/troubleshooting.md)**: Common errors, corner cases, compatibility notes
- **[performance-tuning.md](references/performance-tuning.md)**: Optimizing k values, large codebase strategies

## ⚙️ Arguments Reference

### index
- `DIRECTORY` (required): Directory to index (positional argument)
- `--project-name NAME` (optional): Custom project name (default: directory basename)
- `--full` (optional): Do full reindex (default: incremental)
- `-h, --help`: Show usage information

### list-projects
- No arguments required
- Lists all indexed projects with statistics

### status
- `--project PATH` (optional): Project path to check status for (default: current project or error)

### search
- `--query "QUERY"` (required): Natural language search query
- `--k NUM` (optional, default: 5): Number of results (5-50 recommended)
- `--project PATH` (optional): Project path to search in (default: all projects)

### find-similar
- `--chunk-id "CHUNK_ID"` (required): Reference chunk identifier from search results
- `--k NUM` (optional, default: 5): Number of similar chunks to return
- `--project PATH` (optional): Project path to search in (default: current project)

## 🎓 Learning Path

**Beginners**: Start with `effective-queries.md` to learn query patterns
**Troubleshooting**: Consult `troubleshooting.md` for common issues
**Performance**: Read `performance-tuning.md` for large codebases (>10k files)

## 🔒 Design Rationale

**Why Bash Orchestrators Instead of Direct MCP Usage?**

1. **Simplicity**: Bash scripts call existing Python code directly - no reimplementation needed
2. **Reusability**: Uses the same CodeSearchServer class that the MCP server uses
3. **Auto-venv**: Scripts automatically use the correct venv Python interpreter
4. **Token Efficiency**: Scripts are compact (~50 lines each) vs full MCP server integration
5. **Composability**: Scripts output JSON, enabling shell pipelines and automation
6. **Maintainability**: Changes to MCP server's CodeSearchServer are automatically available

**Orchestrator Pattern**

Each bash script:
1. Sets `VENV_PYTHON` to `~/.local/share/claude-context-local/.venv/bin/python`
2. Sets `PYTHONPATH` for proper imports
3. Changes to claude-context-local directory
4. Calls CodeSearchServer methods via inline Python

This pattern avoids code duplication while maintaining the benefits of thin wrapper scripts.

## 📝 Notes

- Scripts use the venv Python from claude-context-local installation
- All errors are output from the MCP server's error handling
- Chunk IDs are stable only within a single index build (reindexing may change IDs)
- Index location: `~/.claude_code_search/projects/{project_name}_{hash}/`
- Uses FAISS IndexFlatIP for semantic similarity search
- Embedding model: google/embeddinggemma-300m (768 dimensions)

## ⚠️ Known Issues

**Auto-Reindexing Bug**: The MCP server has a bug in incremental auto-reindexing (triggered when index is >5 minutes old). This can cause "list index out of range" errors during search. Workaround: Run `scripts/index --full` before searching after long intervals.

---

**Next Steps**: Start by indexing your codebase with `scripts/index /path/to/project --full`, then explore with semantic search queries.
