"""
Integration Tests for Incremental Cache System

Tests full workflows across multiple components to ensure the system
works end-to-end in production scenarios.

Key differences from unit tests:
- Test complete workflows, not isolated functions
- Test cross-session persistence
- Test interaction between components (cache + index + metadata)
- Test production error scenarios
"""

import tempfile
import pytest
import numpy as np
import sys
from pathlib import Path
from types import SimpleNamespace

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from incremental_reindex import FixedCodeIndexManager


class TestCrossSessionPersistence:
    """
    Integration Test Suite: Cross-Session Persistence

    Validates that cache, index, and metadata persist correctly across
    Python sessions (process restarts).
    """

    def test_cache_persists_across_sessions(self):
        """
        End-to-end: Cache should persist across sessions

        Scenario:
        1. Session 1: Create index with embeddings
        2. Session 1: Save and exit
        3. Session 2: Load index, verify cache loaded
        4. Session 2: Search works without re-embedding
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # SESSION 1: Create index
            manager1 = FixedCodeIndexManager(tmpdir)

            # Add 50 chunks
            embeddings_added = []
            for i in range(50):
                embedding = np.random.rand(768).astype(np.float32)
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=embedding,
                    metadata={'file_path': f'file_{i}.py', 'line_start': 1}
                )
                manager1.add_embeddings([result])
                embeddings_added.append(embedding)

            # Save index
            manager1.save_index()

            # Verify cache was saved
            assert len(manager1.embedding_cache) == 50, "Session 1: Cache should have 50 embeddings"
            assert manager1.cache_path.exists(), "Session 1: Cache file should exist"

            # SESSION 2: Load index (simulates process restart)
            manager2 = FixedCodeIndexManager(tmpdir)

            # Verify cache was loaded
            assert len(manager2.embedding_cache) == 50, "Session 2: Cache should have loaded 50 embeddings"
            assert manager2.get_index_size() == 50, "Session 2: Index should have 50 chunks"

            # Verify all embeddings are in cache
            for i in range(50):
                assert f'chunk_{i}' in manager2.embedding_cache, f"Session 2: chunk_{i} missing from cache"

            # Verify search works (uses persisted index)
            query = np.random.rand(768).astype(np.float32)
            results = manager2.search(query, k=5)
            assert len(results) == 5, "Session 2: Search should return 5 results"

    def test_rebuild_persists_across_sessions(self):
        """
        End-to-end: Rebuild from cache should persist correctly

        Scenario:
        1. Session 1: Create index with 100 chunks
        2. Session 1: Simulate bloat (delete 30 from metadata)
        3. Session 1: Rebuild from cache
        4. Session 1: Save and exit
        5. Session 2: Load index, verify bloat is 0
        6. Session 2: Verify search works
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # SESSION 1: Create index with bloat
            manager1 = FixedCodeIndexManager(tmpdir)

            # Add 100 chunks
            for i in range(100):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager1.add_embeddings([result])

            # Simulate bloat: delete 30 chunks from metadata (lazy deletion)
            for i in range(30):
                del manager1.metadata_db[f'chunk_{i}']

            # Verify bloat exists
            bloat_before = manager1._calculate_bloat()
            assert bloat_before['bloat_percentage'] == 30.0, "Session 1: Should have 30% bloat"

            # Rebuild from cache
            manager1.rebuild_from_cache()

            # Verify bloat is gone
            bloat_after = manager1._calculate_bloat()
            assert bloat_after['bloat_percentage'] == 0.0, "Session 1: Bloat should be 0 after rebuild"

            # Save index
            manager1.save_index()

            # SESSION 2: Load index
            manager2 = FixedCodeIndexManager(tmpdir)

            # Verify bloat is still 0 (rebuild persisted)
            bloat_session2 = manager2._calculate_bloat()
            assert bloat_session2['bloat_percentage'] == 0.0, "Session 2: Bloat should still be 0"
            assert bloat_session2['total_vectors'] == 70, "Session 2: Should have 70 vectors"
            assert bloat_session2['active_chunks'] == 70, "Session 2: Should have 70 active chunks"

            # Verify search works
            query = np.random.rand(768).astype(np.float32)
            results = manager2.search(query, k=5)
            assert len(results) == 5, "Session 2: Search should work after rebuild"


