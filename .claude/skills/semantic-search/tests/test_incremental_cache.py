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

            # Add embedding to cache
            embedding = np.random.rand(768).astype(np.float32)
            manager.embedding_cache['chunk_123'] = embedding

            # Save cache to disk
            manager._save_cache()

            # Cache file should exist
            assert manager.cache_path.exists(), "Cache file should exist after save"

            # Should be able to read it back
            import pickle
            with open(manager.cache_path, 'rb') as f:
                saved_cache = pickle.load(f)

            assert 'chunk_123' in saved_cache, "Chunk should be in saved cache"
            np.testing.assert_array_equal(saved_cache['chunk_123'], embedding)

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

            # Add embedding with correct dimensions
            embedding = np.random.rand(768).astype(np.float32)
            manager.embedding_cache['chunk_123'] = embedding

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
