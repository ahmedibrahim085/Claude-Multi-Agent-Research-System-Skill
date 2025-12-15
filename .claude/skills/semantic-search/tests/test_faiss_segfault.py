#!/usr/bin/env python3
"""
Minimal test to reproduce FAISS segmentation fault on Apple Silicon.
Tests various approaches to see which one works.
"""

import os
# Disable ALL parallelism to prevent Apple Silicon MPS + multiprocessing crashes
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import sys
from pathlib import Path
import numpy as np
import faiss

# Add MCP to path
sys.path.insert(0, str(Path.home() / ".local/share/claude-context-local"))

from embeddings.embedder import CodeEmbedder
from chunking.multi_language_chunker import MultiLanguageChunker

def test_basic_faiss():
    """Test 1: Basic FAISS with random vectors"""
    print("\n=== Test 1: Basic FAISS with random vectors ===")
    idx = faiss.IndexFlatIP(768)
    vectors = np.random.rand(100, 768).astype('float32')
    faiss.normalize_L2(vectors)
    idx.add(vectors)
    print(f"✅ SUCCESS: Added {idx.ntotal} vectors")
    assert idx.ntotal == 100, f"Expected 100 vectors, got {idx.ntotal}"

def test_mcp_embedder_single_chunk():
    """Test 2: Single chunk through MCP embedder"""
    print("\n=== Test 2: Single chunk through MCP embedder ===")
    # Create a simple test file
    test_file = Path("/tmp/test_embed.py")
    test_file.write_text("def hello():\n    print('world')\n")

    try:
        # Chunk and embed
        chunker = MultiLanguageChunker(str(test_file.parent))
        chunks = chunker.chunk_file(str(test_file))

        assert chunks, "No chunks created"

        embedder = CodeEmbedder()
        results = embedder.embed_chunks([chunks[0]], batch_size=1)

        assert results, "No embeddings generated"

        # Try to add to FAISS
        idx = faiss.IndexFlatIP(768)
        embedding = results[0].embedding

        print(f"Embedding type: {type(embedding)}")
        print(f"Embedding dtype: {embedding.dtype}")
        print(f"Embedding shape: {embedding.shape}")
        print(f"Is C-contiguous: {embedding.flags['C_CONTIGUOUS']}")

        # Convert to proper format
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        idx.add(vector)

        print(f"✅ SUCCESS: Added {idx.ntotal} vectors")
        assert idx.ntotal == 1, f"Expected 1 vector, got {idx.ntotal}"
    finally:
        if test_file.exists():
            test_file.unlink()

def test_mcp_embedder_multiple_chunks():
    """Test 3: Multiple chunks through MCP embedder"""
    print("\n=== Test 3: Multiple chunks through MCP embedder ===")
    # Create a test file with multiple functions
    test_file = Path("/tmp/test_embed_multi.py")
    test_file.write_text("""
def func1():
    print('one')

def func2():
    print('two')

def func3():
    print('three')
""")

    try:
        # Chunk and embed
        chunker = MultiLanguageChunker(str(test_file.parent))
        chunks = chunker.chunk_file(str(test_file))

        print(f"Created {len(chunks)} chunks")

        embedder = CodeEmbedder()
        results = embedder.embed_chunks(chunks, batch_size=64)

        print(f"Generated {len(results)} embeddings")

        # Try to add to FAISS
        idx = faiss.IndexFlatIP(768)

        # Method 1: Direct array conversion (like our code)
        print("\nMethod 1: Direct np.array conversion")
        embeddings = np.array([r.embedding for r in results], dtype=np.float32)
        print(f"Embeddings shape: {embeddings.shape}")
        print(f"Embeddings dtype: {embeddings.dtype}")
        print(f"Is C-contiguous: {embeddings.flags['C_CONTIGUOUS']}")

        # Apply our Apple Silicon fix
        embeddings = np.ascontiguousarray(embeddings.copy())
        print(f"After ascontiguousarray: C-contiguous={embeddings.flags['C_CONTIGUOUS']}")

        faiss.normalize_L2(embeddings)
        idx.add(embeddings)

        print(f"✅ SUCCESS: Added {idx.ntotal} vectors")
        assert idx.ntotal == len(results), f"Expected {len(results)} vectors, got {idx.ntotal}"
    finally:
        if test_file.exists():
            test_file.unlink()

def test_cpu_conversion():
    """Test 4: Explicit CPU conversion of embeddings"""
    print("\n=== Test 4: Explicit CPU conversion ===")
    # Create a test file
    test_file = Path("/tmp/test_cpu.py")
    test_file.write_text("def hello():\n    print('world')\n")

    try:
        # Chunk and embed
        chunker = MultiLanguageChunker(str(test_file.parent))
        chunks = chunker.chunk_file(str(test_file))

        embedder = CodeEmbedder()
        results = embedder.embed_chunks(chunks, batch_size=1)

        # Try to add to FAISS with explicit CPU conversion
        idx = faiss.IndexFlatIP(768)
        embedding = results[0].embedding

        # Check if it's a torch tensor (it shouldn't be, but let's check)
        print(f"Embedding type: {type(embedding)}")

        # If it's a torch tensor, convert to numpy
        if hasattr(embedding, 'cpu'):
            print("Converting from torch tensor to numpy...")
            embedding = embedding.cpu().numpy()

        # Ensure numpy array
        embedding = np.asarray(embedding, dtype=np.float32)

        # Ensure on CPU (not MPS)
        if hasattr(embedding, 'device'):
            print(f"Embedding device: {embedding.device}")

        # Make it C-contiguous
        embedding = np.ascontiguousarray(embedding)

        # Add to FAISS
        vector = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vector)
        idx.add(vector)

        print(f"✅ SUCCESS: Added {idx.ntotal} vectors")
        assert idx.ntotal == 1, f"Expected 1 vector, got {idx.ntotal}"
    finally:
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    print("Testing FAISS segmentation fault scenarios on Apple Silicon")
    print("=" * 70)

    results = {
        "Basic FAISS": test_basic_faiss(),
        "Single chunk": test_mcp_embedder_single_chunk(),
        "Multiple chunks": test_mcp_embedder_multiple_chunks(),
        "CPU conversion": test_cpu_conversion(),
    }

    print("\n" + "=" * 70)
    print("SUMMARY:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")

    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)
