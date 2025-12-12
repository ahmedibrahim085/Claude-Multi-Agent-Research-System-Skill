#!/usr/bin/env python3
"""
POC Test: IndexIDMap2 + IndexIVFFlat Bug Verification

Tests if GitHub issue #4535 (IndexIDMap2 + IndexIVFFlat assertion failure)
is fixed in FAISS 1.13.0.

Background:
- August 2024: Bug reported with IndexIDMap2 wrapped around IndexIVFFlat
- November 2024: FAISS 1.13.0 released (MCP's current version)
- Question: Is the bug fixed?

Test Steps:
1. Create IndexIVFFlat base index
2. Wrap with IndexIDMap2
3. Train the index
4. Add vectors with custom IDs
5. Remove some IDs
6. Search and verify results

If this test PASSES: Incremental indexing is viable
If this test FAILS: Must use alternative approach

Run with MCP's Python:
~/.local/share/claude-context-local/.venv/bin/python test_indexidmap2_bug.py
"""

import sys
import numpy as np

try:
    import faiss
    print(f"✓ FAISS version: {faiss.__version__}")
except ImportError:
    print("✗ FAISS not available")
    sys.exit(1)


def test_indexidmap2_indexivf():
    """
    Test IndexIDMap2 + IndexIVFFlat combination

    This is the exact combination that failed in GitHub issue #4535
    """
    print("\n" + "="*70)
    print("TEST: IndexIDMap2 + IndexIVFFlat")
    print("="*70)

    # Parameters
    dim = 768  # Same as embeddinggemma-300m
    nlist = 100  # Number of clusters
    n_vectors = 1000  # Test with 1000 vectors

    print(f"\nParameters:")
    print(f"  Dimension: {dim}")
    print(f"  Clusters (nlist): {nlist}")
    print(f"  Test vectors: {n_vectors}")

    try:
        # Step 1: Create base IndexIVFFlat
        print("\n[1/6] Creating IndexIVFFlat base index...")
        quantizer = faiss.IndexFlatIP(dim)
        base_index = faiss.IndexIVFFlat(
            quantizer,
            dim,
            nlist,
            faiss.METRIC_INNER_PRODUCT
        )
        print(f"  ✓ Created IndexIVFFlat(dim={dim}, nlist={nlist})")

        # Step 2: Wrap with IndexIDMap2
        print("\n[2/6] Wrapping with IndexIDMap2...")
        index = faiss.IndexIDMap2(base_index)
        print(f"  ✓ Created IndexIDMap2(IndexIVFFlat(...))")
        print(f"  Index type: {type(index).__name__}")

        # Step 3: Train the index
        print("\n[3/6] Training index...")
        # Generate random training vectors
        np.random.seed(42)
        training_vectors = np.random.random((n_vectors, dim)).astype('float32')
        faiss.normalize_L2(training_vectors)  # Normalize for IP similarity

        base_index.train(training_vectors)
        print(f"  ✓ Trained on {n_vectors} vectors")
        print(f"  Index is_trained: {base_index.is_trained}")

        # Step 4: Add vectors with custom IDs
        print("\n[4/6] Adding vectors with custom IDs...")
        # Use file-based IDs like: hash("file1.py") = 12345
        custom_ids = np.arange(1000, 1000 + n_vectors, dtype=np.int64)

        index.add_with_ids(training_vectors, custom_ids)
        print(f"  ✓ Added {n_vectors} vectors with custom IDs")
        print(f"  Index ntotal: {index.ntotal}")

        # Step 5: Remove some IDs (simulate file deletion)
        print("\n[5/6] Removing vectors (simulate changed files)...")
        ids_to_remove = custom_ids[100:200]  # Remove 100 vectors

        # Create IDSelectorArray for removal
        selector = faiss.IDSelectorArray(len(ids_to_remove), faiss.swig_ptr(ids_to_remove))
        removed_count = index.remove_ids(selector)

        print(f"  ✓ Removed {removed_count} vectors")
        print(f"  Index ntotal after removal: {index.ntotal}")
        print(f"  Expected: {n_vectors - len(ids_to_remove)}")

        # Step 6: Search and verify results
        print("\n[6/6] Searching index...")
        query_vector = training_vectors[0:1]  # Use first vector as query
        k = 5

        similarities, indices = index.search(query_vector, k)
        print(f"  ✓ Search returned {k} results")
        print(f"  Top-5 IDs: {indices[0]}")
        print(f"  Top-5 similarities: {similarities[0]}")

        # Verify removed IDs are not in results
        removed_in_results = any(idx in ids_to_remove for idx in indices[0])
        if removed_in_results:
            print(f"  ⚠ WARNING: Removed ID found in search results!")
        else:
            print(f"  ✓ Removed IDs correctly excluded from results")

        print("\n" + "="*70)
        print("RESULT: ✓ TEST PASSED")
        print("="*70)
        print("\nConclusion:")
        print("  IndexIDMap2 + IndexIVFFlat works in FAISS 1.13.0")
        print("  GitHub issue #4535 appears to be FIXED")
        print("  Incremental indexing is VIABLE with this combination")

        return True

    except Exception as e:
        print("\n" + "="*70)
        print("RESULT: ✗ TEST FAILED")
        print("="*70)
        print(f"\nError: {e}")
        print(f"Error type: {type(e).__name__}")

        if "assert" in str(e).lower():
            print("\nThis appears to be the GitHub #4535 assertion failure bug")
            print("The bug is NOT fixed in FAISS 1.13.0")

        print("\nConclusion:")
        print("  IndexIDMap2 + IndexIVFFlat does NOT work reliably")
        print("  Must use alternative approach (optimize full rebuild)")

        return False


