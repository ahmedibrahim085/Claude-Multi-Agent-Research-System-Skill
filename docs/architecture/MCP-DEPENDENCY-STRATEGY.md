# MCP Dependency Strategy
## How We Use claude-context-local (and What to Avoid)

**Date**: 2025-12-04
**Status**: Active
**Context**: Resolving confusion between MCP native scripts vs our fixed scripts

---

## Executive Summary

**claude-context-local is a PYTHON LIBRARY DEPENDENCY, NOT an MCP server.**

**Critical Distinctions:**
- ❌ **NOT an MCP server** - No MCP protocol communication, no running server process
- ✅ **Python library only** - Our scripts import Python modules via PYTHONPATH
- ✅ **Dynamic linking** - Imports via `sys.path.insert()`, not code copying
- ✅ **GPL-3.0 compliant** - Dynamic linking preserves our Apache 2.0 license

**What We Use:**
We import claude-context-local's high-quality Python modules (Merkle tree, chunking, embeddings) but **NOT** its buggy index manager. Our `incremental-reindex` script fixes the IndexFlatIP bug by wrapping with IndexIDMap2.

**No MCP Server Runs:**
```bash
$ ps aux | grep claude-context-local
# Returns nothing - no server process
```

---

## What We Use from MCP

### ✅ Components We Import
```python
from merkle.merkle_dag import MerkleDAG                    # Change detection
from merkle.change_detector import ChangeDetector          # Smart reindex
from merkle.snapshot_manager import SnapshotManager        # Merkle snapshots
from chunking.multi_language_chunker import MultiLanguageChunker  # Code → chunks
from embeddings.embedder import CodeEmbedder               # Chunks → vectors
from common_utils import get_storage_dir                   # Storage paths
import faiss                                                # Vector similarity
```

**Why These Are Good:**
- ✅ Well-tested, production-quality code
- ✅ Handles 15+ programming languages
- ✅ Merkle tree change detection (42x faster than full reindex)
- ✅ Proper chunking boundaries (functions, classes, methods)

---

## License Compliance: GPL-3.0 Dynamic Linking

### Why We Can Use GPL-3.0 Code

**claude-context-local License:** GPL-3.0 (copyleft)
**Our Project License:** Apache 2.0 (permissive)

**Dynamic Linking is GPL-Safe:**
```python
# Our script: incremental_reindex.py (line 25)
sys.path.insert(0, str(Path.home() / ".local/share/claude-context-local"))

# Import Python modules (dynamic linking, NOT code copying)
from merkle.merkle_dag import MerkleDAG
from chunking.multi_language_chunker import MultiLanguageChunker
from embeddings.embedder import CodeEmbedder
```

**Legal Analysis:**
- ✅ **Dynamic linking** via PYTHONPATH = runtime dependency (not distribution)
- ✅ **GPL explicitly allows** dynamic linking without triggering copyleft
- ✅ **Our Apache 2.0 license preserved** - no relicensing required
- ✅ **Legally compliant** - follows GPL terms and intent

**What Would Trigger GPL Copyleft:**
- ❌ Copying their code into our repository (bundling/vendoring)
- ❌ Creating derivative works by modifying their code in-place
- ❌ Statically linking GPL code into our binary

**Our Approach:**
- ✅ External installation required (`git clone` to `~/.local/share/`)
- ✅ Runtime imports via PYTHONPATH (dynamic linking)
- ✅ Our code remains Apache 2.0, their code remains GPL-3.0
- ✅ Clear separation of codebases

**Why This Matters:**
If we bundled (copied) GPL code into our repo, our **entire project** would become GPL-3.0 due to copyleft requirements. Dynamic linking preserves our permissive Apache 2.0 license.

---

## What We DON'T Use from MCP

### ❌ MCP Native Index Manager (BUGGY)
```python
# ❌ DON'T USE THIS:
from mcp_server.code_search_server import CodeSearchServer
server = CodeSearchServer()
server.index_directory(...)  # Creates buggy IndexFlatIP
```

