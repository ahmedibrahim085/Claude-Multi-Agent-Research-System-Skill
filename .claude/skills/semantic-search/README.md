# Semantic Search Skill - v3.0

**Find code by meaning, not keywords** - Semantic code intelligence via agent delegation with optimized incremental cache.

---

## 🎯 What Is This?

A Claude Code skill that enables **semantic search** across codebases - find functionality by describing what it does, not by guessing variable names or keywords.

Unlike traditional search (Grep/Glob), semantic search understands the **meaning** of code, finding functionally similar implementations even when using different wording, variable names, or patterns.

**Example**:
```
Query: "user authentication logic"
Finds: authenticate_user(), validateCredentials(), checkLogin(), etc.
```

---

## ⚡ Key Features

### 1. **Semantic Understanding**
- Finds code by **meaning**, not exact keywords
- Works across different languages, frameworks, naming conventions
- Discovers similar implementations automatically

### 2. **Incremental Cache System** (v3.0 - NEW!)
- ✅ **3.2x speedup** on file edits (13.67s → 4.33s)
- ✅ **98% cache hit rate** (measured on 51-file project)
- ✅ **9.34s saved** per incremental reindex
- ✅ **Automatic bloat management** via rebuild triggers

### 3. **Model Caching Optimization**
- Eliminates ~0.8s model reload overhead
- Shares embedder across instances (class-level cache)
- Enables fast incremental updates

### 4. **Auto-Reindex System**
- Background reindexing after first prompt
- Smart change detection via Merkle DAG
- 6-hour cooldown protection
- Concurrent execution protection

### 5. **Agent Orchestration**
- Delegates operations to specialized agents
- Token-optimized (agents run in separate context)
- Error interpretation (JSON → natural language)

---

## 📊 Performance (v3.0)

**Measured on 51-file Python project**:

| Operation | Time | Notes |
|-----------|------|-------|
| **Full reindex** | 13.67s | First run, model loading |
| **Incremental (1 file)** | 4.33s | **3.2x faster!** |
| **Rebuild from cache** | ~5-6s | Clears bloat, no re-embedding |
| **Cache hit rate** | 98% | 50/51 files cached |

**Speedup breakdown**:
- Embedding saved: 9.46s (from caching 50 files)
- Model reload avoided: ~0.8s (class-level caching)
- Total time saved: 9.34s per incremental reindex

---

## 🚀 Quick Start

### Installation

**1. Install Python Library** (~5 minutes):
```bash
# Clone library to standard location
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local

# Set up virtual environment
cd ~/.local/share/claude-context-local
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**2. Index Your Project**:
```bash
# Full index (first time)
scripts/incremental-reindex /path/to/project --full

# Check status
scripts/status --project /path/to/project
```

**3. Search**:
```bash
# Semantic search
scripts/search --query "user authentication logic" --project /path/to/project

# Find similar code
scripts/find-similar --chunk-id "src/auth.py:45-67:function:authenticate" --project /path/to/project
```

---

## 💾 Incremental Cache System

### How It Works

**Cache Structure**:
```
~/.claude_code_search/projects/{project}_{hash}/index/
├── code.index              # FAISS vector index
├── metadata.db             # SQLite chunk metadata
├── embeddings.pkl          # Embedding cache (NEW!)
├── merkle_snapshot.json    # Change detection
└── stats.json              # Statistics
```

**Lazy Deletion Strategy**:
1. File modified → chunks deleted from metadata + cache
2. Vectors remain in FAISS (creates "bloat")
3. Bloat exceeds threshold → auto-rebuild from cache
4. Rebuild is fast (embeddings are cached!)

**Auto-Rebuild Triggers** (Hybrid Logic):
```
Rebuild if EITHER:
1. Bloat ≥ 30%
   OR
