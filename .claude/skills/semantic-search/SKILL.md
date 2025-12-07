---
name: semantic-search
description: Semantic search for finding code by meaning using natural language queries. Orchestrates semantic-search-reader (search/find-similar/list-projects) and semantic-search-indexer (index/reindex/status) agents. Use for understanding unfamiliar codebases, finding similar implementations, or locating functionality by description rather than exact keywords. (project)
allowed-tools: Bash, Read, Glob, Grep
---

# Semantic Search Skill

**Orchestrator for Semantic Code Intelligence via Agent Delegation**

This skill orchestrates two specialized agents for semantic search operations. It provides bash scripts that import Python modules from the claude-context-local library (**NOT an MCP server** - no server process runs, just Python imports via PYTHONPATH). Unlike traditional text-based search (Grep) or pattern matching (Glob), semantic search understands the **meaning** of content, finding functionally similar text even when using different wording, variable names, or patterns.

The skill uses the library's venv Python interpreter to import merkle, chunking, and embedding modules, enabling semantic search, indexing, and similarity finding across any text content (code, docs, markdown, configs).

## 🎬 Orchestration Instructions

**When this skill is active, you MUST spawn the appropriate agent via Task tool.**

This skill uses a **2-agent architecture** for token optimization:
- **semantic-search-reader**: Handles READ operations (search, find-similar, list-projects)
- **semantic-search-indexer**: Handles WRITE operations (index, incremental-reindex, status)

### Decision Logic: Which Agent to Spawn?

| User Request Contains | Operation Type | Agent to Spawn |
|----------------------|----------------|----------------|
| "find X", "search for Y", "where is Z" | **search** | semantic-search-reader |
| "find similar to...", "similar chunks" | **find-similar** | semantic-search-reader |
| "what projects", "list indexed", "show projects" | **list-projects** | semantic-search-reader |
| "index this", "create index", "full reindex" | **index** | semantic-search-indexer |
| "incremental reindex", "auto reindex", "update index" | **incremental-reindex** | semantic-search-indexer |
| "check index", "index status", "is it indexed" | **status** | semantic-search-indexer |

### Agent Spawn Examples

**Example 1: Search Operation** (semantic-search-reader)
```python
Task(
    subagent_type="semantic-search-reader",
    description="Search project semantically",
    prompt="""You are the semantic-search-reader agent.

Operation: search
Query: "user authentication logic"
K: 10
Project: /path/to/project

Execute the search operation using scripts/search and return interpreted results with explanations."""
)
```

**Example 2: Index Operation** (semantic-search-indexer)
```python
Task(
    subagent_type="semantic-search-indexer",
    description="Index project for semantic search",
    prompt="""You are the semantic-search-indexer agent.

Operation: index
Directory: /path/to/project
Full: true

Execute the indexing operation using scripts/incremental-reindex and return interpreted results with statistics."""
)
```

**Example 3: Incremental Reindex Operation** (semantic-search-indexer)
```python
Task(
    subagent_type="semantic-search-indexer",
    description="Incremental reindex with change detection",
    prompt="""You are the semantic-search-indexer agent.

Operation: incremental-reindex
Directory: /path/to/project
Max Age: 60  # minutes

Execute smart incremental reindexing using scripts/incremental-reindex.
This will detect changed files using Merkle tree and only re-embed what changed.
Return statistics showing files added/removed/modified and total chunks."""
)
```

**Example 4: Find Similar** (semantic-search-reader)
```python
Task(
    subagent_type="semantic-search-reader",
    description="Find similar content chunks",
    prompt="""You are the semantic-search-reader agent.

Operation: find-similar
Chunk ID: "src/auth.py:45-67:function:authenticate"
K: 5
Project: /path/to/project

Execute the find-similar operation using scripts/find-similar and return interpreted results."""
)
```

**Example 5: Status Check** (semantic-search-indexer)
```python
Task(
    subagent_type="semantic-search-indexer",
    description="Check semantic index status",
    prompt="""You are the semantic-search-indexer agent.

Operation: status
Project: /path/to/project

Execute the status operation using scripts/status and return interpreted results with statistics."""
)
```

