#!/usr/bin/env python3
"""
Tests for Model Caching Optimization

Validates that the embedder model is reused across multiple
FixedIncrementalIndexer instances to eliminate reload overhead.

Evidence-based: Model loading takes ~0.8s per reindex.
Fix: Cache embedder at class level, reuse across instances.
"""

import tempfile
import time
from pathlib import Path
import sys
from unittest import mock

# Add scripts directory to path
TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from incremental_reindex import FixedIncrementalIndexer


def test_embedder_reused_across_instances():
    """
    Test that creating multiple FixedIncrementalIndexer instances
    reuses the same embedder (doesn't reload model).

    BEFORE fix: Each instance creates new CodeEmbedder (~0.8s load time)
    AFTER fix: Embedder cached, reused across instances (~0.001s)
    """
    print("\n" + "="*60)
    print("TEST: Embedder Reuse Across Instances")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()

        # Create a test file
        (project_path / "test.py").write_text("def test(): pass\n")

        # Create first indexer - this will load the model
        print("\n1. Creating first indexer (may load model)...")
        start1 = time.time()
        indexer1 = FixedIncrementalIndexer(project_path=str(project_path))
        time1 = time.time() - start1

        # Get reference to embedder
        embedder1 = indexer1.embedder

        # Create second indexer - this should reuse the model
        print("2. Creating second indexer (should reuse model)...")
        start2 = time.time()
        indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
        time2 = time.time() - start2

        # Get reference to embedder
        embedder2 = indexer2.embedder

        print(f"\n   First indexer creation:  {time1:.3f}s")
        print(f"   Second indexer creation: {time2:.3f}s")

        # Verify embedder is reused (same object)
        assert embedder1 is embedder2, "Embedder should be the same object (cached)"

        print(f"\n   ✓ Embedder reused: {embedder1 is embedder2}")
        print(f"   ✓ Time savings: {time1 - time2:.3f}s ({(1 - time2/time1)*100:.1f}% faster)")


def test_model_loading_overhead_eliminated():
    """
    Test that model loading overhead is eliminated when using cached embedder.

    Measures the time to create multiple indexers. With caching, subsequent
    creations should be much faster (no model loading).
    """
    print("\n" + "="*60)
    print("TEST: Model Loading Overhead Eliminated")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()
        (project_path / "test.py").write_text("def test(): pass\n")

        # Time creating 3 indexers
        times = []
        for i in range(3):
            start = time.time()
            indexer = FixedIncrementalIndexer(project_path=str(project_path))
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"\n   Indexer {i+1}: {elapsed:.3f}s")

        # First creation may load model (slower)
        # Subsequent creations should be fast (cached)
        first_time = times[0]
        avg_subsequent = sum(times[1:]) / len(times[1:])

        print(f"\n   First creation:        {first_time:.3f}s")
        print(f"   Average subsequent:    {avg_subsequent:.3f}s")
        print(f"   Speedup:               {first_time / avg_subsequent:.1f}x")

        # Subsequent creations should be at least 2x faster
        # (if model loading takes ~0.8s and creation takes ~0.1s, ratio is 8x)
        speedup = first_time / avg_subsequent
        assert speedup >= 2.0, f"Subsequent creations should be at least 2x faster, got {speedup:.1f}x"

        print(f"\n   ✓ Model caching working: {speedup:.1f}x speedup")


def test_embedder_cleanup():
    """
    Test that embedder can be cleaned up when needed (memory management).

    Verifies that we can explicitly cleanup the cached embedder
    to free memory when needed.
    """
    print("\n" + "="*60)
    print("TEST: Embedder Cleanup")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test_project"
        project_path.mkdir()
        (project_path / "test.py").write_text("def test(): pass\n")

        # Create indexer (caches embedder)
        indexer1 = FixedIncrementalIndexer(project_path=str(project_path))
        embedder1 = indexer1.embedder

        # Cleanup embedder
        FixedIncrementalIndexer.cleanup_shared_embedder()

        # Create new indexer (should create new embedder)
        indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
        embedder2 = indexer2.embedder

        # Should be different objects (old one was cleaned up)
        assert embedder1 is not embedder2, "After cleanup, new embedder should be created"

        print(f"\n   ✓ Cleanup successful: New embedder created after cleanup")


if __name__ == "__main__":
    """Run all model caching tests"""
    print("\n" + "="*60)
    print("MODEL CACHING OPTIMIZATION TESTS")
    print("="*60)

    try:
        # Test 1: Embedder reused
        test_embedder_reused_across_instances()

        # Test 2: Overhead eliminated
        test_model_loading_overhead_eliminated()

        # Test 3: Cleanup works
        test_embedder_cleanup()

        # Summary
        print("\n" + "="*60)
        print("✅ ALL MODEL CACHING TESTS PASSED")
        print("="*60)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