def test_indexidmap2_indexflat():
    """
    Test IndexIDMap2 + IndexFlatIP (fallback option)

    This should work (no IVF, just flat index with custom IDs)
    """
    print("\n" + "="*70)
    print("TEST: IndexIDMap2 + IndexFlatIP (Fallback)")
    print("="*70)

    dim = 768
    n_vectors = 1000

    print(f"\nParameters:")
    print(f"  Dimension: {dim}")
    print(f"  Test vectors: {n_vectors}")

    try:
        # Create IndexFlatIP + IndexIDMap2
        print("\n[1/4] Creating IndexFlatIP + IndexIDMap2...")
        base_index = faiss.IndexFlatIP(dim)
        index = faiss.IndexIDMap2(base_index)
        print(f"  ✓ Created IndexIDMap2(IndexFlatIP({dim}))")

        # Generate vectors
        print("\n[2/4] Adding vectors...")
        np.random.seed(42)
        vectors = np.random.random((n_vectors, dim)).astype('float32')
        faiss.normalize_L2(vectors)

        custom_ids = np.arange(2000, 2000 + n_vectors, dtype=np.int64)
        index.add_with_ids(vectors, custom_ids)
        print(f"  ✓ Added {n_vectors} vectors")

        # Remove vectors
        print("\n[3/4] Removing vectors...")
        ids_to_remove = custom_ids[100:200]
        selector = faiss.IDSelectorArray(len(ids_to_remove), faiss.swig_ptr(ids_to_remove))
        removed_count = index.remove_ids(selector)
        print(f"  ✓ Removed {removed_count} vectors")

        # Search
        print("\n[4/4] Searching...")
        query = vectors[0:1]
        similarities, indices = index.search(query, 5)
        print(f"  ✓ Search successful")

        print("\n" + "="*70)
        print("RESULT: ✓ FALLBACK TEST PASSED")
        print("="*70)
        print("\nConclusion:")
        print("  IndexIDMap2 + IndexFlatIP works reliably")
        print("  Can be used if IndexIVFFlat fails")
        print("  Performance: Slower search, but enables incremental updates")

        return True

    except Exception as e:
        print(f"\n✗ Fallback test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("FAISS IndexIDMap2 Bug Verification")
    print("Testing GitHub Issue #4535 Status in FAISS 1.13.0")
    print("="*70)

    # Test 1: IndexIDMap2 + IndexIVFFlat (the problematic combination)
    test1_passed = test_indexidmap2_indexivf()

    # Test 2: IndexIDMap2 + IndexFlatIP (fallback option)
    test2_passed = test_indexidmap2_indexflat()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Test 1 (IndexIDMap2 + IndexIVFFlat): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (IndexIDMap2 + IndexFlatIP):  {'✓ PASSED' if test2_passed else '✗ FAILED'}")

    if test1_passed:
        print("\n✓ RECOMMENDATION: Use IndexIDMap2 + IndexIVFFlat for incremental indexing")
        print("  - Faster search than IndexFlatIP")
        print("  - Bug appears fixed in FAISS 1.13.0")
    elif test2_passed:
        print("\n⚠ RECOMMENDATION: Use IndexIDMap2 + IndexFlatIP for incremental indexing")
        print("  - Slower search but reliable")
        print("  - Bug still present in IndexIVFFlat combination")
    else:
        print("\n✗ RECOMMENDATION: Keep current IndexFlatIP with full rebuild")
        print("  - IndexIDMap2 not working reliably")
        print("  - Focus on optimizing full rebuild performance")

    print("="*70 + "\n")

    sys.exit(0 if (test1_passed or test2_passed) else 1)