### Important Notes

- **NEVER run bash scripts directly** - always spawn the appropriate agent
- **Agents handle error interpretation** - they convert JSON errors to natural language
- **Token optimization**: Agent execution happens in separate context (saves YOUR tokens)
- **Wait for agent completion** - agents return summarized results, not raw JSON

## 🎯 When to Use This Skill

### ✅ Use Semantic Search When:

**1. Exploring Unfamiliar Projects**
- "How does this codebase handle user authentication?"
- "Where is database connection pooling implemented?"
- "Show me error handling patterns in this project"
- "Find documentation about the architecture"

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

**5. Searching Documentation & Configuration**
- "Find documentation explaining the deployment process"
- "Locate configuration examples for database connections"
- "Search for troubleshooting guides or setup instructions"
- "Find ADRs (Architecture Decision Records) about API design"
- "Locate markdown files about testing strategies"

**6. Cross-Format Content Discovery**
- "Find all references to environment variables (across code, docs, configs)"
- "Search for rate limiting mentions in any format"
- "Locate authentication documentation and implementation together"
- "Find deployment guides and deployment scripts"

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

**Required: Python Library Dependency**

> **IMPORTANT:** This is **NOT an MCP server** - it's a Python library dependency. No server process runs. Our scripts import Python modules via PYTHONPATH.

This skill requires the claude-context-local Python library for semantic indexing:

