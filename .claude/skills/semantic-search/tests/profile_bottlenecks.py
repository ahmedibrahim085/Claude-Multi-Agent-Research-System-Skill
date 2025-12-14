#!/usr/bin/env python3
"""
Detailed Profiling to Find ACTUAL Bottlenecks

This script profiles incremental reindex operations to identify
where time is ACTUALLY spent, not where we THINK it's spent.

Evidence-based performance analysis.
"""

import tempfile
import time
from pathlib import Path
import sys
import shutil
import cProfile
import pstats
import io

# Add scripts directory to path
TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from incremental_reindex import FixedIncrementalIndexer


def profile_single_file_edit(project_path: Path):
    """
    Profile a single file edit with detailed timing breakdown
    """
    print("\n" + "="*60)
    print("PROFILING: Single File Edit (Detailed Breakdown)")
    print("="*60)

    # Initial full index
    print("\n1. Creating baseline (full index)...")
    index_dir = Path.home() / ".claude_code_search" / "projects" / project_path.name / "index"
    if index_dir.exists():
        shutil.rmtree(index_dir)

    indexer1 = FixedIncrementalIndexer(project_path=str(project_path))
    indexer1.auto_reindex()

    # Modify one file
    test_file = list(project_path.rglob("*.py"))[0]
    original_content = test_file.read_text()

    try:
        modified_content = f"# Profile test\n{original_content}"
        test_file.write_text(modified_content)
        time.sleep(0.1)

        # Profile the incremental reindex
        print("\n2. Profiling incremental reindex...")

        profiler = cProfile.Profile()
        profiler.enable()

        start = time.time()
        indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
        result = indexer2.auto_reindex()
        total_time = time.time() - start

        profiler.disable()

        # Print detailed timing from result
        if 'timings' in result:
            print("\n📊 TIMING BREAKDOWN (from result dict):")
            timings = result['timings']
            for phase, duration in sorted(timings.items(), key=lambda x: x[1], reverse=True):
                percentage = (duration / total_time * 100) if total_time > 0 else 0
                print(f"   {phase:20s}: {duration:6.3f}s ({percentage:5.1f}%)")
            print(f"   {'TOTAL':20s}: {total_time:6.3f}s (100.0%)")

        # Print top 20 function calls
        print("\n📊 TOP 20 FUNCTION CALLS (by cumulative time):")
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)

        # Filter output to show only relevant lines
        for line in s.getvalue().split('\n'):
            if 'incremental_reindex' in line or 'embed' in line or 'chunk' in line or 'faiss' in line:
                print(f"   {line}")

        return total_time, result

    finally:
        test_file.write_text(original_content)


def profile_full_vs_incremental(project_path: Path):
    """
    Compare full reindex vs incremental with detailed breakdown
    """
    print("\n" + "="*60)
    print("COMPARISON: Full Reindex vs Incremental (Same Project)")
    print("="*60)

    # Full reindex (baseline)
    print("\n1. Full reindex (baseline)...")
    index_dir = Path.home() / ".claude_code_search" / "projects" / project_path.name / "index"
    if index_dir.exists():
        shutil.rmtree(index_dir)

    start_full = time.time()
    indexer1 = FixedIncrementalIndexer(project_path=str(project_path))
    result_full = indexer1.auto_reindex()
    time_full = time.time() - start_full

    print(f"   Full reindex: {time_full:.2f}s")
    if 'timings' in result_full:
        print("   Breakdown:")
        for phase, duration in sorted(result_full['timings'].items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / time_full * 100) if time_full > 0 else 0
            print(f"     {phase:20s}: {duration:6.3f}s ({percentage:5.1f}%)")

    # Modify one file
    test_file = list(project_path.rglob("*.py"))[0]
    original_content = test_file.read_text()

    try:
        modified_content = f"# Comparison test\n{original_content}"
        test_file.write_text(modified_content)
        time.sleep(0.1)

        # Incremental reindex
        print("\n2. Incremental reindex (1 file modified)...")
        start_inc = time.time()
        indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
        result_inc = indexer2.auto_reindex()
        time_inc = time.time() - start_inc

        print(f"   Incremental reindex: {time_inc:.2f}s")
        if 'timings' in result_inc:
            print("   Breakdown:")
            for phase, duration in sorted(result_inc['timings'].items(), key=lambda x: x[1], reverse=True):
                percentage = (duration / time_inc * 100) if time_inc > 0 else 0
                print(f"     {phase:20s}: {duration:6.3f}s ({percentage:5.1f}%)")

        # Analysis
        print("\n📊 ANALYSIS:")
        print(f"   Full reindex: {time_full:.2f}s")
        print(f"   Incremental:  {time_inc:.2f}s")
        speedup = time_full / time_inc if time_inc > 0 else 0
        print(f"   Speedup:      {speedup:.2f}x")

        # Identify bottlenecks
        print("\n🔍 BOTTLENECK ANALYSIS:")

        # Compare phase timings
        if 'timings' in result_full and 'timings' in result_inc:
            full_timings = result_full['timings']
            inc_timings = result_inc['timings']

            print("\n   Phase-by-phase comparison (Full vs Incremental):")
            all_phases = set(full_timings.keys()) | set(inc_timings.keys())
            for phase in sorted(all_phases):
                full_time = full_timings.get(phase, 0)
                inc_time = inc_timings.get(phase, 0)

                full_pct = (full_time / time_full * 100) if time_full > 0 else 0
                inc_pct = (inc_time / time_inc * 100) if time_inc > 0 else 0

                print(f"   {phase:20s}: {full_time:6.3f}s ({full_pct:5.1f}%) → {inc_time:6.3f}s ({inc_pct:5.1f}%)")

        # Calculate overhead
        if 'timings' in result_inc:
            embedding_time = result_inc['timings'].get('embedding', 0)
            overhead = time_inc - embedding_time
            overhead_pct = (overhead / time_inc * 100) if time_inc > 0 else 0

            print(f"\n   Embedding time: {embedding_time:.3f}s")
            print(f"   Overhead time:  {overhead:.3f}s ({overhead_pct:.1f}%)")
            print(f"   Total time:     {time_inc:.3f}s")

            print("\n   ⚠️ OVERHEAD BREAKDOWN:")
            for phase, duration in result_inc['timings'].items():
                if phase != 'embedding':
                    pct = (duration / overhead * 100) if overhead > 0 else 0
                    print(f"     {phase:20s}: {duration:6.3f}s ({pct:5.1f}% of overhead)")

        return time_full, time_inc, speedup

    finally:
        test_file.write_text(original_content)


