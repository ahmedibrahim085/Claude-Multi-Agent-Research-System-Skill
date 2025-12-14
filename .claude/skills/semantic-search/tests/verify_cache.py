#!/usr/bin/env python3
"""Verify the embedding cache file integrity and contents."""

import pickle
from pathlib import Path

# Find the cache file
cache_dir = Path.home() / ".claude_code_search" / "projects"
cache_files = list(cache_dir.glob("Claude-Multi-Agent-Research-System-Skill_*/index/embeddings.pkl"))

if not cache_files:
    print("ERROR: No cache file found")
    exit(1)

cache_file = cache_files[0]
print(f"Cache file: {cache_file}")
print(f"File size: {cache_file.stat().st_size / (1024*1024):.2f} MB")

# Load the cache
with open(cache_file, 'rb') as f:
    cache = pickle.load(f)

print(f"\nCache type: {type(cache)}")
print(f"Number of cached embeddings: {len(cache)}")

# Verify cache structure
if cache:
    # Get first item
    first_key = next(iter(cache.keys()))
    first_value = cache[first_key]

    print(f"\nSample chunk_id: {first_key}")
    print(f"Embedding type: {type(first_value)}")
    print(f"Embedding shape: {first_value.shape}")
    print(f"Embedding dtype: {first_value.dtype}")

    # Calculate expected size
    expected_size = len(cache) * 768 * 4  # 10009 chunks * 768 dims * 4 bytes per float32
    print(f"\nExpected cache size: {expected_size / (1024*1024):.2f} MB (without pickle overhead)")
    print(f"Actual cache size: {cache_file.stat().st_size / (1024*1024):.2f} MB")

    # Verify all embeddings have correct shape
    print("\nVerifying all embeddings...")
    invalid_count = 0
    for chunk_id, embedding in cache.items():
        if embedding.shape != (768,) or embedding.dtype != 'float32':
            print(f"  INVALID: {chunk_id} - shape={embedding.shape}, dtype={embedding.dtype}")
            invalid_count += 1

    if invalid_count == 0:
        print(f"✅ All {len(cache)} embeddings are valid (768-dim float32)")
    else:
        print(f"❌ Found {invalid_count} invalid embeddings")

print("\n✅ Cache verification complete!")
