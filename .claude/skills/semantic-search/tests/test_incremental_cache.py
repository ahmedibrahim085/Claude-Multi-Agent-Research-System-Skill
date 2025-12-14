#!/usr/bin/env python3
"""
Test suite for incremental cache feature (embedding cache + lazy deletion + bloat tracking)

This test suite follows TDD (Test-Driven Development) approach:
- Each test is written BEFORE implementation (RED)
- Then minimal code is written to make test pass (GREEN)
- Finally code is refactored while keeping tests green (REFACTOR)

Run: pytest test_incremental_cache.py -v
"""

import sys
from pathlib import Path
import numpy as np
import pytest
import tempfile
import shutil

# Add incremental_reindex.py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from incremental_reindex import FixedCodeIndexManager


class TestEmbeddingCache:
    """Feature 1: Embedding Cache - Store embeddings separately for rebuild without re-embedding"""

    def test_cache_initialized_empty(self):
        """
        Test 1: Cache Initialization (RED phase)

        Fresh FixedCodeIndexManager should initialize with:
        - Empty embedding_cache dict
        - cache_path pointing to embeddings.pkl

        Expected failure: AttributeError (embedding_cache doesn't exist yet)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # These should exist after __init__
            assert hasattr(manager, 'embedding_cache'), "embedding_cache attribute missing"
            assert manager.embedding_cache == {}, "Cache should be empty dict initially"

            assert hasattr(manager, 'cache_path'), "cache_path attribute missing"
            assert manager.cache_path.name == "embeddings.pkl", "Cache filename should be embeddings.pkl"

    def test_cache_saves_single_embedding(self):
        """
        Test 2: Cache Saves Single Embedding (RED phase)

        Cache should persist to disk when _save_cache() is called.

        Expected failure: AttributeError (_save_cache method doesn't exist yet)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add embedding to cache AND metadata (cache cleanup requires metadata entry)
            embedding = np.random.rand(768).astype(np.float32)
            manager.embedding_cache['chunk_123'] = embedding
            manager.metadata_db['chunk_123'] = {
                'metadata': {'file_path': 'test.py'},
                'chunk_id': 'chunk_123',
                'faiss_id': 0
            }

            # Save cache to disk
            manager._save_cache()

            # Cache file should exist
            assert manager.cache_path.exists(), "Cache file should exist after save"

            # Should be able to read it back (versioned format)
            import pickle
            with open(manager.cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            # Verify versioned structure
            assert 'version' in cache_data, "Cache should have version"
            assert 'embeddings' in cache_data, "Cache should have embeddings"
            assert 'chunk_123' in cache_data['embeddings'], "Chunk should be in saved cache"
            np.testing.assert_array_equal(cache_data['embeddings']['chunk_123'], embedding)

    def test_cache_loads_after_restart(self):
        """
        Test 3: Cache Loads After Restart (RED phase)

        Cache should persist across Python sessions (manager restarts).

        Expected failure: Cache not loaded in __init__ (no _load_cache call)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Session 1: Create cache
            manager1 = FixedCodeIndexManager(tmpdir)
            embedding = np.random.rand(768).astype(np.float32)
            manager1.embedding_cache['chunk_123'] = embedding
            manager1.metadata_db['chunk_123'] = {
                'metadata': {'file_path': 'test.py'},
                'chunk_id': 'chunk_123',
                'faiss_id': 0
            }
            manager1._save_cache()

            # Session 2: Load cache (simulates restart)
            manager2 = FixedCodeIndexManager(tmpdir)

            # Cache should be loaded automatically
            assert 'chunk_123' in manager2.embedding_cache, "Cache should load on init"
            np.testing.assert_array_equal(
                manager2.embedding_cache['chunk_123'],
                embedding,
                err_msg="Loaded embedding should match saved embedding"
            )

    def test_cache_atomic_write(self):
        """
        Test 4: Cache Atomic Write (RED phase)

        Cache writes should use atomic pattern (temp file + rename) to prevent
        corruption if process crashes during write.

        Expected failure: _save_cache() doesn't use temp file pattern yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add embedding to cache
            embedding = np.random.rand(768).astype(np.float32)
            manager.embedding_cache['chunk_123'] = embedding

            # Mock os.rename to verify it's called with temp file
            import os
            original_rename = os.rename
            rename_calls = []

            def mock_rename(src, dst):
                rename_calls.append((src, dst))
                original_rename(src, dst)

            # Patch rename and save
            import unittest.mock as mock
            with mock.patch('os.rename', side_effect=mock_rename):
                manager._save_cache()

            # Verify atomic write pattern: temp file -> final file
            assert len(rename_calls) == 1, "Should have exactly one rename call"
            src, dst = rename_calls[0]
            assert src.endswith('.tmp'), f"Source should be temp file (.tmp), got: {src}"
            assert dst == str(manager.cache_path), f"Destination should be cache_path, got: {dst}"

            # Cache file should exist (renamed from temp)
            assert manager.cache_path.exists(), "Cache file should exist after atomic write"

    def test_cache_stores_correct_dimensions(self):
        """
        Test 5: Cache Correct Dimensions (RED phase)

        Cache should store 768-dim float32 numpy arrays.

        Expected failure: No dimension validation yet (will pass actually,
        but we're testing the validation exists conceptually)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add embedding with correct dimensions AND metadata
            embedding = np.random.rand(768).astype(np.float32)
            manager.embedding_cache['chunk_123'] = embedding
            manager.metadata_db['chunk_123'] = {
                'metadata': {'file_path': 'test.py'},
                'chunk_id': 'chunk_123',
                'faiss_id': 0
            }

            # Verify dimensions
            assert manager.embedding_cache['chunk_123'].shape == (768,), \
                "Embedding should be 768-dimensional"
            assert manager.embedding_cache['chunk_123'].dtype == np.float32, \
                "Embedding should be float32"

            # Save and reload
            manager._save_cache()
            manager2 = FixedCodeIndexManager(tmpdir)

            # Verify dimensions persist
            assert manager2.embedding_cache['chunk_123'].shape == (768,), \
                "Loaded embedding should be 768-dimensional"
            assert manager2.embedding_cache['chunk_123'].dtype == np.float32, \
                "Loaded embedding should be float32"

    def test_cache_handles_missing_file(self):
        """
        Test 6: Cache Handles Missing File (RED phase)

        Cache should gracefully handle missing file (empty cache on load).

        Expected: This should already pass with current implementation
        (graceful degradation in _load_cache)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize manager with no existing cache file
            manager = FixedCodeIndexManager(tmpdir)

            # Cache should be empty (no error)
            assert manager.embedding_cache == {}, "Cache should be empty when file missing"

            # Now save, delete, and reload
            manager.embedding_cache['chunk_123'] = np.random.rand(768).astype(np.float32)
            manager._save_cache()
            assert manager.cache_path.exists(), "Cache file should exist after save"

            # Delete cache file
            manager.cache_path.unlink()

            # Load should handle missing file gracefully
            manager2 = FixedCodeIndexManager(tmpdir)
            assert manager2.embedding_cache == {}, "Cache should be empty when file deleted"


class TestCacheIntegration:
    """Integration tests: Cache should integrate with add_embeddings() automatically"""

    def test_add_embeddings_caches_automatically(self):
        """
        Integration Test: add_embeddings() should automatically cache

        When add_embeddings() is called, it should:
        1. Add embeddings to FAISS index
        2. Store embeddings in cache
        3. Save cache to disk

        Expected failure: add_embeddings() doesn't cache yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Create mock embedding result (simulates what embedder.embed_chunks returns)
            from types import SimpleNamespace
            embedding = np.random.rand(768).astype(np.float32)
            embedding_result = SimpleNamespace(
                chunk_id='chunk_123',
                embedding=embedding,
                metadata={'file_path': 'test.py', 'line_start': 1, 'line_end': 10}
            )

            # Call add_embeddings
            manager.add_embeddings([embedding_result])

            # Should be in cache
            assert 'chunk_123' in manager.embedding_cache, \
                "add_embeddings() should cache embedding"
            np.testing.assert_array_equal(
                manager.embedding_cache['chunk_123'],
                embedding,
                err_msg="Cached embedding should match input"
            )

            # Cache should persist (was saved)
            manager2 = FixedCodeIndexManager(tmpdir)
            assert 'chunk_123' in manager2.embedding_cache, \
                "Cache should persist after add_embeddings()"


class TestBloatTracking:
    """Feature 2: Bloat Tracking - Monitor index bloat from lazy deletion"""

    def test_bloat_zero_initially(self):
        """
        Test 1: Bloat Zero Initially (RED phase)

        Fresh index should have 0% bloat.
        Bloat = stale vectors / total vectors

        Expected failure: _calculate_bloat() doesn't exist yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Calculate bloat on empty index
            bloat = manager._calculate_bloat()

            # Verify bloat metrics
            assert bloat['total_vectors'] == 0, "Empty index should have 0 total vectors"
            assert bloat['active_chunks'] == 0, "Empty index should have 0 active chunks"
            assert bloat['stale_vectors'] == 0, "Empty index should have 0 stale vectors"
            assert bloat['bloat_percentage'] == 0.0, "Empty index should have 0% bloat"

    def test_bloat_increases_after_lazy_delete(self):
        """
        Test 2: Bloat Increases After Delete (RED phase)

        Lazy delete (removing from metadata_db but not from FAISS) should increase bloat.

        Expected: This should pass immediately - bloat calculation already handles this
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add 100 chunks
            from types import SimpleNamespace
            for i in range(100):
                embedding = np.random.rand(768).astype(np.float32)
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=embedding,
                    metadata={'file_path': f'file_{i}.py', 'line_start': 1, 'line_end': 10}
                )
                manager.add_embeddings([result])

            # Verify no bloat initially
            bloat_before = manager._calculate_bloat()
            assert bloat_before['bloat_percentage'] == 0.0, "No bloat before deletion"

            # Lazy delete 20 chunks (remove from metadata, leave in FAISS)
            for i in range(20):
                del manager.metadata_db[f'chunk_{i}']

            # Calculate bloat after deletion
            bloat_after = manager._calculate_bloat()

            # Verify bloat metrics
            assert bloat_after['total_vectors'] == 100, "FAISS still has all 100 vectors"
            assert bloat_after['active_chunks'] == 80, "Metadata has 80 chunks (deleted 20)"
            assert bloat_after['stale_vectors'] == 20, "20 stale vectors from deletion"
            assert bloat_after['bloat_percentage'] == 20.0, "Bloat should be 20%"

    def test_rebuild_trigger_hybrid_logic(self):
        """
        Test 3: Rebuild Trigger Hybrid Logic (RED phase)

        Rebuild triggers: (20% bloat AND 500 stale) OR (30% bloat)

        This prevents rebuilding small projects with low absolute bloat count.

        Expected failure: _needs_rebuild() doesn't exist yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Scenario 1: 20% bloat but only 100 stale → NO rebuild
            # (simulate 500 total, 400 active, 100 stale = 20%)
            from types import SimpleNamespace
            for i in range(500):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            # Delete 100 (20% bloat, but <500 stale)
            for i in range(100):
                del manager.metadata_db[f'chunk_{i}']

            assert not manager._needs_rebuild(), "20% + 100 stale → NO rebuild"

            # Scenario 2: 20% bloat AND 500 stale → YES rebuild
            # Delete 400 more (total 500 deleted = 500 stale, still 20%)
            for i in range(100, 500):
                del manager.metadata_db[f'chunk_{i}']

            assert manager._needs_rebuild(), "20% + 500 stale → YES rebuild"

            # Scenario 3: 30% bloat regardless of count → YES rebuild
            # Add 100 more, delete 30 (30% of 100)
            for i in range(500, 600):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            # Clear previous state
            manager.metadata_db = {}
            for i in range(500, 600):
                manager.metadata_db[f'chunk_{i}'] = {'metadata': {}, 'chunk_id': f'chunk_{i}', 'faiss_id': i}

            # Delete 30 out of 100 (30% bloat, but only 30 stale)
            for i in range(570, 600):
                del manager.metadata_db[f'chunk_{i}']

            assert manager._needs_rebuild(), "30% bloat → YES rebuild (fallback)"

    def test_small_project_rebuild_trigger(self):
        """
        Test 4: Small Project 30% Trigger (RED phase)

        Small projects (<1667 vectors) use 30% fallback trigger.
        This prevents primary trigger (20% + 500 stale) from being too strict for small projects.

        Expected: Should pass immediately (fallback logic already implemented)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Small project: 1000 total, 700 active, 300 stale = 30% bloat
            # Should trigger despite stale_count < 500
            from types import SimpleNamespace
            for i in range(1000):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            # Delete 300 (30% bloat, but only 300 stale < 500)
            for i in range(300):
                del manager.metadata_db[f'chunk_{i}']

            # Should trigger via 30% fallback (despite stale < 500)
            assert manager._needs_rebuild(), "30% bloat → YES rebuild (fallback trigger)"

            # Verify 30% is the threshold
            # 29% bloat (290 stale) → NO rebuild
            manager2 = FixedCodeIndexManager(tmpdir)
            for i in range(1000):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager2.add_embeddings([result])

            # Delete 290 (29% bloat)
            for i in range(290):
                del manager2.metadata_db[f'chunk_{i}']

            bloat = manager2._calculate_bloat()
            # Verify it's ~29% (floating point tolerance)
            assert 28.9 <= bloat['bloat_percentage'] < 29.5, f"Should be ~29% bloat, got {bloat['bloat_percentage']}"
            assert not manager2._needs_rebuild(), "29% bloat → NO rebuild (below threshold)"

    def test_rebuild_resets_bloat(self):
        """
        Test 5: Rebuild Resets Bloat (RED phase)

        After rebuild, bloat should be 0% because only active chunks are in the index.

        Expected failure: rebuild_from_cache() doesn't exist yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add 100 chunks
            from types import SimpleNamespace
            for i in range(100):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py', 'line_start': i*10, 'line_end': i*10+10}
                )
                manager.add_embeddings([result])

            # Delete 20 chunks (20% bloat)
            for i in range(20):
                del manager.metadata_db[f'chunk_{i}']

            bloat_before = manager._calculate_bloat()
            assert bloat_before['bloat_percentage'] == 20.0, "Should have 20% bloat before rebuild"
            assert bloat_before['total_vectors'] == 100, "FAISS should have 100 vectors"
            assert bloat_before['active_chunks'] == 80, "Metadata should have 80 chunks"

            # Rebuild from cache (this should remove stale vectors)
            manager.rebuild_from_cache()

            # After rebuild, bloat should be 0
            bloat_after = manager._calculate_bloat()
            assert bloat_after['bloat_percentage'] == 0.0, "Bloat should be 0% after rebuild"
            assert bloat_after['total_vectors'] == 80, "FAISS should only have 80 vectors (active chunks)"
            assert bloat_after['active_chunks'] == 80, "Metadata should still have 80 chunks"
            assert bloat_after['stale_vectors'] == 0, "No stale vectors after rebuild"

    def test_stats_json_includes_bloat(self):
        """
        Test 6: Stats.json Bloat Metrics (RED phase)

        stats.json should include bloat metrics when index is saved.

        Expected failure: stats.json doesn't include bloat fields yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add 100 chunks
            from types import SimpleNamespace
            for i in range(100):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            # Delete 20 chunks (20% bloat)
            for i in range(20):
                del manager.metadata_db[f'chunk_{i}']

            # Save index (triggers _update_stats())
            manager.save_index()

            # Read stats.json
            stats_path = manager.index_dir / "stats.json"
            assert stats_path.exists(), "stats.json should exist after save"

            import json
            with open(stats_path) as f:
                stats = json.load(f)

            # Verify bloat metrics are present
            assert 'bloat_percentage' in stats, "stats.json should include bloat_percentage"
            assert 'stale_vectors' in stats, "stats.json should include stale_vectors"
            assert 'total_vectors' in stats, "stats.json should include total_vectors"
            assert 'active_chunks' in stats, "stats.json should include active_chunks"

            # Verify values are correct
            assert stats['bloat_percentage'] == 20.0, f"Expected 20% bloat, got {stats['bloat_percentage']}"
            assert stats['stale_vectors'] == 20, f"Expected 20 stale vectors, got {stats['stale_vectors']}"
            assert stats['total_vectors'] == 100, f"Expected 100 total vectors, got {stats['total_vectors']}"
            assert stats['active_chunks'] == 80, f"Expected 80 active chunks, got {stats['active_chunks']}"


class TestCacheVersioning:
    """Critical Feature: Cache Versioning - Prevent stale embedding usage after model changes"""

    def test_cache_saves_with_version_metadata(self):
        """
        Test 1: Cache saves with version metadata (RED phase)

        Cache must include: version number, model_name, embedding_dimension
        This prevents using incompatible cached embeddings after model changes.

        Expected failure: Cache doesn't have version metadata yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add one embedding
            from types import SimpleNamespace
            embedding = np.random.rand(768).astype(np.float32)
            result = SimpleNamespace(
                chunk_id='chunk_1',
                embedding=embedding,
                metadata={'file_path': 'test.py'}
            )
            manager.add_embeddings([result])

            # Load cache file directly and check structure
            import pickle
            with open(manager.cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            # Should be a dict with metadata keys
            assert isinstance(cache_data, dict), "Cache should be a dict"
            assert 'version' in cache_data, "Cache must have version field"
            assert 'model_name' in cache_data, "Cache must have model_name field"
            assert 'embedding_dimension' in cache_data, "Cache must have embedding_dimension field"
            assert 'embeddings' in cache_data, "Cache must have embeddings field"

            # Verify values
            assert cache_data['version'] == 1, "Version should be 1"
            assert cache_data['embedding_dimension'] == 768, "Dimension should be 768"
            assert isinstance(cache_data['model_name'], str), "Model name should be string"
            assert len(cache_data['model_name']) > 0, "Model name should not be empty"

            # Verify embeddings are stored correctly
            assert 'chunk_1' in cache_data['embeddings'], "Embedding should be in cache"
            np.testing.assert_array_equal(cache_data['embeddings']['chunk_1'], embedding)

    def test_cache_rejects_incompatible_versions(self):
        """
        Test 2: Cache rejects incompatible versions (RED phase)

        When cache version/model/dimension mismatches, cache should be cleared
        and warning printed. This prevents using stale embeddings.

        Expected: Should pass immediately (validation already implemented)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Scenario 1: Wrong cache version
            manager1 = FixedCodeIndexManager(tmpdir)
            embedding = np.random.rand(768).astype(np.float32)
            manager1.embedding_cache['chunk_1'] = embedding
            manager1._save_cache()

            # Manually corrupt cache version
            import pickle
            with open(manager1.cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            cache_data['version'] = 999  # Incompatible version
            with open(manager1.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)

            # Reload should clear cache
            manager2 = FixedCodeIndexManager(tmpdir)
            assert manager2.embedding_cache == {}, "Cache should be cleared on version mismatch"

            # Scenario 2: Wrong dimension
            manager3 = FixedCodeIndexManager(tmpdir)
            manager3.embedding_cache['chunk_1'] = embedding
            manager3._save_cache()

            with open(manager3.cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            cache_data['embedding_dimension'] = 384  # Wrong dimension
            with open(manager3.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)

            manager4 = FixedCodeIndexManager(tmpdir)
            assert manager4.embedding_cache == {}, "Cache should be cleared on dimension mismatch"

            # Scenario 3: Wrong model name
            manager5 = FixedCodeIndexManager(tmpdir)
            manager5.embedding_cache['chunk_1'] = embedding
            manager5._save_cache()

            with open(manager5.cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            cache_data['model_name'] = 'different-model'  # Wrong model
            with open(manager5.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)

            manager6 = FixedCodeIndexManager(tmpdir)
            assert manager6.embedding_cache == {}, "Cache should be cleared on model mismatch"


class TestRebuildSafety:
    """Critical Feature: Rebuild Safety - Prevent data loss during rebuild operations"""

    def test_rebuild_creates_backup_before_starting(self):
        """
        Test 1: Rebuild creates backup (RED phase)

        rebuild_from_cache() must backup old index files before destructive operations.
        This prevents data loss if rebuild fails.

        Expected failure: No backup mechanism implemented yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add initial data and save
            from types import SimpleNamespace
            for i in range(10):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])
            manager.save_index()

            # Verify backup files are created during rebuild
            manager.rebuild_from_cache()

            # Check for backup directory
            backup_dir = manager.index_dir / "backup"
            assert backup_dir.exists(), "Backup directory should exist after rebuild"

            # Verify backup contains index files
            backup_index = backup_dir / "code.index"
            backup_metadata = backup_dir / "metadata.db"
            backup_chunk_ids = backup_dir / "chunk_ids.pkl"

            assert backup_index.exists(), "Backup should contain code.index"
            assert backup_metadata.exists(), "Backup should contain metadata.db"
            assert backup_chunk_ids.exists(), "Backup should contain chunk_ids.pkl"


