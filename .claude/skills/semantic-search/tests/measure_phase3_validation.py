#!/usr/bin/env python3
"""
Phase 3 Performance Validation - Real-World Benchmarking

Measures actual speedup against conservative targets from the plan:
- Benchmark 1: Single file edit (<10s target, <5s stretch)
- Benchmark 2: 10 file edits (<50s target, <30s stretch)
- Benchmark 3: Rebuild from cache (<30s target, <15s stretch)

Uses REAL project data on this codebase to validate performance claims.
"""

import tempfile
import time
from pathlib import Path
import sys
import shutil

# Add scripts directory to path
TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from incremental_reindex import FixedIncrementalIndexer


def measure_baseline_full_reindex(project_path: Path):
    """
    Measure baseline: full reindex time

    This is the "before" metric - how long a full reindex takes
    without any cache benefits.
    """
    print("\n" + "="*60)
    print("BASELINE: Full Reindex (No Cache)")
    print("="*60)

    # Force full reindex by clearing any existing index
    index_dir = Path.home() / ".claude_code_search" / "projects" / project_path.name / "index"
    if index_dir.exists():
        shutil.rmtree(index_dir)

    start = time.time()
    indexer = FixedIncrementalIndexer(project_path=str(project_path))
    result = indexer.auto_reindex()
    baseline_time = time.time() - start

    print(f"\n✓ Baseline full reindex: {baseline_time:.2f}s")
    print(f"   - Files indexed: {result.get('files_indexed', 'N/A')}")
    print(f"   - Chunks created: {result.get('chunks_added', 'N/A')}")

    return baseline_time, result


def measure_single_file_edit(project_path: Path, baseline_time: float):
    """
    Benchmark 1: Single file edit

    Conservative Target: <10s (25x speedup vs baseline)
    Stretch Goal: <5s (50x speedup)
    Minimum Acceptable: <baseline/2 (2x speedup)
    """
    print("\n" + "="*60)
    print("BENCHMARK 1: Single File Edit")
    print("="*60)

    # Modify one file
    test_file = list(project_path.rglob("*.py"))[0]
    original_content = test_file.read_text()

    try:
        # Add a comment to the file
        modified_content = f"# Modified for benchmark\n{original_content}"
        test_file.write_text(modified_content)
        time.sleep(0.1)  # Ensure timestamp difference

        # Time incremental reindex
        start = time.time()
        indexer = FixedIncrementalIndexer(project_path=str(project_path))
        result = indexer.auto_reindex()
        single_edit_time = time.time() - start

        print(f"\n✓ Single file edit: {single_edit_time:.2f}s")
        print(f"   - Files re-embedded: {result.get('reembedded_files', 0)}")
        print(f"   - Cached files: {result.get('cached_files', 'N/A')}")

        # Calculate speedup
        speedup = baseline_time / single_edit_time if single_edit_time > 0 else 0

        print(f"\n📊 RESULTS:")
        print(f"   - Baseline: {baseline_time:.2f}s")
        print(f"   - With cache: {single_edit_time:.2f}s")
        print(f"   - Speedup: {speedup:.1f}x")

        # Evaluate against targets
        print(f"\n🎯 TARGET EVALUATION:")
        if single_edit_time < 5:
            print(f"   ✅ STRETCH GOAL MET: <5s ({single_edit_time:.2f}s)")
        elif single_edit_time < 10:
            print(f"   ✅ CONSERVATIVE TARGET MET: <10s ({single_edit_time:.2f}s)")
        elif speedup >= 2:
            print(f"   ⚠️  MINIMUM ACCEPTABLE: 2x speedup ({speedup:.1f}x)")
        else:
            print(f"   ❌ FAILED: <2x speedup ({speedup:.1f}x)")

        return single_edit_time, speedup

    finally:
        # Restore original file
        test_file.write_text(original_content)


def measure_ten_file_edits(project_path: Path, baseline_time: float):
    """
    Benchmark 2: 10 file edits

    Conservative Target: <50s (5x speedup vs baseline)
    Stretch Goal: <30s (8x speedup)
    Minimum Acceptable: <baseline/2 (2x speedup)
    """
    print("\n" + "="*60)
    print("BENCHMARK 2: 10 File Edits")
    print("="*60)

    # Select 10 files to modify
    all_files = list(project_path.rglob("*.py"))[:10]
    original_contents = []

    try:
        # Modify 10 files
        for file_path in all_files:
            original_content = file_path.read_text()
            original_contents.append((file_path, original_content))

            modified_content = f"# Benchmark modification\n{original_content}"
            file_path.write_text(modified_content)

        time.sleep(0.1)  # Ensure timestamp difference

        # Time incremental reindex
        start = time.time()
        indexer = FixedIncrementalIndexer(project_path=str(project_path))
        result = indexer.auto_reindex()
        ten_edit_time = time.time() - start

        print(f"\n✓ 10 file edits: {ten_edit_time:.2f}s")
        print(f"   - Files re-embedded: {result.get('reembedded_files', 0)}")
        print(f"   - Cached files: {result.get('cached_files', 'N/A')}")

        # Calculate speedup
        speedup = baseline_time / ten_edit_time if ten_edit_time > 0 else 0

        print(f"\n📊 RESULTS:")
        print(f"   - Baseline: {baseline_time:.2f}s")
        print(f"   - With cache: {ten_edit_time:.2f}s")
        print(f"   - Speedup: {speedup:.1f}x")

        # Evaluate against targets
        print(f"\n🎯 TARGET EVALUATION:")
        if ten_edit_time < 30:
            print(f"   ✅ STRETCH GOAL MET: <30s ({ten_edit_time:.2f}s)")
        elif ten_edit_time < 50:
            print(f"   ✅ CONSERVATIVE TARGET MET: <50s ({ten_edit_time:.2f}s)")
        elif speedup >= 2:
            print(f"   ⚠️  MINIMUM ACCEPTABLE: 2x speedup ({speedup:.1f}x)")
        else:
            print(f"   ❌ FAILED: <2x speedup ({speedup:.1f}x)")

        return ten_edit_time, speedup

    finally:
        # Restore original files
        for file_path, original_content in original_contents:
            file_path.write_text(original_content)