```bash
# Clone Python library to standard location (5 minutes)
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local

# Set up Python virtual environment and install dependencies
cd ~/.local/share/claude-context-local
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

**What this installs:**
- Merkle tree change detection (80KB)
- Multi-language code chunking (192KB) - supports 15+ languages
- Embedding generation (76KB) - wraps sentence-transformers
- Dependencies: faiss-cpu, sentence-transformers, tree-sitter

**Installation location:**
- **macOS/Linux**: `~/.local/share/claude-context-local`
- **Windows**: `%LOCALAPPDATA%\claude-context-local`

**License:** claude-context-local is GPL-3.0. We import via PYTHONPATH (dynamic linking), which preserves our Apache 2.0 license. See `docs/architecture/MCP-DEPENDENCY-STRATEGY.md` for details.

**Index Creation**

This skill provides an `index` script that creates and updates the semantic content index. The index is stored in `~/.claude_code_search/projects/{project_name}_{hash}/` and contains:
- `code.index` - FAISS vector index
- `metadata.db` - SQLite database with chunk metadata
- `chunk_ids.pkl` - Chunk ID mappings
- `stats.json` - Index statistics

You can verify an index exists using the `status` script or the `list-projects` script.

## 🔄 Auto-Reindex System

**Automatic Index Management** (New in v2.3.x)

The semantic-search skill now automatically maintains index freshness via the SessionStart hook, eliminating the need for manual reindexing after code changes.

### How It Works

**Trigger-Based Logic**: The SessionStart hook analyzes the session type and index state to determine the optimal action:

| Session Type | Index State | Action | Duration |
|--------------|-------------|--------|----------|
| `startup` / `resume` | Never indexed | **Full index** (background) | ~3 min |
| `startup` / `resume` | Indexed before | **Smart reindex** (background) | ~5 sec (with Merkle tree) |
| `startup` / `resume` | Last full <60min | **Smart reindex** (cooldown active) | ~5 sec (with Merkle tree) |
| `clear` / `compact` | Any | **Skip** (no code changes) | N/A |

**Key Benefits**:
- ✅ **Automatic**: No manual reindexing required after code changes
- ✅ **Smart**: Uses Merkle tree to detect only changed files
- ✅ **Fast**: Incremental updates in ~5 seconds vs ~3 minutes full reindex
- ✅ **Non-blocking**: Background process, session starts immediately (<20ms overhead)
- ✅ **Efficient**: 60-minute cooldown prevents rapid full reindex spam

### 60-Minute Cooldown Protection

Prevents expensive full reindex spam during rapid restarts:

**Problem**: User workflow pattern:
```
10:00 - First startup → Full index (3 min)
10:05 - Close IDE, fix typo
10:07 - Reopen IDE → Would do full index again (waste 3 min)
10:10 - Close IDE, test change
10:12 - Reopen IDE → Would do full index again (waste 3 min)
```

**Solution**: Cooldown logic:
```
10:00 - First startup → Full index (~3 min)
10:05 - Close IDE, fix typo
10:07 - Reopen IDE → Smart reindex (fast, cooldown active)
10:10 - Close IDE, test change
10:12 - Reopen IDE → Smart reindex (fast, cooldown active)
11:05 - Restart after major refactor → Index exists, incremental anyway
```

**Result**: Saves 6 minutes in this example scenario.

**Note**: Cooldown prevents CHOOSING full index when index directory deleted, but cannot prevent full index when Merkle snapshot is also missing (Merkle stored at `~/.claude_code_search/projects/{project}_{hash}/index/merkle_snapshot.json`). If entire index directory deleted, Merkle deleted with it, and incremental-reindex script falls back to full regardless of cooldown.

### Concurrent Execution Protection

**PID-Based Lock Files**: Prevents duplicate indexing when multiple Claude Code windows opened simultaneously:

- **Lock file**: `~/.claude_code_search/projects/{project}_{hash}/indexing.lock`
- **Contains**: Process ID (PID) of running index operation
- **Validation**: Checks if process still alive before spawning new one
- **Stale lock cleanup**: Automatically removes locks from dead processes
- **Graceful handling**: Shows message if indexing already in progress

**Behavior**:
```
Window 1: Opens → Spawns background index → Creates lock
Window 2: Opens → Checks lock → PID alive → Skips, shows "already in progress"
Window 1: Index completes → Removes lock
Window 3: Opens → No lock → Proceeds normally
```

### State File Management

**Prerequisites State**: `logs/state/semantic-search-prerequisites.json`
- **Purpose**: Controls conditional enforcement in user-prompt-submit hook
- **Updated by**: `scripts/check-prerequisites`
- **Read by**: SessionStart hook (fast check, <5ms)
- **Content**:
  ```json
  {
    "SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY": true,
    "last_checked": "2025-12-03T12:00:00Z",
    "last_check_details": {
      "total_checks": 23,
      "passed": 23,
      "failed": 0,
      "warnings": 0
    }
  }
  ```

**Index State**: `~/.claude_code_search/projects/{project}_{hash}/index_state.json`
- **Purpose**: Tracks indexing timestamps for 60-minute cooldown logic
- **Updated by**: `scripts/incremental-reindex` (after full index), `scripts/incremental-reindex` (after any index)
- **Read by**: SessionStart hook (determine index type)
- **Content**:
  ```json
  {
    "last_full_index": "2025-12-03T10:00:00Z",
    "last_incremental_index": "2025-12-03T10:15:00Z",
    "project_path": "/Users/.../project"
  }
  ```

**Indexing Lock**: `~/.claude_code_search/projects/{project}_{hash}/indexing.lock`
- **Purpose**: Prevent concurrent indexing operations
- **Contains**: PID of running process
- **Lifecycle**: Created on spawn, updated by script with its PID, removed on completion
- **Validation**: Checks process alive via `os.kill(pid, 0)` (doesn't actually kill)

### Conditional Enforcement

**Prerequisites-Based**: The user-prompt-submit hook checks prerequisites before enforcing semantic-search skill:

- **If prerequisites TRUE**: Enforcement active, semantic-search skill suggested/required
- **If prerequisites FALSE**: Enforcement skipped, Claude uses Grep/Glob naturally (graceful degradation)
- **Default behavior**: TRUE if state file missing (backward compatible, lazy initialization works)

**Why This Matters**:
- First-time users: Can work immediately with Grep/Glob while setup completes
- Missing model: Graceful fallback, no errors
- Network issues: System remains functional

### Manual Control

You can still manually trigger indexing operations:

```bash
# Force full reindex (ignores cooldown, always does full)
scripts/incremental-reindex /path/to/project --full

