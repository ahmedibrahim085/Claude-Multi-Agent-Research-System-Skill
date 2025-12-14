#!/usr/bin/env python3
"""
Analyze timing breakdowns to find why incremental is not faster
"""

import tempfile
import time
from pathlib import Path
import sys
import shutil

TESTS_DIR = Path(__file__).parent
SCRIPTS_DIR = TESTS_DIR.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from incremental_reindex import FixedIncrementalIndexer


def detailed_timing_analysis():
    """
    Get detailed timing breakdowns for full vs incremental
    """
    project_path = TESTS_DIR.parent.parent.parent.parent

    print("="*70)
    print("DETAILED TIMING ANALYSIS")
    print("="*70)

    # Full reindex
    print("\n1. FULL REINDEX:")
    index_dir = Path.home() / ".claude_code_search" / "projects" / project_path.name / "index"
    if index_dir.exists():
        shutil.rmtree(index_dir)

    indexer1 = FixedIncrementalIndexer(project_path=str(project_path))
    result_full = indexer1.auto_reindex()

    print(f"\n   Total time: {result_full.get('time_taken', 'N/A')}s")
    if 'timing_breakdown' in result_full:
        print("\n   Phase breakdown:")
        total = sum(result_full['timing_breakdown'].values())
        for phase, duration in sorted(result_full['timing_breakdown'].items(), key=lambda x: x[1], reverse=True):
            pct = (duration / total * 100) if total > 0 else 0
            print(f"     {phase:25s}: {duration:7.3f}s ({pct:5.1f}%)")

    # Modify one file
    test_file = list(project_path.rglob("*.py"))[0]
    original_content = test_file.read_text()

    try:
        modified_content = f"# Timing test\n{original_content}"
        test_file.write_text(modified_content)
        time.sleep(0.1)

        # Incremental reindex
        print("\n2. INCREMENTAL REINDEX (1 file changed):")
        indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
        result_inc = indexer2.auto_reindex()

        print(f"\n   Total time: {result_inc.get('time_taken', 'N/A')}s")
        if 'timing_breakdown' in result_inc:
            print("\n   Phase breakdown:")
            total = sum(result_inc['timing_breakdown'].values())
            for phase, duration in sorted(result_inc['timing_breakdown'].items(), key=lambda x: x[1], reverse=True):
                pct = (duration / total * 100) if total > 0 else 0
                print(f"     {phase:25s}: {duration:7.3f}s ({pct:5.1f}%)")

        # Comparison
        print("\n" + "="*70)
        print("COMPARISON:")
        print("="*70)

        if 'timing_breakdown' in result_full and 'timing_breakdown' in result_inc:
            print("\n   Phase               Full (s)    Full %    Inc (s)    Inc %     Diff")
            print("   " + "-"*66)

            all_phases = set(result_full['timing_breakdown'].keys()) | set(result_inc['timing_breakdown'].keys())
            total_full = sum(result_full['timing_breakdown'].values())
            total_inc = sum(result_inc['timing_breakdown'].values())

            for phase in sorted(all_phases):
                full_time = result_full['timing_breakdown'].get(phase, 0)
                inc_time = result_inc['timing_breakdown'].get(phase, 0)
                full_pct = (full_time / total_full * 100) if total_full > 0 else 0
                inc_pct = (inc_time / total_inc * 100) if total_inc > 0 else 0
                diff = inc_time - full_time

                marker = "✓" if diff < 0 else ("✗" if diff > 0.1 else "=")
                print(f"   {marker} {phase:20s} {full_time:7.3f}s  {full_pct:5.1f}%  {inc_time:7.3f}s  {inc_pct:5.1f}%  {diff:+7.3f}s")

            print("   " + "-"*66)
            print(f"     {'TOTAL':20s} {total_full:7.3f}s  100.0%  {total_inc:7.3f}s  100.0%  {total_inc-total_full:+7.3f}s")

        # Analysis
        print("\n" + "="*70)
        print("BOTTLENECK ANALYSIS:")
        print("="*70)

        if 'timing_breakdown' in result_inc:
            embedding_time = result_inc['timing_breakdown'].get('embedding', 0)
            non_embedding_time = sum(v for k, v in result_inc['timing_breakdown'].items() if k != 'embedding')

            print(f"\n   Embedding time:     {embedding_time:.3f}s")
            print(f"   Non-embedding time: {non_embedding_time:.3f}s")
            print(f"   Total:              {embedding_time + non_embedding_time:.3f}s")

            print(f"\n   Embedding is {embedding_time/(embedding_time + non_embedding_time)*100:.1f}% of total")
            print(f"   Overhead is {non_embedding_time/(embedding_time + non_embedding_time)*100:.1f}% of total")

            # Expected savings
            files_full = result_full.get('files_indexed', result_full.get('chunks_added', 0) // 5)
            files_inc = result_inc.get('reembedded_files', 1)

            print(f"\n   Files in full reindex: {files_full}")
            print(f"   Files re-embedded: {files_inc}")
            print(f"   Cache hit rate: {(files_full - files_inc) / files_full * 100:.1f}%")

            # Theoretical speedup
            if 'timing_breakdown' in result_full:
                full_embedding = result_full['timing_breakdown'].get('embedding', 0)
                theoretical_savings = full_embedding * (files_full - files_inc) / files_full
                theoretical_new_time = total_full - theoretical_savings

                print(f"\n   THEORETICAL ANALYSIS:")
                print(f"   Full embedding time: {full_embedding:.3f}s")
                print(f"   Expected savings: {theoretical_savings:.3f}s ({theoretical_savings/full_embedding*100:.1f}% of embedding)")
                print(f"   Theoretical new time: {theoretical_new_time:.3f}s")
                print(f"   Actual incremental time: {total_inc:.3f}s")
                print(f"   Unexplained overhead: {total_inc - theoretical_new_time:.3f}s")

    finally:
        test_file.write_text(original_content)


if __name__ == "__main__":
    detailed_timing_analysis()