class TestCompleteWorkflows:
    """
    Integration Test Suite: Complete Workflows

    Tests full workflows that involve multiple operations in sequence.
    """

    def test_full_lifecycle_workflow(self):
        """
        End-to-end: Complete lifecycle from creation to cleanup

        Workflow:
        1. Create index
        2. Add embeddings (cache populated)
        3. Simulate file changes (bloat accumulates)
        4. Rebuild from cache (bloat cleared)
        5. Search still works
        6. Stats are accurate
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # STEP 1: Add initial embeddings
            for i in range(100):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            # Verify cache populated
            assert len(manager.embedding_cache) == 100, "Step 1: Cache should have 100 embeddings"

            # STEP 2: Simulate file changes (lazy deletion creates bloat)
            for i in range(20):
                del manager.metadata_db[f'chunk_{i}']

            # Verify bloat tracked
            bloat = manager._calculate_bloat()
            assert bloat['stale_vectors'] == 20, "Step 2: Should have 20 stale vectors"
            assert bloat['bloat_percentage'] == 20.0, "Step 2: Should have 20% bloat"

            # STEP 3: Rebuild from cache (cleanup bloat)
            manager.rebuild_from_cache()

            # Verify bloat cleared
            bloat_after = manager._calculate_bloat()
            assert bloat_after['bloat_percentage'] == 0.0, "Step 3: Bloat should be cleared"
            assert manager.get_index_size() == 80, "Step 3: Should have 80 chunks (removed 20)"

            # STEP 4: Search still works
            query = np.random.rand(768).astype(np.float32)
            results = manager.search(query, k=5)
            assert len(results) == 5, "Step 4: Search should return 5 results"

            # Verify results are from active chunks (not deleted ones)
            for chunk_id, similarity, metadata in results:
                # chunk_0 through chunk_19 were deleted
                chunk_num = int(chunk_id.split('_')[1])
                assert chunk_num >= 20, f"Step 4: Result {chunk_id} should not be from deleted chunks"

            # STEP 5: Verify bloat metrics are tracked
            bloat_final = manager._calculate_bloat()
            assert bloat_final['bloat_percentage'] == 0.0, "Step 5: Bloat should be 0%"
            assert bloat_final['total_vectors'] == 80, "Step 5: Should have 80 total vectors"
            assert bloat_final['active_chunks'] == 80, "Step 5: Should have 80 active chunks"
            assert bloat_final['stale_vectors'] == 0, "Step 5: Should have 0 stale vectors"

    def test_cache_cleanup_integration(self):
        """
        End-to-end: Cache cleanup removes embeddings for deleted chunks

        Workflow:
        1. Add 100 chunks
        2. Delete 30 chunks from metadata
        3. Save cache (should prune deleted chunks)
        4. Reload manager
        5. Verify cache only has 70 embeddings
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # STEP 1: Create index
            manager1 = FixedCodeIndexManager(tmpdir)

            for i in range(100):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager1.add_embeddings([result])

            assert len(manager1.embedding_cache) == 100, "Step 1: Cache should have 100"

            # STEP 2: Delete 30 chunks from metadata (simulate file deletion)
            for i in range(30):
                del manager1.metadata_db[f'chunk_{i}']

            # STEP 3: Save (triggers cleanup)
            manager1.save_index()

            # Verify in-memory cache was pruned
            assert len(manager1.embedding_cache) == 70, "Step 3: In-memory cache should be pruned to 70"

            # STEP 4: Reload manager (test persistence)
            manager2 = FixedCodeIndexManager(tmpdir)

            # STEP 5: Verify persisted cache only has 70 embeddings
            assert len(manager2.embedding_cache) == 70, "Step 5: Persisted cache should have 70"

            # Verify deleted chunks not in cache
            for i in range(30):
                assert f'chunk_{i}' not in manager2.embedding_cache, f"Step 5: Deleted chunk_{i} should not be in cache"

            # Verify active chunks still in cache
            for i in range(30, 100):
                assert f'chunk_{i}' in manager2.embedding_cache, f"Step 5: Active chunk_{i} should be in cache"


class TestErrorRecovery:
    """
    Integration Test Suite: Error Recovery

    Tests that the system handles errors gracefully and can recover.
    """

    def test_rebuild_with_backup_recovery(self):
        """
        End-to-end: Rebuild creates backup for recovery

        Workflow:
        1. Create index with data
        2. Trigger rebuild (backup created)
        3. Verify backup exists
        4. Simulate rebuild completion
        5. Verify data intact
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FixedCodeIndexManager(tmpdir)

            # Add data
            for i in range(50):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager.add_embeddings([result])

            manager.save_index()

            # Trigger rebuild (should create backup)
            manager.rebuild_from_cache()

            # Verify backup was created
            backup_dir = manager.index_dir / "backup"
            assert backup_dir.exists(), "Backup directory should exist after rebuild"
            assert (backup_dir / "code.index").exists(), "Backup should contain index file"
            assert (backup_dir / "metadata.db").exists(), "Backup should contain metadata"
            assert (backup_dir / "chunk_ids.pkl").exists(), "Backup should contain chunk_ids"

            # Verify index still works
            assert manager.get_index_size() == 50, "Index should still have 50 chunks"

            query = np.random.rand(768).astype(np.float32)
            results = manager.search(query, k=5)
            assert len(results) == 5, "Search should work after rebuild with backup"

    def test_cache_version_mismatch_recovery(self):
        """
        End-to-end: Cache version mismatch clears cache gracefully

        Workflow:
        1. Create index with current version
        2. Manually corrupt cache version
        3. Reload manager
        4. Verify cache was cleared (not crashed)
        5. Verify index still works
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create index
            manager1 = FixedCodeIndexManager(tmpdir)

            for i in range(20):
                result = SimpleNamespace(
                    chunk_id=f'chunk_{i}',
                    embedding=np.random.rand(768).astype(np.float32),
                    metadata={'file_path': f'file_{i}.py'}
                )
                manager1.add_embeddings([result])

            manager1.save_index()

            # Verify cache exists
            assert manager1.cache_path.exists(), "Cache should exist"

            # Corrupt cache version
            import pickle
            with open(manager1.cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            cache_data['version'] = 999  # Invalid version

            with open(manager1.cache_path, 'wb') as f:
                pickle.dump(cache_data, f)

            # Reload manager (should clear cache gracefully)
            manager2 = FixedCodeIndexManager(tmpdir)

            # Verify cache was cleared (not crashed)
            assert len(manager2.embedding_cache) == 0, "Cache should be cleared on version mismatch"

            # Verify index still loaded correctly
            assert manager2.get_index_size() == 20, "Index should still have 20 chunks"

            # Verify search still works
            query = np.random.rand(768).astype(np.float32)
            results = manager2.search(query, k=5)
            assert len(results) == 5, "Search should work even with cleared cache"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