# Smart incremental (respects age threshold, default 60min)
scripts/incremental-reindex /path/to/project

# Custom age threshold (reindex if >30min old)
scripts/incremental-reindex /path/to/project --max-age 30

# Check if reindex needed without executing
scripts/incremental-reindex /path/to/project --check-only
```

### Performance Characteristics

**Hook Overhead**: <20ms per session start
- Prerequisites check: <5ms (single file read)
- Index existence check: <5ms (single file check)
- Timestamp check: <1ms (JSON parse)
- Spawn background process: <5ms (detached, non-blocking)

**Background Indexing**:
- Full index: ~3 minutes (first time or major changes)
- Incremental: ~5 seconds (typical, with Merkle tree)
- Hook never blocks: Process detached, survives IDE close

**Cooldown Impact**:
- Prevents: ~3 minutes wasted per rapid restart
- Typical savings: 6-9 minutes per development session with frequent restarts

### Troubleshooting

**Auto-reindex not triggering?**
- Check prerequisites: `scripts/check-prerequisites`
- Verify state file: `cat logs/state/semantic-search-prerequisites.json`
- Set prerequisites manually: `scripts/set-prerequisites-ready`

**Index not updating after changes?**
- Check last index time: `scripts/status --project /path/to/project`
- Trigger manual reindex: `scripts/incremental-reindex /path/to/project`
- Force full reindex: `scripts/incremental-reindex /path/to/project --full`

**Concurrent indexing message?**
- Another window already indexing (wait for completion)
- Stale lock from crashed process (will auto-cleanup on next attempt)
- Check lock file: `cat ~/.claude_code_search/projects/{project}_{hash}/indexing.lock`

## 🚀 Quick Start

### Operation 1: Index a Project

**When to use**: Create or update the semantic index for a project

```bash
# Full index (recommended on first run or after major changes)
scripts/incremental-reindex /path/to/project --full

# Incremental index (faster, only processes changed files)
scripts/incremental-reindex /path/to/project

# Custom project name
scripts/incremental-reindex /path/to/project --project-name my-project --full
```

**Output**: JSON with indexing statistics (files added/modified/removed, chunks indexed, time taken).

### Operation 2: Incremental Reindex (RECOMMENDED)

**When to use**: Smart automatic reindexing with proper incremental support

**What it does**: Uses Merkle tree change detection to identify modified files, then re-embeds only changed content. Properly handles vector removal using IndexIDMap2 fix, preventing the "list index out of range" bug that occurs with standard incremental indexing.

```bash
# Auto-detect changes and reindex if >60min old (default)
scripts/incremental-reindex /path/to/project

# Custom age threshold (reindex if >30min old)
scripts/incremental-reindex /path/to/project --max-age 30

# Force full reindex regardless of age
scripts/incremental-reindex /path/to/project --full

# Check if reindex needed without executing
scripts/incremental-reindex /path/to/project --check-only
```

**Output**: JSON with detailed statistics:
```json
{
  "success": true,
  "incremental": true,
  "files_added": 3,
  "files_removed": 1,
  "files_modified": 5,
  "chunks_added": 127,
  "chunks_removed": 89,
  "total_chunks": 2045,
  "time_taken": 12.34
}
```

**Key Benefits**:
- ✅ **Fast**: Only re-processes changed files (not entire codebase)
- ✅ **Smart**: Merkle tree detects exactly what changed
- ✅ **Fixed**: Uses IndexIDMap2 to properly remove vectors
- ✅ **Safe**: No metadata/FAISS desynchronization
- ✅ **Automatic**: Can be triggered by hooks based on age threshold

### Operation 3: List Indexed Projects

**When to use**: See all projects that have been indexed

```bash
scripts/list-projects
```

**Output**: JSON with array of projects including paths, hashes, creation dates, and index statistics.

### Operation 4: Check Index Status

**When to use**: Verify index exists and inspect statistics for a project

```bash
scripts/status --project /path/to/project
```

**Output**: JSON with index statistics (chunk count, embedding dimension, files indexed, top folders, chunk types).

### Operation 5: Search by Natural Language Query

**When to use**: Find content by describing what it does or contains

```bash
# Basic search (returns top 5 results)
scripts/search --query "user authentication logic" --project /path/to/project