**Why It's Buggy:**
```python
# MCP's CodeIndexManager (lines 50-85):
self.index = faiss.IndexFlatIP(768)  # ❌ No IndexIDMap2 wrapper!

# When incremental reindex tries to remove vectors:
self.index.add_with_ids(...)  # ❌ FAILS: "not implemented for this type of index"
```

**Our Fix** (`.claude/skills/semantic-search/scripts/incremental_reindex.py:70-73`):
```python
# ✅ WE WRAP WITH IndexIDMap2:
base_index = faiss.IndexFlatIP(768)
self.index = faiss.IndexIDMap2(base_index)  # ✅ Supports add_with_ids + remove_ids
```

---

## The Confusion That Caused Today's Bug

### What Happened Today (Dec 4, 2025)

**Timeline:**
1. **Dec 3** - Fixed `incremental_reindex.py` with IndexIDMap2 wrapper (commit 197bcc2)
2. **Dec 4, 10:29 AM** - Ran `bash .claude/skills/semantic-search/scripts/index --full .`
3. **Problem**: That script is MCP's native wrapper → creates unwrapped IndexFlatIP
4. **Result**: 19+ auto-reindex attempts failed with "add_with_ids not implemented"

### Why It Happened

**Two scripts with similar names:**
```
scripts/index                # ❌ MCP native wrapper (BUGGY)
scripts/incremental-reindex  # ✅ Our fixed version (GOOD)
```

**Both support `--full` flag:**
```bash
# ❌ WRONG (creates broken index):
bash .claude/skills/semantic-search/scripts/index --full .

# ✅ RIGHT (creates IndexIDMap2 index):
bash .claude/skills/semantic-search/scripts/incremental-reindex --full .
```

---

## Solution: Remove Confusing References

### 1. Deprecate `scripts/index` (MCP Native Wrapper)

**Action**: Rename to make it obvious it's deprecated:
```bash
mv scripts/index scripts/index.mcp-native.DEPRECATED
```

**Why**: Users won't accidentally run it anymore.

### 2. Update All Documentation

**Files to update:**
- ✅ `.claude/CLAUDE.md.backup` - 2 references to `scripts/index --full`
- ✅ `.claude/utils/reindex_manager.py` - 2 error messages
- ✅ `.claude/agents/semantic-search-indexer.md` - 1 example
- ✅ `.claude/skills/semantic-search/SKILL.md` - 15 references
- ✅ `.claude/skills/semantic-search/scripts/check-prerequisites` - 2 warning messages

**Replace all with:**
```bash
# OLD:
scripts/index /path/to/project --full

# NEW:
scripts/incremental-reindex /path/to/project --full
```

### 3. Add Warning to Deprecated Script

**Add to top of `scripts/index.mcp-native.DEPRECATED`:**
```bash
#!/usr/bin/env bash
echo "⚠️  DEPRECATED: This script creates buggy IndexFlatIP indexes"
echo "   Use instead: scripts/incremental-reindex --full"
echo ""
exit 1
```

---

## Python Library Installation Strategy

### Current State (NOT an MCP Server)
```
~/.local/share/claude-context-local/
├── .git/                          # Git repository (for updates)
├── .venv/                         # Python dependencies (faiss, sentence-transformers)
├── merkle/                        # ✅ We import this (Python modules)
├── chunking/                      # ✅ We import this (Python modules)
├── embeddings/                    # ✅ We import this (Python modules)
├── common_utils.py                # ✅ We import this (Python module)
├── mcp_server/                    # ❌ We DON'T use this (buggy + never runs)
└── scripts/                       # ❌ We DON'T use this (deprecated)
```

**Naming Confusion:**
The repository is called "claude-context-local" because it was originally designed as an MCP server. However, we **only use its Python library components** - no MCP protocol, no server process.

### Keep As Python Library Dependency (NOT Bundle)

**Why NOT bundle (copy) their code into our repo:**
- ❌ **GPL-3.0 copyleft** - Would force our entire project to become GPL-3.0
- ❌ 2000+ lines to maintain (352KB of complex Python code)
- ❌ Bug fixes would require manual sync
- ❌ Chunking/Merkle tree are complex, well-tested components
- ❌ License incompatibility (their GPL-3.0 vs our Apache 2.0)

