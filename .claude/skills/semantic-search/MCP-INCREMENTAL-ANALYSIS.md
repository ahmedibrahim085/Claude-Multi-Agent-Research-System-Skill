# MCP Incremental Indexing Analysis

**Date**: 2025-12-13
**Investigation**: How does MCP handle incremental with IndexFlatIP?

---

## Executive Summary

**Finding**: MCP does NOT implement true incremental indexing with IndexFlatIP.

**Approach**: "Lazy Deletion" - Delete metadata but NOT FAISS vectors

**Trade-off**: Stale vectors remain in index until periodic rebuild

---

## MCP Architecture

### File: `search/incremental_indexer.py`

**Purpose**: Provides incremental indexing interface

**Key Methods**:
- `incremental_index()` - Main entry point
- `_remove_old_chunks()` - Remove metadata for deleted/modified files
- `_add_new_chunks()` - Add embeddings for new/modified files

### File: `search/indexer.py`

**Index Type**: `IndexFlatIP` (line 77)
```python
self._index = faiss.IndexFlatIP(embedding_dimension)
```

**Key Data Structures**:
- `self._index` - FAISS IndexFlatIP instance
- `self._metadata_db` - SqliteDict with chunk metadata
- `self._chunk_ids` - List mapping FAISS position → chunk_id

---

## Critical Finding: Lazy Deletion Approach

### Method: `remove_file_chunks()` (lines 271-317)

```python
def remove_file_chunks(self, file_path: str, project_name: Optional[str] = None) -> int:
    """Remove all chunks from a specific file."""
    chunks_to_remove = []

    # Find chunks to remove
    for chunk_id in self._chunk_ids:
        metadata_entry = self.metadata_db.get(chunk_id)
        if not metadata_entry:
            continue

        metadata = metadata_entry['metadata']
        chunk_file = metadata.get('file_path') or metadata.get('relative_path')

        if file_path in chunk_file or chunk_file in file_path:
            if project_name and metadata.get('project_name') != project_name:
                continue
            chunks_to_remove.append(chunk_id)

    # Remove chunks from metadata
    for chunk_id in chunks_to_remove:
        del self.metadata_db[chunk_id]

    # ⚠️ CRITICAL LINE ⚠️
    # Note: We don't remove from FAISS index directly as it's complex
    # Instead, we'll rebuild the index periodically or on demand

    self.metadata_db.commit()
    return len(chunks_to_remove)
```

---

## How It Works (The Workaround)

### Step 1: Initial Index
```
FAISS Index:    [vec0, vec1, vec2, vec3, vec4]
Chunk IDs:      [id_A, id_B, id_C, id_D, id_E]
Metadata DB:    {id_A: {...}, id_B: {...}, ...}
```

### Step 2: File Deleted (e.g., file contains chunks B and D)
```python
# MCP's remove_file_chunks():
del self.metadata_db[id_B]  # Delete from metadata
del self.metadata_db[id_D]  # Delete from metadata

# BUT: FAISS index is NOT modified!
```

### Step 3: After Removal
```
FAISS Index:    [vec0, vec1, vec2, vec3, vec4]  ← UNCHANGED!
Chunk IDs:      [id_A, id_B, id_C, id_D, id_E]  ← UNCHANGED!
Metadata DB:    {id_A: {...}, id_C: {...}, id_E: {...}}  ← B and D deleted
```

### Step 4: Search Impact
```python
# When searching:
results = index.search(query, k=5)
# Returns positions [1, 3, 0, 2, 4]

for position in results:
    chunk_id = chunk_ids[position]  # Gets id_B or id_D
    metadata = metadata_db.get(chunk_id)  # Returns None!

    if not metadata:
        continue  # Skip stale entry
```

---

## The Problems with This Approach

### Problem 1: Index Bloat
- Deleted chunks remain in FAISS index
- Index size grows over time
- Search becomes slower (more vectors to compare)
- Memory waste

### Problem 2: Search Quality Degradation
- FAISS returns stale chunks
- Must filter results after search
- Wastes k positions on deleted chunks
- Example: Ask for k=5, get 3 valid + 2 stale

### Problem 3: Eventually Requires Rebuild
- Index bloat grows unbounded
- At some point, MUST rebuild entire index
- Rebuild = full reindex (defeats purpose of incremental!)

### Problem 4: Inconsistent State
- FAISS index out of sync with metadata
- chunk_ids list contains deleted IDs
- Confusion about "true" index size

