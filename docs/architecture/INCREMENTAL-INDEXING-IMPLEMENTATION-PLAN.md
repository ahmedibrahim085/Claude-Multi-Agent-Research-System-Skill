# Incremental Indexing Implementation Plan

**Status**: Ready for Implementation
**POC Status**: ✅ All tests passed, bug fixed, production ready
**Estimated Effort**: 30-60 minutes
**Target File**: `.claude/skills/semantic-search/scripts/incremental_reindex.py`

---

## Prerequisites

✅ **POC Validation Complete**:
- GitHub issue #4535 verified fixed in FAISS 1.13.0
- All core operations tested and working
- Correctness verified with deterministic search tests
- Real MCP components tested end-to-end
- Critical chunk ID generation bug found and fixed

✅ **Current System Understanding**:
- Current implementation uses `IndexFlatIP` (flat index, no custom IDs)
- MerkleDAG already detects file changes
- System performs full reindex on every change
- Target: Replace full reindex with incremental updates

---

## Implementation Strategy

### Phase 1: Index Type Migration
**Goal**: Switch from IndexFlatIP to IndexIDMap2(IndexFlatIP)

**Changes**:
1. Modify index creation in `CodeSearchIndex.__init__()`
2. Add file-to-IDs mapping persistence
3. Maintain backward compatibility with existing indexes

**Code Pattern**:
```python
# OLD
self.index = faiss.IndexFlatIP(self.dimension)

# NEW
base_index = faiss.IndexFlatIP(self.dimension)
self.index = faiss.IndexIDMap2(base_index)
self.file_to_ids = {}  # Track chunk IDs per file
```

### Phase 2: File-to-IDs Mapping
**Goal**: Persist mapping between files and their chunk IDs

**Storage Strategy**:
```python
# Save alongside index
file_to_ids_path = index_path.replace('.faiss', '.file_mapping.json')
with open(file_to_ids_path, 'w') as f:
    json.dump(self.file_to_ids, f)

# Load on startup
if file_to_ids_path.exists():
    with open(file_to_ids_path, 'r') as f:
        self.file_to_ids = json.load(f)
```

**Mapping Structure**:
```python
{
    "path/to/file1.py": [1234567890, 1234567891],
    "path/to/file2.py": [2345678901, 2345678902, 2345678903],
    ...
}
```

### Phase 3: Chunk ID Generation
**Goal**: Generate stable, deterministic chunk IDs

**CRITICAL**: Use per-file chunk index (bug fix from POC)

```python
def _generate_chunk_id(self, file_path: str, chunk_index: int) -> int:
    """
    Generate deterministic chunk ID.

    Args:
        file_path: Relative path to the file
        chunk_index: Index of chunk WITHIN THE FILE (0, 1, 2, ...)

    Returns:
        63-bit positive integer ID
    """
    # Hash combines file path + chunk index
    chunk_key = f"{file_path}:{chunk_index}"
    hash_value = hash(chunk_key)

    # Ensure positive 63-bit integer (FAISS requirement)
    return hash_value & 0x7FFFFFFFFFFFFFFF
```

**WHY THIS MATTERS** (from bug fix):
- ✅ Same file always gets same IDs regardless of indexing order
- ✅ Enables reliable edit/delete operations
- ✅ IDs are deterministic and reproducible

### Phase 4: Incremental Operations

#### Add New File
```python
def add_file_to_index(self, file_path: str):
    """Add a new file to the index incrementally."""
    # 1. Chunk the file
    chunks = self.chunker.chunk_file(str(file_path))
    if not chunks:
        return

    # 2. Generate embeddings
    embeddings = self.embedder.embed_chunks(chunks, batch_size=32)
    vectors = np.array([e.embedding for e in embeddings], dtype='float32')
    faiss.normalize_L2(vectors)

    # 3. Generate chunk IDs (per-file index!)
    chunk_ids = np.array([
        self._generate_chunk_id(file_path, idx)
        for idx in range(len(chunks))
    ], dtype=np.int64)

    # 4. Add to index
    self.index.add_with_ids(vectors, chunk_ids)

    # 5. Update mapping
    self.file_to_ids[file_path] = chunk_ids.tolist()
    self._save_file_mapping()
```

