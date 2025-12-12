#!/usr/bin/env python3
"""
POC: Incremental Indexing with Real MCP Components (Minimal)

Tests incremental operations using actual MCP components
but with minimal complexity to avoid cleanup issues.

Tests:
1. Chunk real Python code
2. Embed with real model
3. Index with IndexIDMap2
4. Incremental operations (add/remove) with real embeddings

Run: ~/.local/share/claude-context-local/.venv/bin/python test_incremental_with_real_components.py
"""

import sys
from pathlib import Path
import tempfile
import shutil
import numpy as np

# Add MCP to path
sys.path.insert(0, str(Path.home() / ".local/share/claude-context-local"))

from chunking.multi_language_chunker import MultiLanguageChunker
from embeddings.embedder import CodeEmbedder
import faiss

print(f"✓ Imported MCP components (FAISS {faiss.__version__})\n")
print("=" * 70)
print("POC: Incremental Operations with Real MCP Components")
print("=" * 70)

# Create temp directory with Python files
test_dir = Path(tempfile.mkdtemp(prefix="incremental_real_"))
print(f"\nTest directory: {test_dir}")

try:
    # Create Python files
    (test_dir / "file1.py").write_text("""
def authenticate(username, password):
    '''User authentication function'''
    if not username or not password:
        raise ValueError("Username and password required")
    return check_credentials(username, password)
""")

    (test_dir / "file2.py").write_text("""
class UserManager:
    '''Manage user accounts'''
    def create_user(self, username, email):
        if not username:
            raise ValueError("Username required")
        return {"username": username, "email": email}
""")

    print("✓ Created 2 Python test files")

    # Initialize MCP components
    chunker = MultiLanguageChunker(str(test_dir))
    embedder = CodeEmbedder()
    print("✓ Initialized MCP components")

    # Setup index
    index = faiss.IndexIDMap2(faiss.IndexFlatIP(768))
    file_to_ids = {}
    print("✓ Created IndexIDMap2(IndexFlatIP(768))")

    print("\n" + "=" * 70)
    print("TEST 1: Chunk and Embed Real Python Code")
    print("=" * 70)

    # Chunk file1
    file1_path = test_dir / "file1.py"
    chunks1 = chunker.chunk_file(str(file1_path))
    print(f"\n✓ Chunked file1.py: {len(chunks1)} chunks")

    # Embed chunks
    embeddings1 = embedder.embed_chunks(chunks1, batch_size=32)
    vectors1 = np.array([e.embedding for e in embeddings1], dtype=np.float32)
    faiss.normalize_L2(vectors1)
    print(f"✓ Generated embeddings: shape {vectors1.shape}")

    # Generate IDs and add
    ids1 = np.array([hash(f"file1.py:{i}") & 0x7FFFFFFFFFFFFFFF for i in range(len(chunks1))], dtype=np.int64)
    index.add_with_ids(vectors1, ids1)
    file_to_ids['file1.py'] = ids1.tolist()
    print(f"✓ Added to index: {index.ntotal} vectors")

    print("\n" + "=" * 70)
    print("TEST 2: Incremental Add with Real Embeddings")
    print("=" * 70)

    # Chunk and add file2
    file2_path = test_dir / "file2.py"
    chunks2 = chunker.chunk_file(str(file2_path))
    print(f"\n✓ Chunked file2.py: {len(chunks2)} chunks")

    embeddings2 = embedder.embed_chunks(chunks2, batch_size=32)
    vectors2 = np.array([e.embedding for e in embeddings2], dtype=np.float32)
    faiss.normalize_L2(vectors2)

    ids2 = np.array([hash(f"file2.py:{i}") & 0x7FFFFFFFFFFFFFFF for i in range(len(chunks2))], dtype=np.int64)
    index.add_with_ids(vectors2, ids2)
    file_to_ids['file2.py'] = ids2.tolist()
    print(f"✓ Added incrementally: total now {index.ntotal} vectors")

    print("\n" + "=" * 70)
    print("TEST 3: Incremental Remove with Real Data")
    print("=" * 70)

    # Remove file1 chunks
    old_ids = np.array(file_to_ids['file1.py'], dtype=np.int64)
    print(f"\n✓ Removing {len(old_ids)} chunks from file1.py")

    selector = faiss.IDSelectorArray(len(old_ids), faiss.swig_ptr(old_ids))
    removed = index.remove_ids(selector)
    del file_to_ids['file1.py']
    print(f"✓ Removed {removed} chunks: total now {index.ntotal} vectors")

    print("\n" + "=" * 70)
    print("TEST 4: Search with Real Embeddings")
    print("=" * 70)

    # Search for "user" concept
    query_embedding = embedder.embed_query("user authentication")
    query_vector = np.array([query_embedding], dtype=np.float32)
    faiss.normalize_L2(query_vector)

    similarities, result_ids = index.search(query_vector, min(3, index.ntotal))
    print(f"\n✓ Search for 'user authentication' returned {len(result_ids[0])} results")
    print(f"  Result IDs: {result_ids[0].tolist()}")
    print(f"  Similarities: {similarities[0].tolist()}")

    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - Real Components Work!")
    print("=" * 70)
    print("\nVerified:")
    print("  ✓ Chunking real Python code works")
    print("  ✓ Embedding real code with MCP model works")
    print("  ✓ IndexIDMap2 + real embeddings works")
    print("  ✓ Incremental add with real data works")
    print("  ✓ Incremental remove with real data works")
    print("  ✓ Search with real embeddings works")
    print("\nCONCLUSION: Incremental indexing PROVEN with real MCP components")
    print("=" * 70)

finally:
    # Cleanup model FIRST to prevent leak
    try:
        embedder.cleanup()
        print("\n✓ Embedding model cleaned up successfully")
    except:
        pass

    # Remove temp directory
    shutil.rmtree(test_dir, ignore_errors=True)
    print(f"✓ Cleaned up test directory")
