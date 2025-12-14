#!/usr/bin/env python3
"""
Tests for Phase 2.4: Incremental Operations

Tests the actual incremental reindex functionality that uses cache
for unchanged files and only re-embeds changed files.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import numpy as np

# Add scripts directory to path
TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from incremental_reindex import FixedIncrementalIndexer, FixedCodeIndexManager
except ImportError:
    import pytest
    pytest.skip("Global installation not found - expected in test environment", allow_module_level=True)


class TestDeleteChunksForFile:
    """Test _delete_chunks_for_file() helper method"""

    def test_delete_chunks_for_single_file(self):
        """Test deleting all chunks for a specific file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_project = Path(tmpdir) / "test_project"
            test_project.mkdir()

            # Create test files
            (test_project / "file1.py").write_text("def foo(): pass")
            (test_project / "file2.py").write_text("def bar(): pass")

            # Index the project
            indexer = FixedIncrementalIndexer(project_path=str(test_project))
            indexer.auto_reindex()

            # Get initial counts
            initial_metadata_count = len(indexer.indexer.metadata_db)
            initial_cache_count = len(indexer.indexer.embedding_cache)

            assert initial_metadata_count > 0, "Should have indexed some chunks"
            assert initial_cache_count > 0, "Should have cached embeddings"

            # Find chunks for file1.py
            file1_chunks = []
            for chunk_id, entry in indexer.indexer.metadata_db.items():
                metadata = entry['metadata']
                if str(test_project / "file1.py") in metadata.get('file_path', ''):
                    file1_chunks.append(chunk_id)

            assert len(file1_chunks) > 0, "Should have chunks for file1.py"

            # Delete chunks for file1.py
            deleted_count = indexer._delete_chunks_for_file(str(test_project / "file1.py"))

            # Verify deletion
            assert deleted_count == len(file1_chunks), f"Should delete {len(file1_chunks)} chunks"

            # Verify chunks removed from metadata
            for chunk_id in file1_chunks:
                assert chunk_id not in indexer.indexer.metadata_db, \
                    f"Chunk {chunk_id} should be removed from metadata"

            # Verify chunks removed from cache
            for chunk_id in file1_chunks:
                assert chunk_id not in indexer.indexer.embedding_cache, \
                    f"Chunk {chunk_id} should be removed from cache"

            # Verify other chunks still exist
            assert len(indexer.indexer.metadata_db) > 0, \
                "Other file chunks should still exist in metadata"
            assert len(indexer.indexer.embedding_cache) > 0, \
                "Other file chunks should still exist in cache"

    def test_delete_chunks_for_nonexistent_file(self):
        """Test deleting chunks for file that has no chunks (should return 0)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_project = Path(tmpdir) / "test_project"
            test_project.mkdir()

            # Create and index a single file
            (test_project / "file1.py").write_text("def foo(): pass")

            indexer = FixedIncrementalIndexer(project_path=str(test_project))
            indexer.auto_reindex()

            # Try to delete chunks for a file that doesn't exist
            deleted_count = indexer._delete_chunks_for_file(str(test_project / "nonexistent.py"))

            assert deleted_count == 0, "Should return 0 when no chunks found"


if __name__ == "__main__":
    print("Running incremental operations tests...")
    import pytest
    pytest.main([__file__, "-v"])
