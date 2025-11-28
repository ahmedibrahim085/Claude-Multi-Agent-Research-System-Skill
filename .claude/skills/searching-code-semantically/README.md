# Searching Code Semantically - Claude Code Skill

**Semantic code search using natural language queries powered by the claude-context-local MCP server.**

## Overview

This skill wraps the `claude-context-local` MCP server's intelligent search capabilities in lightweight, composable Python scripts. Instead of loading the MCP server (which costs ~10k tokens), these scripts provide progressive disclosure (30-50 tokens when inactive) while enabling semantic code search.

### What is Semantic Search?

Traditional search (Grep, Glob) matches exact text or patterns:
```bash
grep "authenticateUser"  # Finds only "authenticateUser"
```

Semantic search understands **meaning**:
```bash
python scripts/search.py --query "user authentication logic"
# Finds: loginUser(), verifyCredentials(), checkAuth(), etc.
# Even if they use different names or patterns
```

## Quick Start

### 1. Installation

**Prerequisite**: Global installation of `claude-context-local` MCP server

```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash

# Windows: Download installer from repository
```

Verify installation:
```bash
ls ~/.local/share/claude-context-local  # macOS/Linux
dir %LOCALAPPDATA%\claude-context-local  # Windows
```

### 2. Index Your Codebase

**IMPORTANT**: This skill does NOT create indexes. You must index via the MCP server first.

```bash
# Use Claude Code with MCP server enabled
# The server provides the index_directory tool
```

Verify index exists:
```bash
ls -la .code-search-index/
# Expected: vector_store.db, file_mappings.json, metadata.json
```

### 3. Search

```bash
# Navigate to skill directory (or use full paths)
cd .claude/skills/searching-code-semantically

# Basic search
python scripts/search.py --query "user authentication logic"

# More results
python scripts/search.py --query "database connection pooling" --k 20

# Custom index location
python scripts/search.py --query "error handling" --storage-dir /path/to/.code-search-index
```

## Scripts Overview

### search.py
**Purpose**: Semantic code search by natural language query

**Usage**:
```bash
python scripts/search.py --query "<natural language query>" [--k <num_results>] [--storage-dir <path>]
```

**Arguments**:
- `--query` (required): Natural language description of code you're looking for
- `--k` (optional, default: 5): Number of results (5-50 recommended)
- `--storage-dir` (optional, default: `.code-search-index`): Index directory path

**Example**:
```bash
python scripts/search.py --query "JWT token validation with expiration check" --k 10
```

### find-similar.py
**Purpose**: Find code chunks semantically similar to a reference chunk

**Usage**:
```bash
python scripts/find-similar.py --chunk-id "<chunk_id_from_search>" [--k <num_results>] [--storage-dir <path>]
```

**Arguments**:
- `--chunk-id` (required): Reference chunk ID from search results
- `--k` (optional, default: 5): Number of similar chunks to return
- `--storage-dir` (optional, default: `.code-search-index`): Index directory path

**Example**:
```bash
# First, search to get a chunk_id
python scripts/search.py --query "payment processing" --k 1

# Then find similar code
python scripts/find-similar.py --chunk-id "src/payments.py:120-145" --k 10
```

### status.py
**Purpose**: Check index status and statistics

**Usage**:
```bash
python scripts/status.py [--storage-dir <path>]
```

**Arguments**:
- `--storage-dir` (optional, default: `.code-search-index`): Index directory path

**Example**:
```bash
python scripts/status.py
```

**Output**:
```json
{
  "success": true,
  "data": {
    "total_chunks": 1523,
    "total_files": 287,
    "last_updated": "2024-11-28T10:15:30",
    "model_info": {...}
  }
}
```

## API Stability Policy (CC#8)

### Stable APIs

The following are **guaranteed stable** and will NOT change in future versions:

**Script Names**:
- ✅ `search.py` - Will NOT be renamed
- ✅ `status.py` - Will NOT be renamed
- ✅ `find-similar.py` - Will NOT be renamed
- ✅ `utils.py` - Will NOT be renamed

**Script Arguments**:
- ✅ `--query` argument format (required string)
- ✅ `--chunk-id` argument format (required string)
- ✅ `--k` argument format (optional int, default 5)
- ✅ `--storage-dir` argument format (optional path string)