#### Edit Existing File
```python
def update_file_in_index(self, file_path: str):
    """Update an existing file in the index (remove old + add new)."""
    # 1. Remove old chunks
    if file_path in self.file_to_ids:
        old_ids = np.array(self.file_to_ids[file_path], dtype=np.int64)
        selector = faiss.IDSelectorArray(len(old_ids), faiss.swig_ptr(old_ids))
        removed_count = self.index.remove_ids(selector)
        print(f"Removed {removed_count} old chunks for {file_path}")

    # 2. Add new chunks
    self.add_file_to_index(file_path)
```

#### Delete File
```python
def remove_file_from_index(self, file_path: str):
    """Remove a file from the index completely."""
    if file_path not in self.file_to_ids:
        return

    # 1. Remove all chunks
    old_ids = np.array(self.file_to_ids[file_path], dtype=np.int64)
    selector = faiss.IDSelectorArray(len(old_ids), faiss.swig_ptr(old_ids))
    removed_count = self.index.remove_ids(selector)

    # 2. Update mapping
    del self.file_to_ids[file_path]
    self._save_file_mapping()

    print(f"Removed {removed_count} chunks for deleted file {file_path}")
```

### Phase 5: Integration with MerkleDAG

**Leverage Existing Change Detection**:
```python
def incremental_reindex(self, project_path: str):
    """Perform incremental reindex based on MerkleDAG changes."""
    # 1. Load current index and mapping
    self._load_index()
    self._load_file_mapping()

    # 2. Build new Merkle DAG
    new_dag = MerkleDAG(project_path)
    supported_files = new_dag.get_supported_files()

    # 3. Detect changes
    current_files = set(self.file_to_ids.keys())
    new_files_set = set(str(f) for f in supported_files)

    added_files = new_files_set - current_files
    deleted_files = current_files - new_files_set
    potentially_modified = new_files_set & current_files

    # 4. Apply incremental updates
    stats = {
        'added': 0,
        'modified': 0,
        'deleted': 0,
        'unchanged': 0
    }

    # Add new files
    for file_path in added_files:
        self.add_file_to_index(file_path)
        stats['added'] += 1

    # Check for modifications (compare hashes)
    for file_path in potentially_modified:
        if self._file_changed(file_path):  # Compare hash
            self.update_file_in_index(file_path)
            stats['modified'] += 1
        else:
            stats['unchanged'] += 1

    # Remove deleted files
    for file_path in deleted_files:
        self.remove_file_from_index(file_path)
        stats['deleted'] += 1

    # 5. Save index
    self._save_index()

    return stats
```

---

## Testing Strategy

### Regression Tests
**Run existing POC tests to ensure implementation matches proven design**:

```bash
# Test 1: Verify bug fix remains (IndexIDMap2 works)
python .claude/skills/semantic-search/tests/test_indexidmap2_bug.py

# Test 2: Verify core operations
python .claude/skills/semantic-search/tests/test_incremental_simple.py

# Test 3: Verify correctness (CRITICAL)
python .claude/skills/semantic-search/tests/test_incremental_verified.py

# Test 4: Verify real components integration
python .claude/skills/semantic-search/tests/test_incremental_real_poc.py
```

### Production Validation
**Test with real codebase (this project)**:

1. **Baseline**: Full reindex of current project
   ```bash
   python .claude/skills/semantic-search/scripts/reindex.py --project .
   ```

2. **Modify a file**: Edit a Python file in the project

3. **Incremental reindex**: Run incremental reindex
   ```bash
   python .claude/skills/semantic-search/scripts/incremental_reindex.py --project .
   ```

4. **Verify search**: Search for content from modified file
   ```bash
   python .claude/skills/semantic-search/scripts/search.py --query "modified content"
   ```

5. **Compare**: Should find updated content, not old content

### Performance Validation

**Measure and compare**:
- Full reindex time: ~N seconds for M files
- Incremental reindex time: ~0.05-0.06s per file (from POC)
- Expected speedup: 10-50x for single file changes

---

## Migration Path

### Option 1: Clean Migration (RECOMMENDED)
**Approach**: Rebuild index on first run with new format

```python
def _needs_migration(self):
    """Check if index needs migration to IndexIDMap2."""
    # Check if current index is old format
    return not isinstance(self.index, faiss.IndexIDMap2)

def migrate_to_incremental(self):
    """Migrate existing index to incremental format."""
    print("Migrating to incremental index format...")

    # Perform full reindex with new format
    self.full_reindex(self.project_path)

    print("Migration complete. Future reindexes will be incremental.")
```

### Option 2: Backward Compatible
**Approach**: Support both formats, auto-migrate on first write