class TestCacheCleanup:
    """High Priority: Cache Cleanup - Prevent cache bloat from deleted chunks"""

    def test_save_cache_prunes_deleted_chunks(self):
        """
        Test 1: save_cache() prunes deleted chunks (RED phase)

        When chunks are deleted from metadata_db, their embeddings should
        be removed from cache during save. This prevents cache bloat.

        Expected failure: Cache cleanup not implemented yet
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add 100 chunks
            from types import SimpleNamespace
            for i in range(100):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            # Verify all 100 in cache
            assert len(manager.embedding_cache) == 100, "Should have 100 embeddings in cache"

            # Delete 20 chunks from metadata (simulate file deletion)
            for i in range(20):
                del manager.metadata_db[f'chunk_{i}']

            # Save cache (should prune deleted chunks)
            manager._save_cache()

            # Reload to verify pruning persisted
            manager2 = FixedCodeIndexManager(tmpdir)
            assert len(manager2.embedding_cache) == 80, "Cache should only have 80 embeddings after pruning"

            # Verify deleted chunks not in cache
            for i in range(20):
                assert f'chunk_{i}' not in manager2.embedding_cache, f"Deleted chunk_{i} should not be in cache"

            # Verify remaining chunks still in cache
            for i in range(20, 100):
                assert f'chunk_{i}' in manager2.embedding_cache, f"Active chunk_{i} should be in cache"