# More results
scripts/search --query "error handling patterns" --k 10 --project /path/to/project

# Search across all indexed projects (omit --project)
scripts/search --query "database queries" --k 5
```

**Output**: JSON with ranked results including file paths, line numbers, kind, similarity scores, chunk IDs, and snippets.

### Operation 6: Find Similar Content Chunks

**When to use**: Discover content semantically similar to a reference chunk

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

**Step 1: Index the Project (One-Time Setup)**
```bash
scripts/incremental-reindex /path/to/project --full
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
scripts/incremental-reindex /path/to/project

# Full reindex (after major refactoring)
scripts/incremental-reindex /path/to/project --full
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

**Why Bash Orchestrators for Python Library Imports?**

> **Clarification:** We use bash scripts to import Python modules, NOT an MCP server. No MCP protocol is used.

1. **Simplicity**: Bash scripts import existing Python modules directly - no reimplementation needed
2. **Reusability**: Imports merkle, chunking, embeddings modules with our IndexIDMap2 fix
3. **Auto-venv**: Scripts automatically use claude-context-local's venv Python interpreter
4. **Token Efficiency**: Scripts are compact (~50 lines each) vs bundling 352KB of Python code
5. **Composability**: Scripts output JSON, enabling shell pipelines and automation
6. **License-safe**: Dynamic linking via PYTHONPATH preserves Apache 2.0 license (GPL-compliant)

**Orchestrator Pattern**

Each bash script:
1. Sets `VENV_PYTHON` to `~/.local/share/claude-context-local/.venv/bin/python`
2. Sets `PYTHONPATH` for Python imports: `export PYTHONPATH="~/.local/share/claude-context-local"`
3. Imports Python modules: `from merkle import ...`, `from chunking import ...`, etc.
4. Runs our fixed indexing code (IndexIDMap2 wrapper)

**NOT Using MCP Protocol:**
- ❌ No MCP server process runs (`ps aux | grep claude-context-local` returns nothing)
- ❌ No MCP protocol communication (stdio/SSE/HTTP)
- ✅ Pure Python module imports via sys.path.insert() and PYTHONPATH
- ✅ This preserves Apache 2.0 license (dynamic linking is GPL-safe)

## 📝 Notes

- Scripts use the venv Python from claude-context-local library installation
- All errors are output from Python module imports (no MCP server involved)
- Chunk IDs are stable only within a single index build (reindexing may change IDs)
- Index location: `~/.claude_code_search/projects/{project_name}_{hash}/`
- Uses FAISS IndexIDMap2 (our fix) for proper add_with_ids/remove_ids support
- Embedding model: google/embeddinggemma-300m (768 dimensions)

## ⚠️ Known Issues

**Index Compatibility**: The `scripts/search` and `scripts/find-similar` operations use a different index format than `scripts/incremental-reindex`.

- If you use `scripts/incremental-reindex` to create/update your index, the search scripts may not find it
- This is because `incremental-reindex` uses a custom IndexIDMap2-based storage format
- Current limitation: Use `scripts/incremental-reindex` for creating indices that `scripts/search` can use
- Future enhancement: Update search scripts to support both index formats

**Workaround**: Use `scripts/incremental-reindex /path/to/project --full` for creating searchable indices, or implement IndexIDMap2 support in search scripts.

---

**Next Steps**:
- For creating searchable indices: `scripts/incremental-reindex /path/to/project --full`
- For local incremental updates (testing): `scripts/incremental-reindex /path/to/project`
- Then explore with semantic search queries using `scripts/search`
