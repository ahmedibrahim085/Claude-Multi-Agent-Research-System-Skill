#!/usr/bin/env python3
"""
Performance measurement for embedding cache.

Validates assumptions:
- Cache significantly speeds up reindex operations
- Rebuild from cache achieves target speedup (8x minimum)
- Cache hit rates are high (>90%)

Usage:
    python measure_cache_performance.py [project_path]

Example:
    python measure_cache_performance.py /path/to/project
"""

import sys
import time
import json
from pathlib import Path

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

try:
    from incremental_reindex import FixedCodeIndexManager, FixedIncrementalIndexer
except ImportError as e:
    print(json.dumps({
        'success': False,
        'error': f'Failed to import dependencies: {e}',
        'hint': 'Run from .claude/skills/semantic-search/scripts/ directory'
    }, indent=2), file=sys.stderr)
    sys.exit(1)


def measure_full_reindex(project_path: str) -> dict:
    """
    Measure full reindex time (baseline).

    This clears the cache and index, then performs a complete reindex
    from scratch (re-embedding all chunks).

    Returns:
        dict: {
            'time_seconds': float,
            'total_chunks': int,
            'cache_size_before': int,
            'cache_size_after': int
        }
    """
    print("\n" + "="*60)
    print("MEASURING: Full Reindex (Baseline)")
    print("="*60)

    indexer = FixedIncrementalIndexer(project_path)

    # Get cache size before (should be 0 after clear)
    cache_size_before = len(indexer.indexer.embedding_cache)

    # Perform full reindex
    start_time = time.time()
    result = indexer.auto_reindex(force_full=True)
    elapsed = time.time() - start_time

    if not result.get('success'):
        raise RuntimeError(f"Full reindex failed: {result.get('error')}")

    # Get cache size after
    cache_size_after = len(indexer.indexer.embedding_cache)
    total_chunks = indexer.indexer.get_index_size()

    print(f"✅ Full reindex complete: {elapsed:.2f}s")
    print(f"   Total chunks: {total_chunks}")
    print(f"   Cache: {cache_size_before} → {cache_size_after} embeddings")

    return {
        'time_seconds': round(elapsed, 2),
        'total_chunks': total_chunks,
        'cache_size_before': cache_size_before,
        'cache_size_after': cache_size_after,
        'chunks_per_second': round(total_chunks / elapsed, 2) if elapsed > 0 else 0
    }


def measure_rebuild_from_cache(project_path: str) -> dict:
    """
    Measure rebuild from cache time (cache hit).

    This rebuilds the FAISS index from cached embeddings without
    re-embedding. Tests the core cache speedup hypothesis.

    Returns:
        dict: {
            'time_seconds': float,
            'total_chunks': int,
            'cache_hits': int,
            'cache_hit_rate': float
        }
    """
    print("\n" + "="*60)
    print("MEASURING: Rebuild From Cache")
    print("="*60)

    manager = FixedCodeIndexManager(project_path)

    # Verify cache exists
    cache_size = len(manager.embedding_cache)
    total_chunks = manager.get_index_size()

    if cache_size == 0:
        raise RuntimeError("No cache found - run full reindex first")

    print(f"Cache status: {cache_size} embeddings cached")
    print(f"Index status: {total_chunks} chunks in index")

    # Measure rebuild time
    start_time = time.time()
    manager.rebuild_from_cache()
    elapsed = time.time() - start_time

    # Calculate cache hit rate
    cache_hit_rate = (cache_size / total_chunks * 100) if total_chunks > 0 else 0

    print(f"✅ Rebuild complete: {elapsed:.2f}s")
    print(f"   Cache hits: {cache_size}/{total_chunks} ({cache_hit_rate:.1f}%)")

    return {
        'time_seconds': round(elapsed, 2),
        'total_chunks': total_chunks,
        'cache_hits': cache_size,
        'cache_hit_rate': round(cache_hit_rate, 1),
        'chunks_per_second': round(total_chunks / elapsed, 2) if elapsed > 0 else 0
    }


def calculate_speedup(baseline: dict, cached: dict) -> dict:
    """
    Calculate speedup metrics.

    Args:
        baseline: Full reindex results
        cached: Rebuild from cache results

    Returns:
        dict: {
            'speedup_factor': float,
            'time_saved': float,
            'time_saved_percentage': float,
            'meets_target': bool
        }
    """
    baseline_time = baseline['time_seconds']
    cached_time = cached['time_seconds']

    speedup = baseline_time / cached_time if cached_time > 0 else 0
    time_saved = baseline_time - cached_time
    time_saved_pct = (time_saved / baseline_time * 100) if baseline_time > 0 else 0

    # Target: 8x speedup for rebuild from cache
    TARGET_SPEEDUP = 8.0
    meets_target = speedup >= TARGET_SPEEDUP

    return {
        'baseline_time': baseline_time,
        'cached_time': cached_time,
        'speedup_factor': round(speedup, 2),
        'time_saved': round(time_saved, 2),
        'time_saved_percentage': round(time_saved_pct, 1),
        'target_speedup': TARGET_SPEEDUP,
        'meets_target': meets_target
    }


def print_summary(full_results: dict, cache_results: dict, speedup: dict):
    """
    Print formatted summary of performance measurements.
    """
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)

    print(f"\n📊 BASELINE (Full Reindex):")
    print(f"   Time: {full_results['time_seconds']}s")
    print(f"   Chunks: {full_results['total_chunks']}")
    print(f"   Throughput: {full_results['chunks_per_second']} chunks/s")

    print(f"\n⚡ CACHED (Rebuild from Cache):")
    print(f"   Time: {cache_results['time_seconds']}s")
    print(f"   Chunks: {cache_results['total_chunks']}")
    print(f"   Cache hit rate: {cache_results['cache_hit_rate']}%")
    print(f"   Throughput: {cache_results['chunks_per_second']} chunks/s")

    print(f"\n🚀 SPEEDUP:")
    print(f"   Speedup factor: {speedup['speedup_factor']}x")
    print(f"   Time saved: {speedup['time_saved']}s ({speedup['time_saved_percentage']}%)")
    print(f"   Target speedup: {speedup['target_speedup']}x")

    if speedup['meets_target']:
        print(f"   ✅ MEETS TARGET ({speedup['speedup_factor']}x >= {speedup['target_speedup']}x)")
    else:
        print(f"   ❌ BELOW TARGET ({speedup['speedup_factor']}x < {speedup['target_speedup']}x)")

    print("\n" + "="*60)


def main():
    if len(sys.argv) < 2:
        project_path = Path.cwd()
        print(f"No project path specified, using current directory: {project_path}")
    else:
        project_path = Path(sys.argv[1]).resolve()

    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Measuring performance for: {project_path}")
    print(f"This will take several minutes...\n")

    try:
        # Step 1: Measure full reindex (baseline)
        full_results = measure_full_reindex(str(project_path))

        # Step 2: Measure rebuild from cache
        cache_results = measure_rebuild_from_cache(str(project_path))

        # Step 3: Calculate speedup
        speedup = calculate_speedup(full_results, cache_results)

        # Step 4: Print summary
        print_summary(full_results, cache_results, speedup)

        # Step 5: Save results to JSON
        results = {
            'project_path': str(project_path),
            'full_reindex': full_results,
            'rebuild_from_cache': cache_results,
            'speedup': speedup,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        }

        output_file = Path.cwd() / 'cache_performance_results.json'
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: {output_file}")

        # Exit code based on target met
        sys.exit(0 if speedup['meets_target'] else 1)

    except Exception as e:
        print(f"\nError during performance measurement: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