def measure_cache_overhead():
    """
    Measure ACTUAL cache overhead (file I/O, path resolution, etc)
    """
    print("\n" + "="*60)
    print("MEASURING: Cache Overhead Components")
    print("="*60)

    project_path = TESTS_DIR.parent.parent.parent.parent

    # Create a test project with known characteristics
    with tempfile.TemporaryDirectory() as tmpdir:
        test_project = Path(tmpdir) / "overhead_test"
        test_project.mkdir()

        # Create 10 files
        for i in range(10):
            (test_project / f"file{i}.py").write_text(f"def func{i}(): return {i}\n" * 5)

        # Full index
        indexer = FixedIncrementalIndexer(project_path=str(test_project))
        indexer.auto_reindex()

        # Measure cache save time
        print("\n1. Cache save time...")
        cache_entries = len(indexer.indexer.embedding_cache)

        start = time.time()
        indexer.indexer._save_cache()
        save_time = time.time() - start

        print(f"   Saved {cache_entries} embeddings in {save_time:.3f}s")
        print(f"   Per-embedding: {save_time/cache_entries*1000:.3f}ms")

        # Measure cache load time
        print("\n2. Cache load time...")

        start = time.time()
        indexer2 = FixedIncrementalIndexer(project_path=str(test_project))
        load_time = time.time() - start

        print(f"   Loaded {len(indexer2.indexer.embedding_cache)} embeddings in {load_time:.3f}s")
        print(f"   Per-embedding: {load_time/cache_entries*1000:.3f}ms")

        # Measure Merkle DAG overhead
        print("\n3. Merkle DAG change detection...")

        # Modify one file
        (test_project / "file0.py").write_text("# Modified\ndef func0(): return 0\n" * 5)
        time.sleep(0.1)

        start = time.time()
        # Just build DAG, don't reindex
        from chunking.merkle_dag import MerkleDAG
        dag = MerkleDAG(str(test_project))
        dag.build()
        changes = dag.detect_changes()
        dag_time = time.time() - start

        print(f"   DAG built and changes detected in {dag_time:.3f}s")
        print(f"   Modified files: {len(changes.modified)}")

        print("\n📊 CACHE OVERHEAD SUMMARY:")
        total_overhead = save_time + load_time + dag_time
        print(f"   Cache save:  {save_time:.3f}s ({save_time/total_overhead*100:.1f}%)")
        print(f"   Cache load:  {load_time:.3f}s ({load_time/total_overhead*100:.1f}%)")
        print(f"   Merkle DAG:  {dag_time:.3f}s ({dag_time/total_overhead*100:.1f}%)")
        print(f"   TOTAL:       {total_overhead:.3f}s")


def main():
    """Run all profiling analyses"""
    print("\n" + "="*60)
    print("EVIDENCE-BASED BOTTLENECK ANALYSIS")
    print("="*60)

    project_path = TESTS_DIR.parent.parent.parent.parent

    # 1. Profile single file edit
    single_time, single_result = profile_single_file_edit(project_path)

    # 2. Full vs Incremental comparison
    full_time, inc_time, speedup = profile_full_vs_incremental(project_path)

    # 3. Cache overhead breakdown
    measure_cache_overhead()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY: Where the Time Actually Goes")
    print("="*60)

    print(f"\nProject: {len(list(project_path.rglob('*.py')))} Python files")
    print(f"Full reindex: {full_time:.2f}s")
    print(f"Incremental (1 file): {inc_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")

    print("\n💡 KEY FINDINGS:")
    if speedup < 2:
        print(f"   ⚠️ Speedup below 2x target ({speedup:.2f}x)")
        print(f"   Possible reasons:")
        print(f"   - Small project (cache overhead > embedding savings)")
        print(f"   - Embedding time already fast (~1-2s)")
        print(f"   - Fixed overheads (DAG, I/O) become dominant")


if __name__ == "__main__":
    main()
