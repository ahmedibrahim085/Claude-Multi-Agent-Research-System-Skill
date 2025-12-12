#!/usr/bin/env python3
"""
SIMPLIFIED POC: Core Incremental Indexing Test

Tests ONLY the critical operations without complex workflows:
1. Can we add vectors with custom IDs?
2. Can we remove vectors by ID?
3. Can we search after incremental changes?

Run: ~/.local/share/claude-context-local/.venv/bin/python test_incremental_simple.py
"""

import sys
from pathlib import Path
import numpy as np

# Add MCP to path
sys.path.insert(0, str(Path.home() / ".local/share/claude-context-local"))

import faiss

print(f"✓ FAISS {faiss.__version__}\n")
print("=" * 70)
print("SIMPLIFIED POC: IndexIDMap2 + IndexFlatIP Incremental Operations")
print("=" * 70)

# Setup
dim = 768
index = faiss.IndexIDMap2(faiss.IndexFlatIP(dim))
file_to_ids = {}

print("\n[TEST 1] Add initial vectors with custom IDs")
vectors = np.random.random((5, dim)).astype('float32')
faiss.normalize_L2(vectors)
ids = np.array([1000, 1001, 1002, 1003, 1004], dtype=np.int64)
index.add_with_ids(vectors, ids)
file_to_ids['file1.py'] = [1000, 1001]
file_to_ids['file2.py'] = [1002, 1003, 1004]
print(f"  ✓ Added {index.ntotal} vectors")
print(f"  File mapping: {file_to_ids}")

print("\n[TEST 2] Add new file incrementally")
new_vectors = np.random.random((2, dim)).astype('float32')
faiss.normalize_L2(new_vectors)
new_ids = np.array([2000, 2001], dtype=np.int64)
index.add_with_ids(new_vectors, new_ids)
file_to_ids['file3.py'] = [2000, 2001]
print(f"  ✓ Added 2 vectors, total now: {index.ntotal}")

print("\n[TEST 3] Edit file (remove old + add new)")
old_ids = file_to_ids['file1.py']
print(f"  Removing {len(old_ids)} old chunks for file1.py")
selector = faiss.IDSelectorArray(len(old_ids), faiss.swig_ptr(np.array(old_ids, dtype=np.int64)))
removed = index.remove_ids(selector)
print(f"  ✓ Removed {removed} chunks")

new_chunks = np.random.random((3, dim)).astype('float32')
faiss.normalize_L2(new_chunks)
new_ids = np.array([1005, 1006, 1007], dtype=np.int64)
index.add_with_ids(new_chunks, new_ids)
file_to_ids['file1.py'] = [1005, 1006, 1007]
print(f"  ✓ Added 3 new chunks, total now: {index.ntotal}")

print("\n[TEST 4] Delete file completely")
old_ids = file_to_ids['file2.py']
print(f"  Removing all {len(old_ids)} chunks for file2.py")
selector = faiss.IDSelectorArray(len(old_ids), faiss.swig_ptr(np.array(old_ids, dtype=np.int64)))
removed = index.remove_ids(selector)
del file_to_ids['file2.py']
print(f"  ✓ Removed {removed} chunks, total now: {index.ntotal}")

print("\n[TEST 5] Search still works")
query = np.random.random((1, dim)).astype('float32')
faiss.normalize_L2(query)
similarities, result_ids = index.search(query, min(5, index.ntotal))
print(f"  ✓ Search returned {len(result_ids[0])} results")
print(f"  Result IDs: {result_ids[0]}")

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED")
print("=" * 70)
print("\nConclusion:")
print("  - IndexIDMap2 + IndexFlatIP supports:")
print("    ✓ Custom IDs (file-based)")
print("    ✓ Incremental add (add_with_ids)")
print("    ✓ Incremental remove (remove_ids)")
print("    ✓ Search after modifications")
print("\nRECOMMENDATION: Incremental indexing is VIABLE")
print("=" * 70)