---

## MCP's Periodic Rebuild Strategy

**Evidence from code**: Comment says "rebuild periodically or on demand"

**NOT IMPLEMENTED**: No automatic rebuild logic found in code

**Implication**: Users must manually trigger full reindex when index bloat becomes problematic

---

## Is This "Incremental Indexing"?

**Technically**: NO
- Does NOT incrementally update FAISS index
- Only incrementally updates metadata
- Requires eventual full rebuild

**Practically**: PARTIAL
- Avoids re-embedding unchanged files (saves time)
- Avoids re-chunking unchanged files (saves time)
- But index still contains stale vectors

**Trade-off**:
- ✅ Faster than full reindex (skip unchanged files)
- ✅ No complex FAISS manipulation
- ❌ Index bloat over time
- ❌ Degraded search quality
- ❌ Eventually needs full rebuild

---

## Why MCP Chose This Approach

### IndexFlatIP Limitation
```python
# IndexFlatIP does NOT support:
index.remove_ids([1, 3, 5])  # ❌ Method doesn't exist!

# Only IndexIDMap2 supports:
index.remove_ids([1, 3, 5])  # ✅ But crashes on Apple Silicon
```

### The Dilemma
1. **IndexIDMap2**: Supports removal but crashes on Apple Silicon
2. **IndexFlatIP**: Works on Apple Silicon but no removal support

**MCP's Choice**: Use IndexFlatIP + lazy deletion workaround

---

## Alternative Approaches (Not Used by MCP)

### Option 1: Rebuild FAISS from Metadata
```python
def rebuild_faiss_from_metadata():
    # Clear FAISS index
    new_index = faiss.IndexFlatIP(dimension)
    new_chunk_ids = []

    # Re-add only chunks that exist in metadata
    for chunk_id, entry in metadata_db.items():
        embedding = get_cached_embedding(chunk_id)  # Need embedding cache!
        new_index.add(embedding)
        new_chunk_ids.append(chunk_id)

    # Replace index
    self._index = new_index
    self._chunk_ids = new_chunk_ids
```

**Problem**: Requires storing embeddings separately from FAISS!

### Option 2: Partition-Based Index
```python
# Multiple small indices per file/module
file_indices = {
    'file_a.py': IndexFlatIP(dim),
    'file_b.py': IndexFlatIP(dim),
    'file_c.py': IndexFlatIP(dim)
}

# On file change: Replace only that file's index
file_indices['file_b.py'] = rebuild_index_for_file('file_b.py')
```

**Problem**: Search complexity, merging results from multiple indices

### Option 3: Build Custom Index
```python
class IncrementalFlatIndex:
    def __init__(self):
        self.vectors = []  # List of embeddings
        self.chunk_ids = []
        self.deleted = set()  # Deleted positions

    def remove(self, position):
        self.deleted.add(position)

    def search(self, query, k):
        # Brute force search, skip deleted
        results = []
        for i, vec in enumerate(self.vectors):
            if i in self.deleted:
                continue
            score = np.dot(query, vec)
            results.append((i, score))
        return sorted(results, reverse=True)[:k]
```

**Problem**: Performance, no FAISS optimizations

---

## MCP's Actual "Incremental" Value

**What MCP Optimizes**:
1. ✅ Skip chunking unchanged files
2. ✅ Skip embedding unchanged files
3. ✅ Merkle tree change detection

**What MCP Does NOT Optimize**:
1. ❌ FAISS index size (grows over time)
2. ❌ Search performance (degradesover time)
3. ❌ Eventually requires full rebuild

**Real Value**: ~50-70% time savings on reindex (embedding is slow)

**But**: Index quality degrades until full rebuild needed

---

## Conclusion

**MCP's "Incremental Indexing" is**:
- A pragmatic workaround for IndexFlatIP's limitations
- Optimizes embedding/chunking (major time cost)
- Does NOT truly update FAISS index incrementally
- Relies on eventual full rebuild

**For our Claude Code Skill**:
- We can copy this approach (it works!)
- But we should be honest about limitations
- Document when full rebuild is needed
- Consider adding automatic rebuild trigger

---

## Next Steps

1. ✅ Understand MCP's approach
2. ⏳ Research if there are BETTER approaches
3. ⏳ Design CORRECT POC based on findings
4. ⏳ Implement and test
