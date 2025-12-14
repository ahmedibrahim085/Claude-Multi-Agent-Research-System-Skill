# Incremental Cache Integration Plan
## Embedding Cache + Lazy Deletion for Semantic Search

**Status**: Planning Phase
**Created**: 2025-12-14
**Timeline**: 6-8 days (with buffer)
**Approach**: Evidence-based, YAGNI-compliant, Test-First

---

## Executive Summary

### Problem
Current full reindex takes **246.24 seconds** (measured baseline, 316 files, 9,992 chunks) every time, even when only a few files change. This is slow for iterative development workflows.

### Solution
Add **embedding cache** to FixedCodeIndexManager to prevent re-embedding unchanged files:
- Cache embeddings separately (pickle format)
- Track bloat from lazy deletion
- Rebuild periodically from cache (no re-embedding)
- Incremental add/edit/delete operations

### Timeline
- **Phase 1**: Benchmarking ✅ **COMPLETE** - Embedding confirmed as bottleneck
- **Phase 2**: Implementation (5-6 days) - Test-first for each feature
- **Phase 3**: Validation (1 day) - Measure actual speedup
- **Total**: 6-8 days with buffer (vs POC's 18-20 days)

### Benchmark Results (VALIDATED)
**Embedding dominates reindex time**:
- **Embedding**: 241.89s (98.2%) ← **DOMINANT BOTTLENECK**
- DAG build: 2.75s (1.1%)
- Chunking: 0.97s (0.4%)
- Index save: 0.42s (0.2%)
- All other phases: <0.5s (<0.3%)

**Theoretical Maximum Speedup**: If we cache 100% of embeddings, we eliminate 98.2% of reindex time:
- Current: 246.24s
- Theoretical minimum: 4.35s (remaining 1.8%)
- **Maximum speedup: 56x**

### Expected Results (Evidence-Based)
**Conservative Targets** (assumes some overhead):
- **Single file edit**: <10s (vs 246s) - **25x speedup**
- **10 file edits**: <50s (vs 246s) - **5x speedup**
- **Rebuild from cache**: <30s (vs 246s) - **8x speedup**

**Why Conservative**: Cache lookup overhead, Merkle tree checks, FAISS operations still needed. Real-world speedup will be less than theoretical 56x but should far exceed 4x target.

---

## Evidence-Based Rationale

### What We Verified

**1. Baseline Performance** (Measured, Not Assumed)
```
Full Reindex: 246.24 seconds (~4.1 minutes)
Files: 316
Chunks: 9,992
Device: Apple Silicon (mps:0)

Timing Breakdown:
- Embedding:      241.89s (98.2%) ← TARGET FOR OPTIMIZATION
- DAG build:        2.75s ( 1.1%)
- Chunking:         0.97s ( 0.4%)
- Index save:       0.42s ( 0.2%)
- Snapshot save:    0.15s ( 0.1%)
- All others:      <0.10s (<0.1%)
```

**2. Current Architecture** (Code Analysis Complete)
```
✅ FixedCodeIndexManager exists (lines 64-355) - EXTEND
✅ FixedIncrementalIndexer exists (lines 357-650) - EXTEND
✅ reindex_manager utilities exist (2260 lines) - REUSE
✅ Hooks integration exists - NO CHANGES NEEDED
```

**3. Code Reuse Opportunities** (50-70% Already Built)
```
✅ Lock management - EXISTS in reindex_manager
✅ Cooldown logic - EXISTS in reindex_manager
✅ File filtering - EXISTS in reindex_manager
✅ Session tracking - EXISTS in reindex_manager
✅ Forensic logging - EXISTS in reindex_manager
✅ Timestamp utilities - EXISTS in reindex_manager
```

### Why This Approach (vs POC Plan)

| Aspect | POC Plan | This Plan | Rationale |
|--------|----------|-----------|-----------|
| **Structure** | Separate POC directory | Direct integration | YAGNI - no parallel implementation needed |
| **Code Reuse** | Build 3 new classes | Extend 1 existing class | Don't reinvent existing utilities |
| **Testing** | Tests after implementation | Test-first (TDD) | Catch bugs early, design better APIs |
| **Timeline** | 18-20 days (92 tasks) | 6-8 days (~20 tasks) | Focus on minimal changes |
| **Evidence** | Assumed 180s baseline | Measured 245s baseline | Verify before claiming |
| **Validation** | POC then promote | Direct integration | Simpler deployment path |

---

## Current Architecture

### What EXISTS (Reuse)

**FixedCodeIndexManager** (incremental_reindex.py:64-355)
```python
class FixedCodeIndexManager:
    # HAS:
    - IndexFlatIP (FAISS, sequential IDs)
    - add_embeddings() - adds vectors to FAISS
    - clear_index() - wipes entire index
    - search() - semantic search with k*3 multiplier
    - find_similar() - find similar chunks
    - save_index() - persists to disk

    # Storage:
    - code.index (FAISS IndexFlatIP)
    - metadata.db (SqliteDict)
    - chunk_ids.pkl (ordered list)
    - stats.json (counts)

    # LACKS (what we'll add):
    - ❌ NO embedding cache
    - ❌ NO bloat tracking
    - ❌ NO rebuild from cache
    - ❌ NO incremental operations
```

**FixedIncrementalIndexer** (incremental_reindex.py:357-650)
```python
class FixedIncrementalIndexer:
    # HAS:
    - Merkle change detection
    - auto_reindex() - ALWAYS full reindex (IndexFlatIP limitation)
    - Timestamp tracking

    # LACKS:
    - ❌ NO incremental vector updates
    - ❌ NO cache-based rebuild
```

**reindex_manager.py** (2260 lines - REUSE AS-IS)
```python
# Lock management (_acquire_reindex_lock, _release_reindex_lock)
# Cooldown logic (should_reindex_after_cooldown)
# File filtering (should_reindex_after_write)
# Session tracking (initialize_session_state, mark_first_prompt_shown)
# Forensic logging (log_reindex_start, log_reindex_end)
# Timestamp utilities (get_reindex_timing_analysis)
```

### Integration Points

**Hooks** (No Changes Needed)
```
first-prompt-reindex.py → spawns background reindex
post-tool-use → synchronous reindex after Write
session-start.py → initializes state
stop.py → background reindex if cooldown expired
```

All hooks call `incremental_reindex.py` via bash wrapper. Our changes extend the Python script, hooks remain unchanged.

---

## Phase 1: Benchmarking ✅ **COMPLETE**

### Objective
**Verify hypothesis**: Embedding generation takes 70-80% of full reindex time.

### ✅ Hypothesis VALIDATED (Exceeded Expectations!)

**Original Hypothesis**: Embedding would take 70-80% of time
**Actual Result**: Embedding takes **98.2%** of time

This is even better than expected - embedding is overwhelmingly the bottleneck, making our cache approach even more impactful.

### Actual Benchmark Results

**Execution**: Full reindex with timing instrumentation
**Date**: 2025-12-14
**Project**: Claude-Multi-Agent-Research-System-Skill
**Command**: `scripts/incremental-reindex.py --full`

```
============================================================
PERFORMANCE BREAKDOWN
============================================================
Phase                Time (s)    % Total
------------------------------------------------------------
embedding              241.89      98.2%  ← DOMINANT BOTTLENECK
dag_build                2.75       1.1%
chunking                 0.97       0.4%
index_save               0.42       0.2%
snapshot_save            0.15       0.1%
file_filtering           0.03       0.0%
faiss_add                0.01       0.0%
clear_index              0.00       0.0%
metadata_add             0.00       0.0%
------------------------------------------------------------
TOTAL                  246.24     100.0%
============================================================

Files indexed: 316
Chunks created: 9,992
Device: Apple Silicon (mps:0)
```

### Strategic Implications

**1. Maximum Theoretical Speedup: 56x**
- If we cache 100% of embeddings, we eliminate 241.89s
- Remaining: 4.35s (DAG, chunking, FAISS, I/O)
- Speedup: 246.24s / 4.35s = **56x faster**

**2. Partial Cache Benefits**
- 50% cache hit → 121s saved → 2x faster
- 80% cache hit → 194s saved → 5x faster
- 90% cache hit → 218s saved → 10x faster
- 95% cache hit → 230s saved → 16x faster

**3. All Other Phases Are Negligible**
- DAG building (2.75s) - already optimized with Merkle tree
- Chunking (0.97s) - fast enough, not worth optimizing
- FAISS operations (0.43s total) - not a bottleneck
- I/O (0.57s) - acceptable

**4. Cache Approach Validated**
- ✅ Embedding is the bottleneck (98.2% confirmed)
- ✅ Cache will have massive impact (up to 56x speedup)
- ✅ No need to optimize other phases
- ✅ Proceed with Phase 2 implementation

### Instrumentation Code (Already Added)

The `_full_index()` method in incremental_reindex.py (lines 558-678) now includes:
- Per-phase timing tracking
- Formatted breakdown output
- Timing data in return dict

This instrumentation will remain in production code to help users understand reindex performance.

### Decision: PROCEED WITH CACHE IMPLEMENTATION

**Rationale**:
1. Hypothesis validated (even exceeded - 98.2% vs 70-80%)
2. Maximum speedup potential: 56x
3. Conservative target (8x) is easily achievable
4. No alternative optimization would have comparable impact

---

## Phase 2: Implementation (5-6 days, Test-First)

### Feature 1: Embedding Cache (1.5 days)

**Objective**: Store embeddings separately to enable rebuild without re-embedding.

**Test-First Approach** (RED-GREEN-REFACTOR):

**Test 1: Cache Initialization** (30 min)
```python
def test_cache_initialized_empty():
    """Fresh cache should be empty dict"""
    manager = FixedCodeIndexManager("/tmp/test_project")
    assert manager.embedding_cache == {}
    assert manager.cache_path.name == "embeddings.pkl"
```
- RED: Write test, verify it fails (cache doesn't exist yet)
- GREEN: Add `self.embedding_cache = {}` to `__init__`
- Commit: `"test: Cache initialized empty (RED)"` + `"feat: Initialize embedding cache (GREEN)"`

**Test 2: Cache Saves Single Embedding** (30 min)
```python
def test_cache_saves_single_embedding():
    """Cache should persist single embedding"""
    manager = FixedCodeIndexManager("/tmp/test_project")
    embedding = np.random.rand(768).astype(np.float32)

    manager.embedding_cache['chunk_123'] = embedding
    manager._save_cache()

    assert manager.cache_path.exists()
```
- RED: Write test, verify it fails (`_save_cache` doesn't exist)
- GREEN: Implement `_save_cache()` method
- Commit: `"test: Cache saves embedding (RED)"` + `"feat: Implement cache save (GREEN)"`

**Test 3: Cache Loads After Restart** (45 min)
```python
def test_cache_loads_after_restart():
    """Cache should persist across restarts"""
    manager1 = FixedCodeIndexManager("/tmp/test_project")
    embedding = np.random.rand(768).astype(np.float32)
    manager1.embedding_cache['chunk_123'] = embedding
    manager1._save_cache()

    # Restart
    manager2 = FixedCodeIndexManager("/tmp/test_project")
    assert 'chunk_123' in manager2.embedding_cache
    np.testing.assert_array_equal(manager2.embedding_cache['chunk_123'], embedding)
```
- RED: Write test, verify it fails (`_load_cache` doesn't call properly)
- GREEN: Implement `_load_cache()` in `__init__`
- Commit: `"test: Cache persists (RED)"` + `"feat: Implement cache load (GREEN)"`

**Test 4: Cache Atomic Write** (45 min)
```python
def test_cache_atomic_write():
    """Cache write should be atomic (temp + rename)"""
    manager = FixedCodeIndexManager("/tmp/test_project")
    embedding = np.random.rand(768).astype(np.float32)
    manager.embedding_cache['chunk_123'] = embedding

    # Simulate crash during write by checking temp file exists
    import os
    original_rename = os.rename
    def mock_rename(src, dst):
        assert src.endswith('.pkl.tmp')
        assert dst.endswith('.pkl')
        original_rename(src, dst)

    with patch('os.rename', side_effect=mock_rename):
        manager._save_cache()
```
- RED: Write test, verify atomic write pattern
- GREEN: Modify `_save_cache()` to use temp file + rename
- Commit: `"test: Cache atomic write (RED)"` + `"feat: Atomic cache save (GREEN)"`

**Test 5: Cache Correct Dimensions** (30 min)
```python
def test_cache_stores_correct_dimensions():
    """Cache should store 768-dim numpy arrays"""
    manager = FixedCodeIndexManager("/tmp/test_project")
    embedding = np.random.rand(768).astype(np.float32)
    manager.embedding_cache['chunk_123'] = embedding

    assert manager.embedding_cache['chunk_123'].shape == (768,)
    assert manager.embedding_cache['chunk_123'].dtype == np.float32
```
- RED: Write test for dimension validation
- GREEN: Add dimension check in cache operations
- Commit: `"test: Cache dimension validation (RED)"` + `"feat: Validate cache dimensions (GREEN)"`

**Test 6: Cache Handles Missing File** (30 min)
```python
def test_cache_handles_missing_file():
    """Cache should gracefully handle missing file"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Cache file doesn't exist, should initialize empty
    assert manager.embedding_cache == {}

    # After save and delete, should handle gracefully
    manager.embedding_cache['chunk_123'] = np.random.rand(768).astype(np.float32)
    manager._save_cache()
    manager.cache_path.unlink()

    manager2 = FixedCodeIndexManager("/tmp/test_project")
    assert manager2.embedding_cache == {}
```
- RED: Write test for graceful degradation
- GREEN: Add try/except in `_load_cache()`
- Commit: `"test: Cache missing file handling (RED)"` + `"feat: Graceful cache degradation (GREEN)"`

**Integration: add_embeddings() Caching** (1 hour)
```python
def test_add_embeddings_caches():
    """add_embeddings should automatically cache"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Create mock embedding results
    embedding_results = [
        EmbeddingResult(
            chunk_id='chunk_1',
            embedding=np.random.rand(768).astype(np.float32),
            metadata={'file_path': 'test.py'}
        )
    ]

    manager.add_embeddings(embedding_results)

    # Should be in cache
    assert 'chunk_1' in manager.embedding_cache
```

**Implementation** (modify existing `add_embeddings`):
```python
def add_embeddings(self, embedding_results):
    """Add embeddings to index - MODIFIED to cache"""
    if not embedding_results:
        return

    vectors = []
    chunk_ids_to_add = []
    start_index = self.index.ntotal

    for result in embedding_results:
        chunk_id = result.chunk_id
        vectors.append(result.embedding)
        chunk_ids_to_add.append(chunk_id)

        # NEW: Cache embedding
        self.embedding_cache[chunk_id] = result.embedding  # ← ADD THIS

        # Store metadata with sequential index
        self.metadata_db[chunk_id] = {
            'metadata': result.metadata,
            'chunk_id': chunk_id,
            'faiss_id': start_index + len(chunk_ids_to_add) - 1
        }

    # Add to FAISS
    vectors_array = np.array(vectors, dtype=np.float32)
    faiss.normalize_L2(vectors_array)
    self.index.add(vectors_array)
    self.chunk_ids.extend(chunk_ids_to_add)

    # NEW: Save cache after adding
    self._save_cache()  # ← ADD THIS
```

**Total Feature 1**: 6 tests × 30-45min + 1hr integration = 8 hours (1 day) + 4hr buffer = **1.5 days**

---

### Feature 2: Bloat Tracking (1 day)

**Objective**: Monitor index bloat from lazy deletion and trigger rebuild at thresholds.

**Test-First Approach**:

**Test 1: Bloat Zero Initially** (20 min)
```python
def test_bloat_zero_initially():
    """Fresh index should have 0% bloat"""
    manager = FixedCodeIndexManager("/tmp/test_project")
    bloat = manager._calculate_bloat()

    assert bloat['total_vectors'] == 0
    assert bloat['active_chunks'] == 0
    assert bloat['stale_vectors'] == 0
    assert bloat['bloat_percentage'] == 0.0
```
- RED: Write test, verify it fails (`_calculate_bloat` doesn't exist)
- GREEN: Implement `_calculate_bloat()` method
- Commit: `"test: Bloat calculation (RED)"` + `"feat: Calculate bloat metrics (GREEN)"`

**Test 2: Bloat Increases After Delete** (30 min)
```python
def test_bloat_increases_after_lazy_delete():
    """Lazy delete should increase bloat"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])

    # Delete 20 chunks from metadata (lazy delete)
    for i in range(20):
        del manager.metadata_db[f'chunk_{i}']

    bloat = manager._calculate_bloat()
    assert bloat['total_vectors'] == 100  # FAISS still has all
    assert bloat['active_chunks'] == 80   # Metadata has 80
    assert bloat['stale_vectors'] == 20
    assert bloat['bloat_percentage'] == 20.0
```
- RED: Write test for lazy deletion bloat
- GREEN: Ensure `_calculate_bloat()` correctly computes stale vectors
- Commit: `"test: Bloat from lazy delete (RED)"` + `"feat: Lazy delete bloat tracking (GREEN)"`

**Test 3: Rebuild Trigger Hybrid Logic** (45 min)
```python
def test_rebuild_trigger_hybrid():
    """Rebuild triggers: (20% + 500 stale) OR (30%)"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Scenario 1: 20% bloat but only 100 stale → NO rebuild
    # (simulate 500 total, 400 active, 100 stale = 20%)
    assert not manager._needs_rebuild_for(total=500, active=400)

    # Scenario 2: 20% bloat AND 500 stale → YES rebuild
    # (simulate 2500 total, 2000 active, 500 stale = 20%)
    assert manager._needs_rebuild_for(total=2500, active=2000)

    # Scenario 3: 30% bloat but only 200 stale → YES rebuild (fallback)
    # (simulate 666 total, 466 active, 200 stale = 30%)
    assert manager._needs_rebuild_for(total=666, active=466)
```
- RED: Write test for hybrid trigger logic
- GREEN: Implement `_needs_rebuild()` method
- Commit: `"test: Hybrid rebuild trigger (RED)"` + `"feat: Implement rebuild trigger (GREEN)"`

**Test 4: Small Project 30% Trigger** (30 min)
```python
def test_small_project_rebuild_trigger():
    """Small projects (<1667 vectors) use 30% fallback"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Small project: 1000 total, 700 active, 300 stale = 30% bloat
    # Should trigger despite stale_count < 500
    assert manager._needs_rebuild_for(total=1000, active=700)

    # Verify 30% is the threshold
    assert not manager._needs_rebuild_for(total=1000, active=710)  # 29% → NO
    assert manager._needs_rebuild_for(total=1000, active=700)      # 30% → YES
```
- RED: Write test for small project edge case
- GREEN: Ensure `_needs_rebuild()` has OR condition for 30%
- Commit: `"test: Small project trigger (RED)"` + `"feat: 30% fallback trigger (GREEN)"`

**Test 5: Rebuild Resets Bloat** (30 min)
```python
def test_rebuild_resets_bloat():
    """After rebuild, bloat should be 0%"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks, delete 20 (20% bloat)
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])
    for i in range(20):
        del manager.metadata_db[f'chunk_{i}']

    bloat_before = manager._calculate_bloat()
    assert bloat_before['bloat_percentage'] == 20.0

    # Rebuild from cache
    manager.rebuild_from_cache()

    bloat_after = manager._calculate_bloat()
    assert bloat_after['bloat_percentage'] == 0.0
    assert bloat_after['total_vectors'] == 80  # Only active chunks
```
- RED: Write test for rebuild resetting bloat
- GREEN: Ensure `rebuild_from_cache()` creates clean index
- Commit: `"test: Rebuild resets bloat (RED)"` + `"feat: Clean rebuild (GREEN)"`

**Test 6: Stats.json Bloat Metrics** (30 min)
```python
def test_stats_json_includes_bloat():
    """stats.json should include bloat metrics"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add chunks and create bloat
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])
    for i in range(20):
        del manager.metadata_db[f'chunk_{i}']

    manager.save_index()  # Triggers _update_stats()

    stats_path = manager.index_dir / "stats.json"
    with open(stats_path) as f:
        stats = json.load(f)

    assert 'bloat_percentage' in stats
    assert stats['bloat_percentage'] == 20.0
    assert 'stale_vectors' in stats
    assert stats['stale_vectors'] == 20
```
- RED: Write test for bloat in stats
- GREEN: Modify `_update_stats()` to include bloat metrics
- Commit: `"test: Stats bloat metrics (RED)"` + `"feat: Add bloat to stats.json (GREEN)"`

**Total Feature 2**: 6 tests × 20-45min = 6 hours (0.75 day) + 2hr buffer = **1 day**

---

### Feature 3: Rebuild from Cache (2 days)

**Objective**: Rebuild index from cached embeddings without re-embedding (4x speedup).

**Test-First Approach**:

**Test 1: Rebuild Uses Cache Not Embedder** (1 hour)
```python
def test_rebuild_uses_cache_not_embedder():
    """Rebuild should use cache, never call embedder"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks (caches embeddings)
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])

    # Mock embedder to verify it's not called
    with patch.object(manager, 'embedder') as mock_embedder:
        manager.rebuild_from_cache()
        mock_embedder.embed_chunks.assert_not_called()
```
- RED: Write test, verify it fails (rebuild doesn't exist)
- GREEN: Implement `rebuild_from_cache()` using only cache
- Commit: `"test: Rebuild uses cache (RED)"` + `"feat: Cache-based rebuild (GREEN)"`

**Test 2: Rebuild Completeness Check** (1 hour)
```python
def test_rebuild_completeness_check():
    """Rebuild should fail if cache incomplete"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])

    # Delete 10 embeddings from cache (simulate incomplete cache)
    for i in range(10):
        del manager.embedding_cache[f'chunk_{i}']

    # Rebuild should raise CacheIncompleteError
    with pytest.raises(CacheIncompleteError) as exc_info:
        manager.rebuild_from_cache()

    assert "Cache incomplete" in str(exc_info.value)
    assert "90/100" in str(exc_info.value)  # 90 cached, 100 in metadata
    assert "--full" in str(exc_info.value)  # Suggests fix
```
- RED: Write test for cache validation
- GREEN: Add completeness check to `rebuild_from_cache()`
- Commit: `"test: Rebuild completeness (RED)"` + `"feat: Cache validation (GREEN)"`

**Test 3: Rebuild Produces Clean Index** (1.5 hours)
```python
def test_rebuild_produces_clean_index():
    """Rebuild should create index with no bloat"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks, delete 20 (20% bloat)
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])
    for i in range(20):
        del manager.metadata_db[f'chunk_{i}']
        del manager.embedding_cache[f'chunk_{i}']

    bloat_before = manager._calculate_bloat()
    assert bloat_before['bloat_percentage'] == 20.0
    assert bloat_before['total_vectors'] == 100  # FAISS still has all

    # Rebuild
    manager.rebuild_from_cache()

    bloat_after = manager._calculate_bloat()
    assert bloat_after['bloat_percentage'] == 0.0
    assert bloat_after['total_vectors'] == 80  # FAISS cleaned up
    assert bloat_after['active_chunks'] == 80
    assert manager.index.ntotal == 80  # FAISS matches metadata
```
- RED: Write test for clean rebuild
- GREEN: Ensure `rebuild_from_cache()` builds fresh index
- Commit: `"test: Rebuild clean index (RED)"` + `"feat: Clean index rebuild (GREEN)"`

**Test 4: Rebuild Preserves Search Quality** (1.5 hours)
```python
def test_rebuild_preserves_search_quality():
    """Rebuild should not affect search results"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks with known content
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(
            f'chunk_{i}',
            content=f'function test_{i}() {{ return {i}; }}'
        )])

    # Search before rebuild
    query = np.random.rand(768).astype(np.float32)
    results_before = manager.search(query, k=5)

    # Create bloat and rebuild
    for i in range(20):
        del manager.metadata_db[f'chunk_{i}']
        del manager.embedding_cache[f'chunk_{i}']
    manager.rebuild_from_cache()

    # Search after rebuild (same query)
    results_after = manager.search(query, k=5)

    # Top-5 should be same (excluding deleted chunks)
    chunk_ids_before = [r[0] for r in results_before if not r[0].startswith('chunk_0')][:5]
    chunk_ids_after = [r[0] for r in results_after][:5]
    assert chunk_ids_before == chunk_ids_after
```
- RED: Write test for search quality preservation
- GREEN: Verify `rebuild_from_cache()` maintains vector ordering
- Commit: `"test: Rebuild preserves search (RED)"` + `"feat: Quality preservation (GREEN)"`

**Test 5: Rebuild Faster Than Full** (1 hour)
```python
def test_rebuild_faster_than_full():
    """Rebuild from cache should be faster than full reindex"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 1000 chunks (representative size)
    for i in range(1000):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])

    # Time full reindex
    manager.clear_index()
    start_full = time.time()
    # ... full reindex logic ...
    time_full = time.time() - start_full

    # Time rebuild from cache
    start_rebuild = time.time()
    manager.rebuild_from_cache()
    time_rebuild = time.time() - start_rebuild

    # Rebuild should be at least 3x faster (no embedding)
    assert time_rebuild < time_full / 3
```
- RED: Write performance test
- GREEN: Verify rebuild is actually faster (benchmark)
- Commit: `"test: Rebuild performance (RED)"` + `"feat: Optimized rebuild (GREEN)"`

**Total Feature 3**: 5 tests × 1-1.5hr = 10.5 hours (1.3 days) + 5.5hr buffer = **2 days**

---

### Feature 4: Incremental Operations (1 day)

**Objective**: Support incremental add/edit/delete without full reindex.

**Test-First Approach**:

**Test 1: Incremental Delete** (1 hour)
```python
def test_incremental_delete():
    """Delete should remove from metadata + cache, leave FAISS unchanged"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 3 files with chunks
    manager.add_embeddings([create_mock_embedding('file1_chunk1', file_path='file1.py')])
    manager.add_embeddings([create_mock_embedding('file2_chunk1', file_path='file2.py')])
    manager.add_embeddings([create_mock_embedding('file3_chunk1', file_path='file3.py')])

    initial_faiss_count = manager.index.ntotal
    initial_metadata_count = len(manager.metadata_db)

    # Delete file2
    deleted_count = manager.incremental_delete(['file2.py'])

    # FAISS unchanged (lazy delete)
    assert manager.index.ntotal == initial_faiss_count

    # Metadata and cache updated
    assert len(manager.metadata_db) == initial_metadata_count - 1
    assert 'file2_chunk1' not in manager.metadata_db
    assert 'file2_chunk1' not in manager.embedding_cache

    # Bloat increased
    bloat = manager._calculate_bloat()
    assert bloat['stale_vectors'] == 1
    assert bloat['bloat_percentage'] > 0
```
- RED: Write test, verify it fails (`incremental_delete` doesn't exist)
- GREEN: Implement `incremental_delete()` method
- Commit: `"test: Incremental delete (RED)"` + `"feat: Lazy deletion (GREEN)"`

**Test 2: Incremental Edit** (1 hour)
```python
def test_incremental_edit():
    """Edit should delete old + add new"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add initial version
    manager.add_embeddings([create_mock_embedding(
        'file1_chunk1',
        file_path='file1.py',
        content='def old_function(): pass'
    )])

    initial_faiss_count = manager.index.ntotal

    # Edit file (new content)
    new_embedding = create_mock_embedding(
        'file1_chunk1_v2',
        file_path='file1.py',
        content='def new_function(): return 42'
    )
    manager.incremental_edit(['file1.py'], [new_embedding])

    # Old version removed from metadata
    assert 'file1_chunk1' not in manager.metadata_db

    # New version added
    assert 'file1_chunk1_v2' in manager.metadata_db
    assert 'file1_chunk1_v2' in manager.embedding_cache

    # FAISS has both (bloat increased by 1)
    assert manager.index.ntotal == initial_faiss_count + 1
```
- RED: Write test for edit operation
- GREEN: Implement `incremental_edit()` = delete + add
- Commit: `"test: Incremental edit (RED)"` + `"feat: Edit operation (GREEN)"`

**Test 3: Lazy Deletion Increases Bloat** (30 min)
```python
def test_lazy_deletion_increases_bloat():
    """Multiple edits should accumulate bloat"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 10 files
    for i in range(10):
        manager.add_embeddings([create_mock_embedding(f'file{i}_chunk', file_path=f'file{i}.py')])

    # Edit 5 files repeatedly (3 times each = 15 stale versions)
    for edit_round in range(3):
        for i in range(5):
            new_embedding = create_mock_embedding(
                f'file{i}_chunk_v{edit_round+1}',
                file_path=f'file{i}.py'
            )
            manager.incremental_edit([f'file{i}.py'], [new_embedding])

    bloat = manager._calculate_bloat()
    assert bloat['stale_vectors'] == 15  # 5 files × 3 old versions
    assert bloat['total_vectors'] == 25  # 10 initial + 15 new versions
    assert bloat['active_chunks'] == 10  # Only current versions
```
- RED: Write test for bloat accumulation
- GREEN: Verify delete + edit correctly update bloat
- Commit: `"test: Bloat accumulation (RED)"` + `"feat: Bloat tracking integration (GREEN)"`

**Test 4: Auto-Rebuild After Threshold** (1 hour)
```python
def test_auto_rebuild_after_threshold():
    """Should auto-rebuild when bloat exceeds threshold"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])

    # Edit 30 files (30% bloat)
    for i in range(30):
        new_embedding = create_mock_embedding(f'chunk_{i}_v2')
        manager.incremental_edit([f'file_{i}.py'], [new_embedding])

    bloat_before = manager._calculate_bloat()
    assert bloat_before['bloat_percentage'] >= 30

    # Next edit should trigger rebuild
    with patch.object(manager, 'rebuild_from_cache') as mock_rebuild:
        manager.incremental_edit([f'file_99.py'], [create_mock_embedding('chunk_99_v2')])
        mock_rebuild.assert_called_once()
```
- RED: Write test for auto-rebuild
- GREEN: Add rebuild check to `incremental_edit()` and `incremental_delete()`
- Commit: `"test: Auto-rebuild trigger (RED)"` + `"feat: Automatic rebuild (GREEN)"`

**Total Feature 4**: 4 tests × 30min-1hr = 6 hours (0.75 day) + 2hr buffer = **1 day**

---

### Feature 5: Search Optimization (0.5 days)

**Objective**: Compensate for bloat using dynamic k-multiplier and adaptive retry.

**Test-First Approach**:

**Test 1: K-Multiplier Uses Ceil** (30 min)
```python
def test_k_multiplier_uses_ceil():
    """K-multiplier should use math.ceil() not int()"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Add 100 chunks, delete 1 (1% bloat)
    for i in range(100):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])
    del manager.metadata_db['chunk_0']

    # Mock search to capture k used
    with patch.object(manager.index, 'search') as mock_search:
        mock_search.return_value = (np.array([[0.9]]), np.array([[1]]))
        manager.search(np.random.rand(768), k=5)

        # At 1% bloat: ceil(5 * 1.01) = 6 (not 5 from int())
        called_k = mock_search.call_args[0][1]
        assert called_k == 6
```
- RED: Write test for ceil() rounding
- GREEN: Modify `search()` to use `math.ceil()`
- Commit: `"test: K-multiplier ceil (RED)"` + `"feat: Ceil rounding (GREEN)"`

**Test 2: Dynamic K-Multiplier** (30 min)
```python
def test_dynamic_k_multiplier():
    """K-multiplier should adapt to bloat percentage"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Test at different bloat levels
    test_cases = [
        (0, 5, 5),    # 0% bloat → k=5
        (1, 5, 6),    # 1% bloat → ceil(5*1.01)=6
        (10, 5, 6),   # 10% bloat → ceil(5*1.10)=6
        (20, 5, 6),   # 20% bloat → ceil(5*1.20)=6
        (50, 5, 8),   # 50% bloat → ceil(5*1.50)=8
        (100, 5, 10), # 100% bloat → ceil(5*2.00)=10
        (200, 5, 15), # 200% bloat → ceil(5*3.00)=15 (capped at 3x)
    ]

    for bloat_pct, k, expected_search_k in test_cases:
        # ... simulate bloat_pct ...
        with patch.object(manager, '_calculate_bloat') as mock_bloat:
            mock_bloat.return_value = {'bloat_percentage': bloat_pct}
            # ... verify search_k == expected_search_k ...
```
- RED: Write test for dynamic multiplier
- GREEN: Implement dynamic k calculation in `search()`
- Commit: `"test: Dynamic k-multiplier (RED)"` + `"feat: Adaptive k (GREEN)"`

**Test 3: Clustered Bloat Adaptive Retry** (1 hour)
```python
def test_clustered_bloat_adaptive_retry():
    """Should retry with higher k if results insufficient"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Create clustered bloat scenario
    # Add 1 file, edit 10 times (creates 10 similar stale vectors)
    manager.add_embeddings([create_mock_embedding('file_v0', content='def auth(): pass')])
    for v in range(1, 11):
        manager.incremental_edit(['auth.py'], [
            create_mock_embedding(f'file_v{v}', content=f'def auth_v{v}(): pass')
        ])

    # 10% bloat, but vectors clustered in embedding space
    # Search should retry with higher k if initial search returns <k valid results
    query = np.random.rand(768)
    results = manager.search(query, k=5)

    # Should still return k=5 results despite clustering
    assert len(results) == 5

    # Verify retry was triggered (mock and check)
    with patch.object(manager.index, 'search') as mock_search:
        # First call returns 3 valid (clustered)
        # Second call (retry) returns 5 valid
        mock_search.side_effect = [
            (np.array([[0.9, 0.8, 0.7]]), np.array([[1, 2, 3]])),  # First: 3 results
            (np.array([[0.9, 0.8, 0.7, 0.6, 0.5]]), np.array([[1, 2, 3, 4, 5]]))  # Retry: 5 results
        ]
        results = manager.search(query, k=5)
        assert mock_search.call_count == 2  # Retry triggered
```
- RED: Write test for adaptive retry
- GREEN: Add retry logic to `search()` when len(valid_results) < k
- Commit: `"test: Adaptive retry (RED)"` + `"feat: Clustered bloat handling (GREEN)"`

**Total Feature 5**: 3 tests × 30min-1hr = 4 hours (0.5 day)

---

**Total Phase 2**: 1.5 + 1 + 2 + 1 + 0.5 = **6 days**

---

## Phase 3: Validation (1 day)

### End-to-End Testing (3 hours)

**Test: Complete Edit Workflow**
```python
def test_complete_edit_workflow():
    """Test full workflow: index → edit → search → rebuild"""
    manager = FixedCodeIndexManager("/tmp/test_project")

    # Step 1: Initial index
    for i in range(50):
        manager.add_embeddings([create_mock_embedding(f'chunk_{i}')])

    # Step 2: Edit 10 files
    for i in range(10):
        manager.incremental_edit([f'file_{i}.py'], [
            create_mock_embedding(f'chunk_{i}_v2')
        ])

    # Step 3: Search still works
    query = np.random.rand(768)
    results = manager.search(query, k=5)
    assert len(results) == 5

    # Step 4: Bloat tracked correctly
    bloat = manager._calculate_bloat()
    assert bloat['stale_vectors'] == 10

    # Step 5: Rebuild from cache
    manager.rebuild_from_cache()
    bloat_after = manager._calculate_bloat()
    assert bloat_after['bloat_percentage'] == 0

    # Step 6: Search still works after rebuild
    results_after = manager.search(query, k=5)
    assert len(results_after) == 5
```

**Test: Cross-Session Persistence**
```python
def test_cross_session_persistence():
    """Cache should persist across Python sessions"""
    project_path = "/tmp/test_project"

    # Session 1: Create index with cache
    manager1 = FixedCodeIndexManager(project_path)
    for i in range(20):
        manager1.add_embeddings([create_mock_embedding(f'chunk_{i}')])
    manager1.save_index()

    # Session 2: Load and verify cache loaded
    manager2 = FixedCodeIndexManager(project_path)
    assert len(manager2.embedding_cache) == 20
    assert manager2.index.ntotal == 20

    # Session 2: Rebuild from cache (no re-embedding)
    manager2.rebuild_from_cache()
    assert manager2.index.ntotal == 20
```

### Performance Benchmarking (2 hours)

**Benchmark 1: Single File Edit**
```bash
# Baseline: Full reindex
time python incremental_reindex.py /path/to/project --full
# Measured: 246.24s (98.2% embedding)

# After implementation: Single file edit
echo "# Modified" >> file.py
time python incremental_reindex.py /path/to/project
# Conservative Target: <10s (25x speedup)
# Stretch Goal: <5s (50x speedup)
```

**Benchmark 2: 10 File Edits**
```bash
# Modify 10 files
for i in {1..10}; do
    echo "# Modified $i" >> file_$i.py
done

time python incremental_reindex.py /path/to/project
# Conservative Target: <50s (5x speedup vs 246s baseline)
# Stretch Goal: <30s (8x speedup)
```

**Benchmark 3: Rebuild from Cache**
```bash
# Create 30% bloat (triggers rebuild)
# ... edit 30% of files ...

time python incremental_reindex.py /path/to/project
# Conservative Target: <30s (8x speedup vs 246s baseline)
# Stretch Goal: <15s (16x speedup, rebuild from cache, no re-embedding)
```

### Documentation (2 hours)

**Update Files**:
1. `SKILL.md` - Document cache feature
2. `incremental_reindex.py` - Update docstrings
3. `README.md` - Add cache usage notes
4. This plan - Update with actual benchmark results

**Total Phase 3**: 3 + 2 + 2 = **7 hours (1 day)**

---

## Success Criteria

### Performance (Measured, Evidence-Based)

**Benchmark-Validated Baseline**: 246.24s (98.2% embedding, 1.8% other)

**Conservative Targets** (Must Achieve):
- ✅ Single file edit: <10s (vs 246s baseline) - **25x speedup**
- ✅ 10 file edits: <50s (vs 246s baseline) - **5x speedup**
- ✅ Rebuild from cache: <30s (vs 246s full reindex) - **8x speedup**

**Stretch Goals** (If Everything Goes Well):
- 🎯 Single file edit: <5s - **50x speedup** (approaching theoretical max)
- 🎯 10 file edits: <30s - **8x speedup**
- 🎯 Rebuild from cache: <15s - **16x speedup**

**Why These Targets Are Achievable**:
- Embedding takes 241.89s (98.2%) - this is what we're caching
- Remaining operations: 4.35s (DAG, chunking, FAISS, I/O)
- Even with cache lookup overhead, we should hit conservative targets easily
- Theoretical maximum: 56x (eliminating all embedding time)

**If Not Achieved**:
- Document actual speedup achieved
- Analyze why targets not met (profiling, bottleneck analysis)
- Decide: Adjust targets OR optimize further OR accept current performance
- **Minimum acceptable**: 2x speedup (otherwise not worth complexity)

### Correctness (Tested, Not Hoped)

**Must Pass**:
- ✅ All 20+ tests pass (100% success rate)
- ✅ Search top-5 results match full index (100% accuracy)
- ✅ Bloat calculation accurate (verified by tests)
- ✅ No crashes on Apple Silicon (all tests pass on mps:0)
- ✅ Cache completeness check prevents corruption
- ✅ Atomic writes prevent cache corruption

### Integration (Verified, Not Assumed)

**Must Work**:
- ✅ Hooks still work (no breaking changes)
- ✅ Existing tests still pass (backward compatible)
- ✅ Manual verification: Edit file → index updates → search works
- ✅ Cross-session persistence works (cache loads after restart)

### Code Quality (Enforced, Not Suggested)

**Must Have**:
- ✅ All tests written BEFORE implementation (true TDD)
- ✅ Code coverage >80% for new code
- ✅ No duplication of existing utilities (reused reindex_manager)
- ✅ Clean git history (atomic commits, meaningful messages)
- ✅ Code passes existing linting/formatting standards

### Go/No-Go Decision

**GO if**:
- All performance targets met OR documented reasons for variance
- All tests pass
- Hooks integration works
- No regressions

**NO-GO if**:
- Performance improvement <2x (not worth complexity)
- Tests fail and can't be fixed quickly
- Hooks break user workflow
- Major regressions discovered

**If NO-GO**:
- Git revert all changes
- Document findings (what worked, what didn't)
- Keep plan for future iteration
- Accept current full reindex approach

---

## Risk Management

### Risk 1: Benchmarking Reveals Embedding is NOT the Bottleneck ✅ **RESOLVED**

**Status**: ✅ **MITIGATED** - Benchmark completed, hypothesis VALIDATED

**Actual Result**:
- Embedding confirmed as bottleneck: **98.2%** of total time
- This exceeded our hypothesis (70-80%)
- Cache approach validated with 56x theoretical maximum speedup

**Conclusion**: No longer a risk. Proceeding with Phase 2 implementation.

---

### Risk 2: Bloat Accumulates Faster Than Expected

**Probability**: Medium (depends on user edit patterns)

**Impact**: Medium (more frequent rebuilds, less speedup)

**Mitigation**:
- Monitor bloat in tests
- Test with realistic edit patterns (10 files, 20 files, 50 files)
- Adjust rebuild thresholds based on data

**Response**:
- If bloat >30% frequently: Lower threshold to 15% + 300 stale
- If rebuild too frequent: Increase threshold to 25% + 750 stale
- Document recommended thresholds based on project size

**Fallback**:
- Allow user to configure thresholds via config
- Document bloat patterns for different workflows

---

### Risk 3: Cache Gets Corrupted

**Probability**: Low (atomic writes protect against most corruption)

**Impact**: Medium (need to detect and recover)

**Mitigation**:
- Use atomic writes (temp + rename)
- Add validation on load (dimension check, completeness check)
- Test corruption scenarios (power loss, disk full)

**Response**:
- If corruption detected: Auto-fallback to full reindex
- Log warning with clear error message
- Suggest running with --full to recreate cache

**Fallback**:
- Delete cache file
- Run full reindex to start fresh
- Cache will be rebuilt automatically

---

### Risk 4: Performance Improvement Less Than 3x

**Probability**: Medium (depends on actual bottleneck distribution)

**Impact**: Medium (doesn't meet target, but may still be useful)

**Mitigation**:
- Benchmark early (Phase 1)
- Measure often (after each feature)
- Profile if performance doesn't match expectations

**Response**:
- If 2-3x speedup: Still useful, document actual improvement
- If <2x speedup: Analyze why, optimize further or No-Go
- If >4x speedup: Great! Document and celebrate

**Fallback**:
- Accept actual speedup if >2x (still meaningful)
- Document findings for future optimization
- Consider different approach if <2x

---

### Risk 5: Integration Breaks Hooks

**Probability**: Low (extending not replacing, hooks call same script)

**Impact**: High (breaks user workflow)

**Mitigation**:
- Test hooks after each major change
- Keep integration points minimal
- Don't change script CLI interface

**Response**:
- Fix immediately if hook breaks
- Rollback if can't fix quickly
- Test on real project before merging

**Fallback**:
- Git revert to previous working state
- Hooks should keep working with old code
- No user impact from rollback

---

## Integration Strategy

### Feature Branch

```bash
# Create sub-branch from current feature
git checkout feature/searching-code-semantically-skill
git checkout -b feature/semantic-search-incremental-cache

# Work on this branch for 6-8 days
# Merge back to parent when complete
```

### Test-First Commits (RED-GREEN-REFACTOR)

**Example Commit Sequence**:
```bash
# Feature 1: Embedding Cache
git commit -m "test: Add test for cache initialization (RED)"
git commit -m "feat: Initialize embedding cache in __init__ (GREEN)"
git commit -m "test: Add test for cache persistence (RED)"
git commit -m "feat: Implement cache save/load with atomic writes (GREEN)"
git commit -m "refactor: Extract cache validation to separate method"

# Feature 2: Bloat Tracking
git commit -m "test: Add test for bloat calculation (RED)"
git commit -m "feat: Implement bloat calculation method (GREEN)"
git commit -m "test: Add test for rebuild trigger logic (RED)"
git commit -m "feat: Implement hybrid rebuild trigger (20% + 500) OR (30%) (GREEN)"

# ... etc for all features
```

### Phase Tags

```bash
# After Feature 1 + 2 complete (cache + bloat)
git tag v1.0.0-cache-alpha
git tag -a v1.0.0-cache-alpha -m "Alpha: Cache + bloat tracking working"

# After Feature 3 complete (rebuild from cache)
git tag v1.0.0-cache-beta
git tag -a v1.0.0-cache-beta -m "Beta: Rebuild from cache working"

# After Feature 4 + 5 complete (incremental ops + search)
git tag v1.0.0-cache-rc
git tag -a v1.0.0-cache-rc -m "RC: All features complete, ready for validation"

# After Phase 3 validation passes
git tag v1.0.0-cache
git tag -a v1.0.0-cache -m "Release: Incremental cache validated, ready for merge"
```

### Merge Strategy

```bash
# After validation passes
git checkout feature/searching-code-semantically-skill
git merge --no-ff feature/semantic-search-incremental-cache -m "feat: Add incremental cache for 4x speedup

Merge feature/semantic-search-incremental-cache

Features:
- Embedding cache (prevents re-embedding unchanged files)
- Bloat tracking (monitors index bloat from lazy deletion)
- Rebuild from cache (4x faster than full reindex)
- Incremental operations (add/edit/delete without full reindex)
- Search optimization (dynamic k-multiplier + adaptive retry)

Performance:
- Single file edit: <15s (vs 245s baseline) - 16x speedup
- 10 file edits: <60s (vs 245s baseline) - 4x speedup
- Rebuild from cache: <60s (vs 245s full) - 4x speedup

Testing:
- 20+ tests (all passing)
- 100% backward compatible
- No hook changes needed

Closes #XXX"

# Delete feature branch after merge
git branch -d feature/semantic-search-incremental-cache
```

### Rollback Plan

**If validation fails**:
```bash
# Immediate rollback
git checkout feature/searching-code-semantically-skill
git reset --hard HEAD~1  # Undo merge

# Or revert merge commit
git revert -m 1 <merge-commit-hash>

# Feature branch still exists for future work
git checkout feature/semantic-search-incremental-cache
# Analyze what went wrong, fix, try again
```

**If production issues found later**:
```bash
# Hooks keep working (they call same script)
# Users can use --full to bypass cache
# Cache file can be deleted to force full reindex

# Emergency rollback
git revert <merge-commit-hash>
git push origin feature/searching-code-semantically-skill
```

---

## Comparison: This Plan vs POC Plan

| Metric | POC Plan | This Plan | Improvement |
|--------|----------|-----------|-------------|
| **Timeline** | 18-20 days | 6-8 days | **3x faster** |
| **Tasks** | 92 tasks | ~20 tasks | **4x fewer** |
| **Documentation** | 230KB (9 docs) | ~15KB (1 doc) | **95% less** |
| **New Classes** | 3 standalone | Extend 1 existing | **Simpler** |
| **Code Reuse** | 30-50% | 50-70% | **More reuse** |
| **Testing** | Tests after | Test-first (TDD) | **Better quality** |
| **Evidence** | Assumed 180s | Measured 245s | **Verified** |
| **Integration** | POC then promote | Direct integration | **Simpler path** |
| **Rollback** | Delete POC dir | Git revert | **Safer** |

---

## Next Steps

1. ✅ **Phase 1: Benchmarking** - COMPLETE
   - ✅ Added timing instrumentation to _full_index()
   - ✅ Ran benchmark (246.24s total, 98.2% embedding)
   - ✅ Hypothesis validated (exceeded expectations)
   - ✅ Updated plan with actual results

2. **User Approval** - Get approval to proceed with Phase 2 implementation
   - Review benchmark findings (98.2% embedding bottleneck)
   - Confirm conservative targets (25x, 5x, 8x speedups)
   - Approve test-first implementation approach

3. **Phase 2: Implementation** (5-6 days) - READY TO START
   - Feature 1: Embedding Cache (1.5 days)
   - Feature 2: Bloat Tracking (1 day)
   - Feature 3: Rebuild from Cache (2 days)
   - Feature 4: Incremental Operations (1 day)
   - Feature 5: Search Optimization (0.5 days)
   - Test-first for each feature (RED-GREEN-REFACTOR)
   - Atomic commits, phase tags (alpha, beta, rc)

4. **Phase 3: Validation** (1 day)
   - End-to-end testing
   - Performance benchmarking against targets
   - Go/No-Go decision

---

## Appendix: File Changes Summary

### Files to Modify

**incremental_reindex.py** (extend existing):
- `FixedCodeIndexManager.__init__()` - Add cache initialization
- `FixedCodeIndexManager._load_cache()` - NEW method
- `FixedCodeIndexManager._save_cache()` - NEW method
- `FixedCodeIndexManager.add_embeddings()` - Add cache save call
- `FixedCodeIndexManager._calculate_bloat()` - NEW method
- `FixedCodeIndexManager._needs_rebuild()` - NEW method
- `FixedCodeIndexManager.rebuild_from_cache()` - NEW method
- `FixedCodeIndexManager.incremental_delete()` - NEW method
- `FixedCodeIndexManager.incremental_edit()` - NEW method
- `FixedCodeIndexManager.search()` - Modify for dynamic k-multiplier
- `FixedCodeIndexManager._update_stats()` - Add bloat metrics
- `FixedCodeIndexManager._full_index()` - Add timing instrumentation

**Total Changes**: ~400-500 lines added/modified in 1 file

### Files to Create

**tests/test_incremental_cache.py** - NEW
- 20+ tests for cache, bloat, rebuild, incremental ops, search

### Files Unchanged (Reused)

**reindex_manager.py** - NO CHANGES
**Hooks** - NO CHANGES
**Agents** - NO CHANGES
**Existing tests** - NO CHANGES (should still pass)

---

**Status**: ✅ Phase 1 Complete - Ready for Phase 2 (Implementation)
**Phase 1 Result**: Hypothesis VALIDATED - Embedding takes 98.2% of time (exceeded 70-80% prediction)
**Theoretical Maximum Speedup**: 56x (if 100% cache hit)
**Conservative Targets**: 25x (single edit), 5x (10 edits), 8x (rebuild)
**Next**: Get user approval to proceed with Phase 2 implementation