**JSON Output Structure**:
```json
{
  "success": true|false,
  "data": {...}|null,
  "error": "message"|null
}
```
- ✅ Top-level `success` key will always exist (boolean)
- ✅ Top-level `data` key will always exist on success
- ✅ Top-level `error` key will always exist on failure
- ✅ Output is always valid JSON
- ✅ Errors always output to stderr, success to stdout

### Evolution Policy

**When we add features**, we will:
- ✅ Add NEW scripts (e.g., `advanced-search.py`)
- ✅ Add NEW optional arguments to existing scripts
- ✅ Add NEW keys to JSON output (backwards-compatible)

**When we fix bugs**, we will:
- ✅ Fix behavior without changing APIs
- ✅ Document breaking changes in release notes if unavoidable

**We will NEVER**:
- ❌ Rename existing scripts
- ❌ Remove existing arguments
- ❌ Change argument semantics (e.g., making --k required)
- ❌ Remove keys from JSON output
- ❌ Change JSON output to non-JSON format
- ❌ Change which stream (stdout/stderr) is used for output

### Versioning

This skill follows semantic versioning:
- **Major version**: Breaking API changes (we'll avoid these!)
- **Minor version**: New features (new scripts, new optional arguments)
- **Patch version**: Bug fixes, documentation updates

**Current version**: 1.0.0 (Initial release)

### Deprecation Process

If we must deprecate an API (extremely rare), we will:

1. **Announce** deprecation in release notes
2. **Maintain** deprecated API for at least 6 months
3. **Warn** users in script output when using deprecated features
4. **Provide** migration guide
5. **Remove** only after 6+ months and major version bump

### Dependencies on claude-context-local

**External dependency**: These scripts depend on the `claude-context-local` MCP server's API.

**Compatibility**: If `claude-context-local` updates its API and breaks these scripts:
1. We'll update `utils.py` to adapt to new API
2. Script APIs remain stable (users don't change their commands)
3. Release notes will document the underlying change

**Mitigation**: All imports are centralized in `utils.py`. API changes only require updating one file.

---

## Architecture

### Design Rationale

**Why separate scripts instead of using MCP server directly?**

| Concern | MCP Server Direct | Wrapper Scripts (This Skill) |
|---------|-------------------|------------------------------|
| **Token cost** | ~10k tokens (always loaded) | 30-50 tokens (progressive disclosure) |
| **Composability** | Limited (MCP tools) | Full (shell pipes, JSON) |
| **Testing** | Requires running server | Unit testable independently |
| **Stability** | Server internals change | Stable script API |
| **Portability** | Tied to Claude Code | Works in any shell/automation |

**Tradeoffs**:
- ✅ Better for token efficiency
- ✅ Better for automation and CI/CD
- ✅ Better for testing
- ⚠️ Requires global installation
- ⚠️ Extra layer of indirection

### Component Diagram

```
┌─────────────────────────────────────┐
│   Claude Code Skill                 │
│   (searching-code-semantically)     │
└────────┬────────────────────────────┘
         │
         │ Invokes
         ↓
┌─────────────────────────────────────┐
│  Wrapper Scripts (This Skill)       │
│  - search.py                        │
│  - find-similar.py                  │
│  - status.py                        │
│  - utils.py (shared)                │
└────────┬────────────────────────────┘
         │
         │ Imports & calls
         ↓
┌─────────────────────────────────────┐
│  Global Installation                │
│  ~/.local/share/claude-context-local│
│  - search.searcher.IntelligentSearcher
│  - indexing.index_manager.CodeIndexManager
└────────┬────────────────────────────┘
         │
         │ Queries
         ↓
┌─────────────────────────────────────┐
│  Codebase Index                     │
│  .code-search-index/                │
│  - vector_store.db (SQLite)         │
│  - file_mappings.json               │
│  - metadata.json                    │
└─────────────────────────────────────┘
```

### Cross-Platform Compatibility

**Platforms supported**:
- ✅ macOS (primary testing platform)
- ✅ Linux (tested)
- ✅ Windows (designed for, limited testing - see CC#7)

**Techniques used**:
1. `pathlib.Path` for all path operations (handles `/` vs `\`)
2. `#!/usr/bin/env python3` shebang (finds python3 in PATH)
3. Platform detection in `utils.py`: `if os.name == 'nt'` for Windows-specific paths
4. Symlink resolution with `.resolve()` (CC#3)

**Windows notes**:
- Don't run scripts with `./script.py` (shebang not supported)
- Use `python scripts/search.py` instead
- Executable permissions not applicable (chmod has no effect)

See [troubleshooting.md](references/troubleshooting.md) CC#7 for Windows-specific issues.

---

## File Structure

```
.claude/skills/searching-code-semantically/
├── SKILL.md                    # Main orchestration guide (progressive disclosure entry point)
├── README.md                   # This file (architecture, API policy, quick start)
├── scripts/
│   ├── search.py               # Semantic search wrapper
│   ├── find-similar.py         # Similarity search wrapper
│   ├── status.py               # Index status checker
│   └── utils.py                # Shared utilities (setup, error handling, JSON output)
├── tests/
│   ├── test_search.py          # Unit tests for search.py
│   ├── test_find_similar.py    # Unit tests for find-similar.py
│   ├── test_status.py          # Unit tests for status.py
│   ├── test_utils.py           # Unit tests for utils.py (CC#9)
│   └── test_integration.py     # Integration tests (script interoperability)
└── references/
    ├── effective-queries.md    # Query patterns, good/bad examples
    ├── troubleshooting.md      # All 10 corner cases documented
    └── performance-tuning.md   # Optimization guide (k values, index size)
```

## Documentation

- **[SKILL.md](SKILL.md)**: Start here - main skill guide with progressive disclosure
- **[effective-queries.md](references/effective-queries.md)**: Learn how to write effective semantic queries
- **[troubleshooting.md](references/troubleshooting.md)**: Solve common issues and understand corner cases (CC#2, #4, #6, #7, #10)
- **[performance-tuning.md](references/performance-tuning.md)**: Optimize for large codebases (CC#5)

---

## Development

### Running Tests

```bash
cd .claude/skills/searching-code-semantically

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_search.py -v

# Run with coverage
pytest tests/ --cov=scripts --cov-report=html
```

**Test suite**:
- 32 total tests (27 unit + 5 integration)
- 100% pass rate
- ~80% code coverage
- Platform-aware (Windows tests skip on macOS/Linux)

### Making Scripts Executable

```bash
chmod +x scripts/*.py
```

### Debugging

**Enable verbose output**:
```bash
# Scripts don't have --verbose flag currently
# Add this to utils.py temporarily for debugging:

def error_exit(message, **kwargs):
    import sys
    error_data = {"success": False, "error": message, **kwargs}
    print(f"DEBUG: {error_data}", file=sys.stderr)  # Temporary debug line
    print(json.dumps(error_data, indent=2), file=sys.stderr)
    sys.exit(1)
```

---

## Contributing

### Reporting Bugs

Include:
1. Platform (macOS/Linux/Windows + version)
2. Python version (`python --version`)
3. Full command executed
4. Full JSON error output
5. Output of `python scripts/status.py`

### Feature Requests

Before requesting features, check:
1. Can it be achieved with existing scripts + shell tools?
2. Does it maintain API stability?
3. Does it fit the "Unix philosophy" (do one thing well)?

### Pull Requests

1. Maintain API stability (see policy above)
2. Add tests for new functionality
3. Update documentation (SKILL.md + references)
4. Follow existing code style (`pathlib`, JSON output, error handling patterns)

---

## License

This skill is part of the Claude Code ecosystem. Refer to the main project for license information.

---

## Acknowledgments

- **claude-context-local**: The MCP server that powers semantic search
- **Claude Code**: The platform this skill integrates with
- **Skill architecture**: Inspired by Unix philosophy and progressive disclosure principles

---

## Version History

### v1.0.0 (November 2024)
- Initial release
- 3 wrapper scripts (search, find-similar, status)
- Shared utilities module
- Comprehensive test suite (32 tests)
- Full documentation (SKILL.md + 3 reference docs)
- All 10 corner cases addressed and documented
- API stability policy established
