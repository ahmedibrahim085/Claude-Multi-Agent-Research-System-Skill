# MCP Dependency Strategy
## How We Use claude-context-local (and What to Avoid)

**Date**: 2025-12-04
**Status**: Active
**Context**: Resolving confusion between MCP native scripts vs our fixed scripts

---

## Executive Summary

**claude-context-local is a LIBRARY DEPENDENCY, not a service we run.**

We use MCP's high-quality components (Merkle tree, chunking, embeddings) but **NOT** its buggy index manager. Our `incremental-reindex` script fixes the IndexFlatIP bug by wrapping with IndexIDMap2.

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

## MCP Installation Strategy

### Current State
```
~/.local/share/claude-context-local/
├── .git/                          # Git repository (for updates)
├── .venv/                         # Python dependencies
├── merkle/                        # ✅ We use this
├── chunking/                      # ✅ We use this
├── embeddings/                    # ✅ We use this
├── common_utils.py                # ✅ We use this
├── mcp_server/                    # ❌ We DON'T use this (buggy)
└── scripts/                       # ❌ We DON'T use this
```

### Keep MCP As Library Dependency

**Why NOT copy MCP code into our repo:**
- ❌ 2000+ lines to maintain
- ❌ Bug fixes would require manual sync
- ❌ Chunking/Merkle tree are complex, well-tested

**Why KEEP as git clone:**
- ✅ Easy to update (`cd ~/.local/share/claude-context-local && git pull`)
- ✅ Can reference their code when debugging
- ✅ Only ~50MB on disk
- ✅ We can contribute bug fixes upstream

### Document MCP as Library Dependency

**In README.md:**
```markdown
## Dependencies

### claude-context-local (Library Only)
We use components from [claude-context-local](https://github.com/FarhanAliRaza/claude-context-local):
- Merkle tree change detection
- Multi-language code chunking
- Embedding generation

**Installation:**
```bash
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local
cd ~/.local/share/claude-context-local
python3 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

**Note**: We use MCP as a library, not as a running service. Our scripts import MCP's components but implement our own fixed index manager.
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
- ✅ Use MCP as library dependency (git clone)
- ✅ Import: merkle, chunking, embeddings, common_utils
- ✅ Use our fixed `incremental-reindex --full` script
- ✅ Keep MCP updated with `git pull`

**DON'T:**
- ❌ Use MCP's native `index` script (creates buggy IndexFlatIP)
- ❌ Import from `mcp_server.code_search_server`
- ❌ Copy MCP code into our repo (maintenance nightmare)
- ❌ Run MCP as a service (we don't need the server)

**Key Insight**: MCP is excellent library code with one buggy component. We use the good parts and fix the bad part.
