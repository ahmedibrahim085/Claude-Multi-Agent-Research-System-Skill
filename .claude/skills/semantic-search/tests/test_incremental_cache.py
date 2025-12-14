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
