#!/usr/bin/env python3
"""
Measure REAL production incremental reindex performance.

This script validates that incremental reindex is ACTUALLY faster
than full reindex by measuring real-world scenarios.

CRITICAL: This measures the PRODUCTION code path (auto_reindex),
not theoretical performance.
"""

import sys
import time
import shutil
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from incremental_reindex import FixedIncrementalIndexer


def measure_baseline(project_path: Path):
    """Measure full reindex time (baseline)"""
    print("\n" + "=" * 60)
    print("BASELINE: Full Reindex Performance")
    print("=" * 60)

    # Clear any existing index
    indexer = FixedIncrementalIndexer(project_path=str(project_path))
    if indexer.indexer.index_dir.exists():
        shutil.rmtree(indexer.indexer.index_dir)

    # Measure full reindex
    start = time.time()
    result = indexer.auto_reindex(force_full=True)
    elapsed = time.time() - start

    print(f"\nBaseline Results:")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Chunks: {result.get('chunks_added', 0)}")
    print(f"  Files: {result.get('files_indexed', 0)}")

    return {
        'time': elapsed,
        'chunks': result.get('chunks_added', 0),
        'files': result.get('files_indexed', 0)
    }


def measure_incremental_single_file(project_path: Path):
    """Measure incremental reindex after modifying one file"""
    print("\n" + "=" * 60)
    print("SCENARIO 1: Single File Modified")
    print("=" * 60)

    # Initial index
    indexer = FixedIncrementalIndexer(project_path=str(project_path))
    result1 = indexer.auto_reindex()

    total_files = result1.get('files_indexed', 0)
    print(f"\nInitial index: {total_files} files indexed")

    # Find a Python file to modify
    py_files = list(project_path.rglob("*.py"))
    if not py_files:
        print("ERROR: No Python files found!")
        return None

    target_file = py_files[0]
    print(f"Modifying: {target_file.relative_to(project_path)}")

    # Modify the file
    original_content = target_file.read_text()
    target_file.write_text(original_content + "\n# Modified for testing\n")

    # Measure incremental reindex
    start = time.time()
    indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
    result2 = indexer2.auto_reindex()
    elapsed = time.time() - start

    # Restore original content
    target_file.write_text(original_content)

    # Verify incremental was used
    if not result2.get('incremental'):
        print("\nWARNING: Incremental path was NOT used!")
        print(f"Result: {result2}")
        return None

    print(f"\nIncremental Results:")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Re-embedded files: {result2.get('reembedded_files', 0)}")
    print(f"  Cached files: {result2.get('cached_files', 0)}")
    print(f"  Chunks added: {result2.get('chunks_added', 0)}")

    return {
        'time': elapsed,
        'reembedded_files': result2.get('reembedded_files', 0),
        'cached_files': result2.get('cached_files', 0)
    }


def measure_incremental_no_changes(project_path: Path):
    """Measure incremental reindex when no files changed"""
    print("\n" + "=" * 60)
    print("SCENARIO 2: No Changes (Skip)")
    print("=" * 60)

    # Ensure index exists
    indexer = FixedIncrementalIndexer(project_path=str(project_path))
    result1 = indexer.auto_reindex()

    # Measure with no changes
    start = time.time()
    indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
    result2 = indexer2.auto_reindex()
    elapsed = time.time() - start

    # Should either skip or do incremental with 0 files
    if result2.get('skipped'):
        print(f"\n✓ Skipped (no changes detected)")
        print(f"  Time: {elapsed:.2f}s")
    elif result2.get('incremental') and result2.get('reembedded_files') == 0:
        print(f"\n✓ Incremental with 0 files (metadata changes only)")
        print(f"  Time: {elapsed:.2f}s")
    else:
        print(f"\nWARNING: Unexpected behavior: {result2}")

    return {'time': elapsed}


def main():
    """Main measurement workflow"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Measure REAL incremental reindex performance'
    )
    parser.add_argument('project_path', help='Path to project directory')

    args = parser.parse_args()
    project_path = Path(args.project_path).resolve()

    if not project_path.exists():
        print(f"ERROR: Project path does not exist: {project_path}")
        sys.exit(1)

    print("=" * 60)
    print("INCREMENTAL REINDEX PERFORMANCE MEASUREMENT")
    print("=" * 60)
    print(f"\nProject: {project_path}")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Scenario 1: Baseline (full reindex)
    baseline = measure_baseline(project_path)

    # Scenario 2: Single file modified
    incremental = measure_incremental_single_file(project_path)

    # Scenario 3: No changes
    no_changes = measure_incremental_no_changes(project_path)

    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)

    if baseline and incremental:
        speedup = baseline['time'] / incremental['time'] if incremental['time'] > 0 else float('inf')

        print(f"\nBaseline (full reindex):")
        print(f"  Time: {baseline['time']:.2f}s")
        print(f"  Files: {baseline['files']}")
        print(f"  Chunks: {baseline['chunks']}")

        print(f"\nIncremental (1 file changed):")
        print(f"  Time: {incremental['time']:.2f}s")
        print(f"  Re-embedded: {incremental['reembedded_files']} files")
        print(f"  Cached: {incremental['cached_files']} files")
        print(f"  Speedup: {speedup:.1f}x")

        print(f"\nNo changes:")
        print(f"  Time: {no_changes['time']:.2f}s")

        # Verdict
        print("\n" + "=" * 60)
        if speedup > 1.5:
            print("✅ VERDICT: Incremental reindex provides MEASURABLE speedup")
            print(f"   {speedup:.1f}x faster than full reindex")
        elif speedup > 1.0:
            print("⚠️  VERDICT: Incremental reindex is faster, but modest gain")
            print(f"   {speedup:.1f}x faster (may be due to small project size)")
        else:
            print("❌ VERDICT: Incremental reindex is NOT faster")
            print(f"   {speedup:.1f}x (REGRESSION!)")

        return 0 if speedup > 1.0 else 1

    else:
        print("\n❌ MEASUREMENT FAILED - Could not collect data")
        return 1


if __name__ == "__main__":
    sys.exit(main())