2. Bloat ≥ 20% AND stale_count ≥ 500
```

### Performance by Project Size

| Project Size | Files | Cache Hit Rate | Expected Speedup |
|--------------|-------|----------------|------------------|
| **Small** | 20-50 | Good (~80%) | 2-3x |
| **Medium** | 50-200 | High (~90%) | 3-5x |
| **Large** | 200+ | Very High (~95%) | 5-10x+ |

---

## 🎬 Agent Orchestration

This skill uses a **2-agent architecture**:

### semantic-search-reader (READ Operations)
- **search**: Find code by natural language query
- **find-similar**: Discover semantically similar chunks
- **list-projects**: Show all indexed projects

### semantic-search-indexer (WRITE Operations)
- **index**: Create/update semantic index
- **incremental-reindex**: Smart auto-reindexing
- **status**: Check index statistics

**Never call scripts directly** - always spawn the appropriate agent via Task tool.

---

## 📖 Documentation

**Main Documentation**:
- **[SKILL.md](SKILL.md)**: Complete skill documentation (orchestration, operations, troubleshooting)

**Detailed Guides**:
- **[effective-queries.md](references/effective-queries.md)**: Query patterns and examples
- **[troubleshooting.md](references/troubleshooting.md)**: Common errors and solutions
- **[performance-tuning.md](references/performance-tuning.md)**: Optimization strategies

**Implementation Details**:
- **[model-caching-optimization.md](docs/model-caching-optimization.md)**: Phase 3 optimization (3.2x speedup)
- **[phase-3-completion-report.md](docs/phase-3-completion-report.md)**: Validation and benchmarking
- **[phase-2-completion-report.md](docs/phase-2-completion-report.md)**: Cache integration

---

## ✅ Use Cases

### When to Use Semantic Search

✅ **Exploring unfamiliar codebases**
- "How does this project handle authentication?"
- "Where is database connection pooling implemented?"

✅ **Finding functionality without keywords**
- Looking for implementations but don't know exact function names
- Need to find code that "does X" without knowing naming

✅ **Discovering similar code**
- "Find code similar to this payment processing logic"
- "Are there other implementations of rate limiting?"

✅ **Cross-reference discovery**
- Finding all authentication methods in polyglot codebase
- Locating retry logic across different services

### When NOT to Use

❌ **Use Grep for**:
- Exact string matching: `"import React"`
- Known variable/function names: `"getUserById"`
- Regex patterns: `"function.*export"`

❌ **Use Glob for**:
- Finding files by name pattern: `"**/*.test.js"`
- Locating configuration files: `"**/config.yml"`

---

## 🔧 Advanced Features

### Model Caching

**Automatic** (class-level caching):
```python
# First instance loads model
indexer1 = FixedIncrementalIndexer(project_path)  # ~0.8s

# Subsequent instances reuse cached model
indexer2 = FixedIncrementalIndexer(project_path)  # ~0.001s
```

**Manual cleanup** (free memory):
```python
FixedIncrementalIndexer.cleanup_shared_embedder()
```

### Bloat Monitoring

```bash
# Check cache effectiveness
scripts/status --project /path/to/project
# Output includes: cached_chunks, cache_hit_rate, bloat_percentage

# Force rebuild from cache
scripts/rebuild-from-cache /path/to/project
```

### Concurrent Protection

**PID-based lock files** prevent duplicate indexing:
- Lock file: `~/.claude_code_search/projects/{project}_{hash}/indexing.lock`
- Validates process is alive before spawning new operation
- Auto-cleanup of stale locks

---

## 🏗️ Architecture

**Technology Stack**:
- **Embedding Model**: google/embeddinggemma-300m (768 dimensions)
- **Vector Index**: FAISS IndexFlatIP (simple, proven, cross-platform)
- **Change Detection**: Merkle DAG (tree-sitter based)
- **Chunking**: Multi-language tree-sitter (15+ languages)
- **Cache**: Pickle-based embedding storage with version control

**Design Principles**:
- **Simplicity**: IndexFlatIP (same as MCP - proven, reliable)
- **Compatibility**: Works on all platforms (Intel, Apple Silicon, Linux, WSL)
- **Safety**: Auto-backups before rebuilds, rollback on failure
- **Quality**: Auto-rebuild triggers ensure search accuracy

---

## 📈 Version History

**v3.0** (2025-12-14):
- ✅ Incremental cache system (Phase 2)
- ✅ Model caching optimization (Phase 3)
- ✅ 3.2x speedup achieved (13.67s → 4.33s)
- ✅ 98% cache hit rate measured
- ✅ Production-ready deployment

**v2.0** (2025-12):
- Auto-reindex system with first-prompt hook
- Merkle DAG change detection
- 6-hour cooldown protection
- Concurrent execution protection

**v1.0** (2025-11):
- Initial semantic search implementation
- Agent orchestration pattern
- Basic indexing and search operations

---

## 🤝 Contributing

**Found a bug?** Create an issue with:
- Error message
- Steps to reproduce
- Project size and system info

**Performance improvements?** Share your measurements:
- Before/after timings
- Project characteristics
- System specs

---

## 📄 License

Apache 2.0

**Note**: Uses claude-context-local (GPL-3.0) via dynamic linking (PYTHONPATH imports), which preserves Apache 2.0 license. See `docs/architecture/MCP-DEPENDENCY-STRATEGY.md` for details.

---

## 🎓 Next Steps

1. **Read [SKILL.md](SKILL.md)** for complete orchestration instructions
2. **Install** the Python library dependency
3. **Index** your first project
4. **Search** and discover code by meaning!

**Questions?** Check [troubleshooting.md](references/troubleshooting.md) or create an issue.

---

**Status**: ✅ Production Ready (v3.0)
**Deployment**: Full GO (all targets exceeded)
**Performance**: 3.2x speedup on incremental reindex
**Quality**: 82/83 tests passing, end-to-end validated