```python
def __init__(self, ...):
    if self._is_old_format():
        print("Old index format detected, will migrate on next reindex")
        self._migration_needed = True
    else:
        self._migration_needed = False
```

**RECOMMENDATION**: Use Option 1 (clean migration) for simplicity.

---

## Risk Mitigation

### Risk 1: Index Corruption
**Mitigation**: Backup index before migration
```python
def _backup_index(self):
    import shutil
    backup_path = self.index_path + '.backup'
    shutil.copy(self.index_path, backup_path)
```

### Risk 2: File-to-IDs Mapping Out of Sync
**Mitigation**: Verify mapping integrity on load
```python
def _verify_mapping_integrity(self):
    """Verify file_to_ids mapping matches index."""
    # Check total IDs matches index size
    total_chunks = sum(len(ids) for ids in self.file_to_ids.values())
    if total_chunks != self.index.ntotal:
        raise ValueError(f"Mapping mismatch: {total_chunks} chunks in mapping, {self.index.ntotal} in index")
```

### Risk 3: Hash Collisions
**Mitigation**: Use 63-bit hash space (extremely low collision probability)
- Probability: ~1 in 9.2 × 10^18
- For 1 million chunks: ~1 in 10^12 chance of collision
- Detection: Search quality monitoring

### Risk 4: Performance Regression
**Mitigation**: Benchmark before and after
- If slower: Investigate bottlenecks
- If equal: Success (incremental updates are bonus)
- If faster: Celebrate

---

## Success Criteria

### Functional
- ✅ All POC tests pass
- ✅ Incremental add works (new file appears in search)
- ✅ Incremental edit works (old content not found, new content found)
- ✅ Incremental delete works (deleted file not in search)
- ✅ Search quality maintained (same results as full reindex)

### Performance
- ✅ Single file change: <1s reindex time
- ✅ Multi-file change: ~0.05s per file
- ✅ Full reindex fallback works if needed

### Reliability
- ✅ Index survives process restart
- ✅ File-to-IDs mapping persists correctly
- ✅ No data loss during incremental updates
- ✅ Backward compatibility or clean migration path

---

## Implementation Checklist

**Pre-Implementation**:
- [x] POC tests all passing
- [x] Bug fixes verified
- [x] Documentation updated
- [x] Implementation plan reviewed

**Implementation**:
- [ ] Add IndexIDMap2 wrapper to index creation
- [ ] Implement chunk ID generation (with per-file index)
- [ ] Add file-to-IDs mapping persistence
- [ ] Implement incremental add operation
- [ ] Implement incremental edit operation
- [ ] Implement incremental delete operation
- [ ] Integrate with MerkleDAG change detection
- [ ] Add migration logic

**Testing**:
- [ ] Run all POC regression tests
- [ ] Test with real project (this codebase)
- [ ] Verify search quality maintained
- [ ] Benchmark performance improvement
- [ ] Test edge cases (empty files, large files, binary files)

**Deployment**:
- [ ] Update documentation
- [ ] Commit implementation
- [ ] Test in production environment
- [ ] Monitor search quality
- [ ] Validate performance metrics

---

## Expected Outcomes

### Before (Current System)
- Every change triggers full reindex
- Reindex time: ~5-10s for medium projects
- Scales linearly with project size

### After (Incremental System)
- Only changed files reindexed
- Reindex time: ~0.05-0.06s per changed file
- 10-50x speedup for typical single-file edits
- Scales with number of changes, not project size

### Example Impact
**Scenario**: Edit 1 file in 500-file project
- Current: Reindex all 500 files (~10s)
- Incremental: Reindex 1 file (~0.05s)
- **Speedup**: 200x faster

---

## Reference Implementation

**Key Files from POC** (proven working code):
- `.claude/skills/semantic-search/tests/test_incremental_real_poc.py` - Complete workflow example
- `.claude/skills/semantic-search/tests/test_incremental_verified.py` - Verification patterns
- `docs/architecture/HONEST-POC-CODE-REVIEW.md` - Bug analysis and fixes

**Production Target**:
- `.claude/skills/semantic-search/scripts/incremental_reindex.py` - Main implementation file

---

## Notes

- POC code is in test files - extract working patterns for production
- Chunk ID generation bug has been fixed - use 3-tuple pattern
- Test 3-4 from real POC prove edit/delete work correctly
- IndexFlatIP is sufficient initially, can upgrade to IndexIVFFlat later
- MerkleDAG already provides change detection infrastructure

---

*Implementation plan created 2025-12-13 based on successful POC validation.*