def measure_rebuild_from_cache(project_path: Path, baseline_time: float):
    """
    Benchmark 3: Rebuild from cache

    Conservative Target: <30s (8x speedup vs baseline)
    Stretch Goal: <15s (16x speedup)
    Minimum Acceptable: <baseline/2 (2x speedup)

    This tests the rebuild_from_cache() method which reconstructs
    the index from cached embeddings without re-embedding.
    """
    print("\n" + "="*60)
    print("BENCHMARK 3: Rebuild from Cache")
    print("="*60)

    # First, create some bloat by editing files
    all_files = list(project_path.rglob("*.py"))[:20]
    original_contents = []

    try:
        # Edit 20 files to create ~20% bloat
        for file_path in all_files:
            original_content = file_path.read_text()
            original_contents.append((file_path, original_content))

            modified_content = f"# Bloat generation\n{original_content}"
            file_path.write_text(modified_content)

        time.sleep(0.1)

        # Incremental reindex to create bloat
        indexer = FixedIncrementalIndexer(project_path=str(project_path))
        indexer.auto_reindex()

        # Check bloat
        bloat_stats = indexer.indexer._calculate_bloat()
        print(f"\n   Bloat created: {bloat_stats['bloat_percentage']:.1f}% ({bloat_stats['stale_vectors']} stale)")

        # Time rebuild from cache
        start = time.time()
        indexer.indexer.rebuild_from_cache()
        rebuild_time = time.time() - start

        print(f"\n✓ Rebuild from cache: {rebuild_time:.2f}s")

        # Verify bloat cleared
        bloat_after = indexer.indexer._calculate_bloat()
        print(f"   - Bloat after rebuild: {bloat_after['bloat_percentage']:.1f}%")

        # Calculate speedup
        speedup = baseline_time / rebuild_time if rebuild_time > 0 else 0

        print(f"\n📊 RESULTS:")
        print(f"   - Baseline full reindex: {baseline_time:.2f}s")
        print(f"   - Rebuild from cache: {rebuild_time:.2f}s")
        print(f"   - Speedup: {speedup:.1f}x")

        # Evaluate against targets
        print(f"\n🎯 TARGET EVALUATION:")
        if rebuild_time < 15:
            print(f"   ✅ STRETCH GOAL MET: <15s ({rebuild_time:.2f}s)")
        elif rebuild_time < 30:
            print(f"   ✅ CONSERVATIVE TARGET MET: <30s ({rebuild_time:.2f}s)")
        elif speedup >= 2:
            print(f"   ⚠️  MINIMUM ACCEPTABLE: 2x speedup ({speedup:.1f}x)")
        else:
            print(f"   ❌ FAILED: <2x speedup ({speedup:.1f}x)")

        return rebuild_time, speedup

    finally:
        # Restore original files
        for file_path, original_content in original_contents:
            file_path.write_text(original_content)


def main():
    """Run all Phase 3 performance benchmarks"""
    print("\n" + "="*60)
    print("PHASE 3: PERFORMANCE VALIDATION")
    print("Real-World Benchmarking on Actual Project")
    print("="*60)

    # Use this project as the benchmark target
    project_path = TESTS_DIR.parent.parent.parent.parent

    print(f"\nProject: {project_path}")
    print(f"Python files: {len(list(project_path.rglob('*.py')))}")

    # Baseline: Full reindex
    baseline_time, baseline_result = measure_baseline_full_reindex(project_path)

    # Benchmark 1: Single file edit
    single_time, single_speedup = measure_single_file_edit(project_path, baseline_time)

    # Benchmark 2: 10 file edits
    ten_time, ten_speedup = measure_ten_file_edits(project_path, baseline_time)

    # Benchmark 3: Rebuild from cache
    rebuild_time, rebuild_speedup = measure_rebuild_from_cache(project_path, baseline_time)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY: Phase 3 Performance Results")
    print("="*60)

    print(f"\nBaseline (Full Reindex): {baseline_time:.2f}s")

    print(f"\n📊 Benchmark 1: Single File Edit")
    print(f"   - Time: {single_time:.2f}s")
    print(f"   - Speedup: {single_speedup:.1f}x")
    print(f"   - Status: {'✅ PASSED' if single_speedup >= 2 else '❌ FAILED'}")

    print(f"\n📊 Benchmark 2: 10 File Edits")
    print(f"   - Time: {ten_time:.2f}s")
    print(f"   - Speedup: {ten_speedup:.1f}x")
    print(f"   - Status: {'✅ PASSED' if ten_speedup >= 2 else '❌ FAILED'}")

    print(f"\n📊 Benchmark 3: Rebuild from Cache")
    print(f"   - Time: {rebuild_time:.2f}s")
    print(f"   - Speedup: {rebuild_speedup:.1f}x")
    print(f"   - Status: {'✅ PASSED' if rebuild_speedup >= 2 else '❌ FAILED'}")

    # Go/No-Go decision
    all_passed = all([
        single_speedup >= 2,
        ten_speedup >= 2,
        rebuild_speedup >= 2
    ])

    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL BENCHMARKS PASSED - GO FOR PRODUCTION")
    else:
        print("❌ SOME BENCHMARKS FAILED - NO-GO")
    print("="*60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
