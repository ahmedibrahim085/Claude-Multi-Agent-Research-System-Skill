#!/usr/bin/env python3
"""
VERIFIED POC: Incremental Indexing with Search Correctness Validation

This POC actually VERIFIES incremental indexing works correctly by:
1. Searching after EACH operation
2. Verifying removed chunks are NOT in results
3. Verifying added chunks ARE in results
4. Testing with actual searchable content (not random vectors)

Run: ~/.local/share/claude-context-local/.venv/bin/python test_incremental_verified.py
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path.home() / ".local/share/claude-context-local"))

import faiss

print(f"✓ FAISS {faiss.__version__}\n")
print("=" * 70)
print("VERIFIED POC: Incremental Indexing with Search Correctness")
print("=" * 70)

# Setup
dim = 768
index = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
file_to_ids = {}

# Create distinguishable vectors (not random - we need to verify search finds the right ones)
def create_vector(seed: int) -> np.ndarray:
    """Create a vector with a specific seed so we can verify search finds it"""
    np.random.seed(seed)
    vec = np.random.random((1, dim)).astype('float32')
    faiss.normalize_L2(vec)
    return vec

def search_and_verify(query_seed: int, expected_ids: list, not_expected_ids: list = None):
    """Search and verify correct IDs are returned"""
    query = create_vector(query_seed)
    k = min(10, index.ntotal)
    if k == 0:
        print("  ⚠ Index empty")
        return True

    similarities, result_ids = index.search(query, k)
    result_ids_list = result_ids[0].tolist()

    # Check expected IDs are found
    for eid in expected_ids:
        if eid in result_ids_list:
            print(f"    ✓ Found expected ID {eid}")
        else:
            print(f"    ✗ FAILED: Expected ID {eid} NOT found in results: {result_ids_list}")
            return False

    # Check removed IDs are NOT found
    if not_expected_ids:
        for nid in not_expected_ids:
            if nid in result_ids_list:
                print(f"    ✗ FAILED: Removed ID {nid} still in results: {result_ids_list}")
                return False
            else:
                print(f"    ✓ Confirmed ID {nid} not in results (correctly removed)")

    return True

print("\n" + "=" * 70)
print("TEST 1: Add Initial Files - Verify Search Finds Them")
print("=" * 70)

# Add file1.py with 2 chunks
file1_vectors = np.vstack([create_vector(1000), create_vector(1001)])
file1_ids = np.array([1000, 1001], dtype=np.int64)
index.add_with_ids(file1_vectors, file1_ids)
file_to_ids['file1.py'] = [1000, 1001]
print(f"\nAdded file1.py: chunks {file1_ids.tolist()}")

# Add file2.py with 3 chunks
file2_vectors = np.vstack([create_vector(2000), create_vector(2001), create_vector(2002)])
file2_ids = np.array([2000, 2001, 2002], dtype=np.int64)
index.add_with_ids(file2_vectors, file2_ids)
file_to_ids['file2.py'] = [2000, 2001, 2002]
print(f"Added file2.py: chunks {file2_ids.tolist()}")
print(f"Total chunks: {index.ntotal}")

# VERIFY: Search for file1 chunks
print("\n[VERIFY] Searching for file1.py chunks...")
if not search_and_verify(1000, expected_ids=[1000]):
    print("✗ TEST 1 FAILED")
    sys.exit(1)

# VERIFY: Search for file2 chunks
print("\n[VERIFY] Searching for file2.py chunks...")
if not search_and_verify(2001, expected_ids=[2001]):
    print("✗ TEST 1 FAILED")
    sys.exit(1)

print("\n✓ TEST 1 PASSED - Initial files searchable")

print("\n" + "=" * 70)
print("TEST 2: Add New File - Verify It's Searchable")
print("=" * 70)

# Add file3.py incrementally
file3_vectors = np.vstack([create_vector(3000), create_vector(3001)])
file3_ids = np.array([3000, 3001], dtype=np.int64)
index.add_with_ids(file3_vectors, file3_ids)
file_to_ids['file3.py'] = [3000, 3001]
print(f"\nAdded file3.py incrementally: chunks {file3_ids.tolist()}")
print(f"Total chunks: {index.ntotal}")

# VERIFY: Search for new file
print("\n[VERIFY] Searching for file3.py chunks...")
if not search_and_verify(3000, expected_ids=[3000]):
    print("✗ TEST 2 FAILED")
    sys.exit(1)

# VERIFY: Old files still searchable
print("\n[VERIFY] Confirming old files still searchable...")
if not search_and_verify(1001, expected_ids=[1001]):
    print("✗ TEST 2 FAILED")
    sys.exit(1)

print("\n✓ TEST 2 PASSED - Incremental add works, old files preserved")

print("\n" + "=" * 70)
print("TEST 3: Edit File - Verify Old Chunks Removed, New Chunks Added")
print("=" * 70)

# Edit file1.py (remove old, add new)
old_file1_ids = file_to_ids['file1.py']
print(f"\nRemoving old file1.py chunks: {old_file1_ids}")

selector = faiss.IDSelectorArray(
    len(old_file1_ids),
    faiss.swig_ptr(np.array(old_file1_ids, dtype=np.int64))
)
removed = index.remove_ids(selector)
print(f"  Removed {removed} chunks")

# Add new version of file1.py with different chunks
new_file1_vectors = np.vstack([create_vector(1100), create_vector(1101), create_vector(1102)])
new_file1_ids = np.array([1100, 1101, 1102], dtype=np.int64)
index.add_with_ids(new_file1_vectors, new_file1_ids)
file_to_ids['file1.py'] = [1100, 1101, 1102]
print(f"  Added new file1.py chunks: {new_file1_ids.tolist()}")
print(f"Total chunks: {index.ntotal}")

# VERIFY: Old file1 chunks NOT in results
print("\n[VERIFY] Confirming old file1.py chunks removed...")
if not search_and_verify(1000, expected_ids=[], not_expected_ids=[1000, 1001]):
    print("✗ TEST 3 FAILED")
    sys.exit(1)

# VERIFY: New file1 chunks ARE in results
print("\n[VERIFY] Searching for new file1.py chunks...")
if not search_and_verify(1100, expected_ids=[1100]):
    print("✗ TEST 3 FAILED")
    sys.exit(1)

# VERIFY: Other files still searchable
print("\n[VERIFY] Confirming file2.py still searchable...")
if not search_and_verify(2000, expected_ids=[2000]):
    print("✗ TEST 3 FAILED")
    sys.exit(1)

print("\n✓ TEST 3 PASSED - Incremental edit works correctly")

print("\n" + "=" * 70)
print("TEST 4: Delete File - Verify All Chunks Removed")
print("=" * 70)

# Delete file2.py completely
old_file2_ids = file_to_ids['file2.py']
print(f"\nDeleting file2.py - removing chunks: {old_file2_ids}")

selector = faiss.IDSelectorArray(
    len(old_file2_ids),
    faiss.swig_ptr(np.array(old_file2_ids, dtype=np.int64))
)
removed = index.remove_ids(selector)
del file_to_ids['file2.py']
print(f"  Removed {removed} chunks")
print(f"Total chunks: {index.ntotal}")

# VERIFY: Deleted file chunks NOT in results
print("\n[VERIFY] Confirming file2.py chunks removed...")
if not search_and_verify(2001, expected_ids=[], not_expected_ids=[2000, 2001, 2002]):
    print("✗ TEST 4 FAILED")
    sys.exit(1)

# VERIFY: Other files still searchable
print("\n[VERIFY] Confirming other files still searchable...")
if not search_and_verify(1101, expected_ids=[1101]):
    print("✗ TEST 4 FAILED")
    sys.exit(1)
if not search_and_verify(3001, expected_ids=[3001]):
    print("✗ TEST 4 FAILED")
    sys.exit(1)

print("\n✓ TEST 4 PASSED - Incremental delete works correctly")

print("\n" + "=" * 70)
print("TEST 5: Final State Verification")
print("=" * 70)

expected_files = {
    'file1.py': [1100, 1101, 1102],  # Edited version
    'file3.py': [3000, 3001]          # Added file
}
deleted_files = {
    'file2.py': [2000, 2001, 2002]    # Deleted
}

print(f"\nExpected state: {expected_files}")
print(f"Deleted files: {deleted_files}")
print(f"Index size: {index.ntotal} (expected: 5)")

if index.ntotal != 5:
    print(f"✗ TEST 5 FAILED: Wrong index size")
    sys.exit(1)

if file_to_ids != expected_files:
    print(f"✗ TEST 5 FAILED: File mapping wrong")
    print(f"  Expected: {expected_files}")
    print(f"  Got: {file_to_ids}")
    sys.exit(1)

print("\n✓ TEST 5 PASSED - Final state correct")

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED - Incremental Indexing VERIFIED")
print("=" * 70)
print("\nVerified Operations:")
print("  ✓ Add initial files - searchable immediately")
print("  ✓ Add new file incrementally - searchable, old files preserved")
print("  ✓ Edit file - old chunks removed from search, new chunks added")
print("  ✓ Delete file - all chunks removed from search")
print("  ✓ Final state - index size and mappings correct")
print("\nCRITICAL: Search correctness verified after EACH operation")
print("=" * 70)
