#!/usr/bin/env python3
"""
Performance measurement for fast-fail optimization
EVIDENCE-BASED VALIDATION - Measure, don't assume

This script measures actual performance of:
1. Fast-fail path (3/4+ heuristics pass, skip Merkle DAG)
2. Full validation path (< 3/4 heuristics pass, build Merkle DAG)

Target: Fast-fail < 200ms (vs 1,700ms Merkle DAG baseline)
"""

import sys
import time
import json
from pathlib import Path

# Add scripts to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts'))

from incremental_reindex import FixedIncrementalIndexer


def measure_fast_fail_path(iterations=5):
    """
    Measure fast-fail path performance (no file changes)
    Should skip Merkle DAG build and return in <200ms
    """
    print("=" * 80)
    print("TEST 1: FAST-FAIL PATH (No Changes - Should Skip)")
    print("=" * 80)
    print(f"Running {iterations} iterations...\n")

    reindexer = FixedIncrementalIndexer(project_path=project_root)
    timings = []

    for i in range(iterations):
        start = time.time()
        result = reindexer.auto_reindex(force_full=False)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        timings.append(elapsed)

        status = "SKIP" if result.get('skipped') else "PROCEED"
        fast_fail = "✓ Fast-fail" if result.get('fast_fail') else "✗ No fast-fail"

        print(f"  Run {i+1}: {elapsed:6.1f}ms - {status} - {fast_fail}")
        if result.get('heuristics'):
            h = result['heuristics']
            print(f"         Heuristics: git={h.get('git_clean')}, "
                  f"snapshot={h.get('snapshot_recent')}, "
                  f"filecount={h.get('file_count_stable')}, "
                  f"cache={h.get('cache_synced')}")

    avg = sum(timings) / len(timings)
    min_time = min(timings)
    max_time = max(timings)

    print(f"\nResults:")
    print(f"  Average: {avg:6.1f}ms")
    print(f"  Min:     {min_time:6.1f}ms")
    print(f"  Max:     {max_time:6.1f}ms")
    print(f"  Target:  < 200ms")
    print(f"  Status:  {'✓ PASS' if avg < 200 else '✗ FAIL'}")

    return {
        'timings': timings,
        'average_ms': avg,
        'min_ms': min_time,
        'max_ms': max_time,
        'target_ms': 200,
        'passes': avg < 200
    }


def measure_full_validation_path(iterations=3):
    """
    Measure full validation path (force full rebuild)
    Should build Merkle DAG (slower, but still reasonable)
    """
    print("\n" + "=" * 80)
    print("TEST 2: FULL VALIDATION PATH (Force Full - Should Build DAG)")
    print("=" * 80)
    print(f"Running {iterations} iterations...\n")

    reindexer = FixedIncrementalIndexer(project_path=project_root)
    timings = []

    for i in range(iterations):
        start = time.time()
        result = reindexer.auto_reindex(force_full=True)
        elapsed = (time.time() - start) * 1000  # Convert to ms

        timings.append(elapsed)

        status = "SKIP" if result.get('skipped') else "PROCEED"

        print(f"  Run {i+1}: {elapsed:6.1f}ms - {status}")

    avg = sum(timings) / len(timings)
    min_time = min(timings)
    max_time = max(timings)

    print(f"\nResults:")
    print(f"  Average: {avg:6.1f}ms")
    print(f"  Min:     {min_time:6.1f}ms")
    print(f"  Max:     {max_time:6.1f}ms")
    print(f"  Note: Full validation includes Merkle DAG build (~1.5s baseline)")

    return {
        'timings': timings,
        'average_ms': avg,
        'min_ms': min_time,
        'max_ms': max_time,
    }


def main():
    """Run performance measurements and save results"""
    print("\nFAST-FAIL OPTIMIZATION - PERFORMANCE MEASUREMENT")
    print("Evidence-based validation (measure, don't assume)")
    print(f"Project: {project_root.name}")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Measure both paths
    fast_fail_results = measure_fast_fail_path(iterations=5)
    full_validation_results = measure_full_validation_path(iterations=3)

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Fast-fail path:      {fast_fail_results['average_ms']:6.1f}ms avg (target < 200ms)")
    print(f"Full validation:     {full_validation_results['average_ms']:6.1f}ms avg")
    print(f"Speedup ratio:       {full_validation_results['average_ms'] / fast_fail_results['average_ms']:.1f}x")
    print(f"\nOverall status:      {'✓ PASS' if fast_fail_results['passes'] else '✗ FAIL'}")

    # Save detailed results
    results_file = project_root / 'tests' / 'fast_fail_performance_results.json'
    results = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'project_path': str(project_root),
        'fast_fail_path': fast_fail_results,
        'full_validation_path': full_validation_results,
        'speedup_ratio': full_validation_results['average_ms'] / fast_fail_results['average_ms']
    }

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    return 0 if fast_fail_results['passes'] else 1


if __name__ == '__main__':
    sys.exit(main())