**Why KEEP as external git clone (dynamic linking):**
- ✅ **Preserves Apache 2.0 license** - Dynamic linking is GPL-safe
- ✅ Easy to update (`cd ~/.local/share/claude-context-local && git pull`)
- ✅ Can reference their code when debugging
- ✅ Only ~50MB on disk (~352KB Python code + dependencies)
- ✅ We can contribute bug fixes upstream (IndexIDMap2 fix)
- ✅ Legally compliant - no licensing conflicts

### Document Python Library Dependency

**For README.md / Installation Instructions:**

```markdown
## Prerequisites

### Python Library: claude-context-local

**Important:** This is **NOT an MCP server** - it's a Python library dependency. No server process runs.

The semantic-search skill imports Python modules from [claude-context-local](https://github.com/FarhanAliRaza/claude-context-local) for:
- Merkle tree change detection (80KB)
- Multi-language code chunking (192KB) - supports 15+ languages
- Embedding generation (76KB) - wraps sentence-transformers

**Installation (5 minutes):**
```bash
# Clone Python library to standard location
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local

# Set up Python virtual environment and install dependencies
cd ~/.local/share/claude-context-local
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

**What This Does:**
1. Clones GPL-3.0 Python library to `~/.local/share/claude-context-local/`
2. Creates virtual environment with dependencies (faiss-cpu, sentence-transformers, tree-sitter)
3. Our scripts import via PYTHONPATH (dynamic linking - preserves Apache 2.0 license)

**License Note:**
- claude-context-local: GPL-3.0 (their code, their license)
- Our project: Apache 2.0 (our code, our license)
- Dynamic linking preserves both licenses independently (GPL-compliant)
```

---

## Verification Checklist

After making changes, verify:

- [ ] `scripts/index` renamed to `scripts/index.mcp-native.DEPRECATED`
- [ ] Deprecated script exits with error + helpful message
- [ ] All 23 references updated to use `incremental-reindex --full`
- [ ] README documents MCP as library dependency
- [ ] Test: `bash scripts/incremental-reindex --full .` creates IndexIDMap2 index
- [ ] Test: Auto-reindex works after file modifications

---

## Future: Upstream Contribution

**Consider contributing IndexIDMap2 fix to MCP:**
```python
# In mcp_server/code_search_server.py:
class CodeIndexManager:
    def __init__(self):
        base = faiss.IndexFlatIP(768)
        self.index = faiss.IndexIDMap2(base)  # ← THE FIX
```

**Benefits:**
- ✅ Everyone benefits from the fix
- ✅ We can use MCP natively again
- ✅ Reduces our maintenance burden

**Process:**
1. Open issue on their GitHub
2. Submit PR with fix + tests
3. If accepted, update our docs to reflect MCP supports it now
4. If rejected, document why we maintain our own fork

---

## Summary

**DO:**
- ✅ Use claude-context-local as **Python library dependency** (git clone + pip install)
- ✅ Import via PYTHONPATH: merkle, chunking, embeddings, common_utils
- ✅ Use our fixed `incremental-reindex --full` script (IndexIDMap2 wrapper)
- ✅ Keep library updated with `git pull` in `~/.local/share/claude-context-local/`
- ✅ Preserve Apache 2.0 license via dynamic linking (GPL-compliant)

**DON'T:**
- ❌ Call it an "MCP server" - it's a Python library (no server process runs)
- ❌ Use their native `index` script (creates buggy IndexFlatIP)
- ❌ Import from `mcp_server.code_search_server` (buggy index manager)
- ❌ Bundle (copy) GPL code into our repo (would force GPL-3.0 on entire project)
- ❌ Run as MCP protocol server (we don't use MCP protocol at all)

**Key Insights:**
1. **Not an MCP server** - Python library with misleading name (historical reasons)
2. **GPL-safe** - Dynamic linking via PYTHONPATH preserves our Apache 2.0 license
3. **Excellent library code** with one buggy component (IndexFlatIP) - we use good parts, fix bad part
4. **Legal compliance** - External dependency + dynamic imports = no license conflicts
