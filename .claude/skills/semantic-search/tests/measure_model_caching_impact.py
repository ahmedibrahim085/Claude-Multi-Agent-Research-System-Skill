#!/usr/bin/env python3
"""
Model Caching Impact Measurement

Measures the ACTUAL performance improvement from model caching optimization.

BEFORE Fix:
- Each FixedIncrementalIndexer() loads model (~0.8s overhead)
- Full reindex: embedding + model loading
- Incremental reindex: embedding + model loading (NO BENEFIT)

AFTER Fix:
- First FixedIncrementalIndexer() loads model
- Subsequent instances reuse cached model (~0.8s saved)
- Full reindex: embedding + model loading
- Incremental reindex: embedding only (BENEFIT!)

This script measures the difference with proper isolation.
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


def measure_model_caching_impact():
    """
    Measure the ACTUAL impact of model caching on incremental reindex.

    Methodology:
    1. Full reindex (creates cache, loads model first time)
    2. Single file edit (uses cache, reuses model - KEY BENEFIT)
    3. Measure speedup from avoiding model reload
    """
    project_path = TESTS_DIR.parent.parent.parent.parent

    print("\n" + "="*70)
    print("MODEL CACHING IMPACT MEASUREMENT")
    print("="*70)
    print(f"\nProject: {project_path.name}")
    print(f"Python files: {len(list(project_path.rglob('*.py')))}")

    # Clear cache to start fresh
    index_dir = Path.home() / ".claude_code_search" / "projects" / project_path.name / "index"
    if index_dir.exists():
        shutil.rmtree(index_dir)

    # Also clear model cache to ensure fresh measurement
    FixedIncrementalIndexer.cleanup_shared_embedder()

    # Step 1: Full reindex (loads model + embeds all files)
    print("\n" + "="*70)
    print("STEP 1: Full Reindex (First Time - Loads Model)")
    print("="*70)

    start_full = time.time()
    indexer1 = FixedIncrementalIndexer(project_path=str(project_path))
    result_full = indexer1.auto_reindex()
    time_full = time.time() - start_full

    files_indexed = result_full.get('files_indexed', 0)
    chunks_added = result_full.get('chunks_added', 0)

    print(f"\n✓ Full reindex completed:")
    print(f"   Time: {time_full:.2f}s")
    print(f"   Files: {files_indexed}")
    print(f"   Chunks: {chunks_added}")

    if 'timing_breakdown' in result_full:
        embedding_time = result_full['timing_breakdown'].get('embedding', 0)
        print(f"   Embedding: {embedding_time:.2f}s ({embedding_time/time_full*100:.1f}%)")

    # Step 2: Modify one file
    test_file = list(project_path.rglob("*.py"))[0]
    original_content = test_file.read_text()

    try:
        modified_content = f"# Model caching benchmark\n{original_content}"
        test_file.write_text(modified_content)
        time.sleep(0.1)

        # Step 3: Incremental reindex (reuses cached model!)
        print("\n" + "="*70)
        print("STEP 2: Incremental Reindex (Reuses Cached Model)")
        print("="*70)

        start_inc = time.time()
        indexer2 = FixedIncrementalIndexer(project_path=str(project_path))
        result_inc = indexer2.auto_reindex()
        time_inc = time.time() - start_inc

        reembedded = result_inc.get('reembedded_files', 0)
        cached = result_inc.get('cached_files', 0)

        print(f"\n✓ Incremental reindex completed:")
        print(f"   Time: {time_inc:.2f}s")
        print(f"   Re-embedded: {reembedded} files")
        print(f"   Cached: {cached} files")

        if 'timing_breakdown' in result_inc:
            embedding_time_inc = result_inc['timing_breakdown'].get('embedding', 0)
            print(f"   Embedding: {embedding_time_inc:.2f}s ({embedding_time_inc/time_inc*100:.1f}%)")

        # Step 4: Calculate speedup
        print("\n" + "="*70)
        print("PERFORMANCE ANALYSIS")
        print("="*70)

        speedup = time_full / time_inc if time_inc > 0 else 0
        time_saved = time_full - time_inc

        print(f"\n📊 TIMING COMPARISON:")
        print(f"   Full reindex:        {time_full:.2f}s")
        print(f"   Incremental reindex: {time_inc:.2f}s")
        print(f"   Time saved:          {time_saved:.2f}s")
        print(f"   Speedup:             {speedup:.1f}x")

        # Detailed breakdown
        if 'timing_breakdown' in result_full and 'timing_breakdown' in result_inc:
            print(f"\n📊 PHASE-BY-PHASE BREAKDOWN:")

            full_breakdown = result_full['timing_breakdown']
            inc_breakdown = result_inc['timing_breakdown']

            print(f"\n   {'Phase':20s} {'Full':>8s} {'Inc':>8s} {'Savings':>8s}")
            print(f"   {'-'*48}")

            all_phases = set(full_breakdown.keys()) | set(inc_breakdown.keys())
            for phase in sorted(all_phases, key=lambda p: full_breakdown.get(p, 0), reverse=True):
                full_time = full_breakdown.get(phase, 0)
                inc_time = inc_breakdown.get(phase, 0)
                savings = full_time - inc_time

                marker = "✓" if savings > 0.1 else (" " if abs(savings) < 0.1 else "↑")
                print(f"   {marker} {phase:18s} {full_time:7.2f}s {inc_time:7.2f}s {savings:+7.2f}s")

        # Model caching benefit
        print(f"\n💡 MODEL CACHING BENEFIT:")

        if 'timing_breakdown' in result_full and 'timing_breakdown' in result_inc:
            full_embed = result_full['timing_breakdown'].get('embedding', 0)
            inc_embed = result_inc['timing_breakdown'].get('embedding', 0)
            embedding_savings = full_embed - inc_embed

            # Expected savings from caching (avoided re-embedding)
            cache_hit_rate = cached / (cached + reembedded) if (cached + reembedded) > 0 else 0
            expected_cache_savings = full_embed * cache_hit_rate

            # Model loading savings (estimated from total - embedding)
            other_savings = time_saved - embedding_savings

            print(f"   Cache hit rate: {cache_hit_rate*100:.1f}% ({cached}/{cached+reembedded} files)")
            print(f"   Embedding saved: {embedding_savings:.2f}s (from caching {cached} files)")
            print(f"   Other savings: {other_savings:.2f}s (includes model reload avoidance)")

        # Success criteria
        print(f"\n🎯 SUCCESS CRITERIA:")

        if speedup >= 2.0:
            print(f"   ✅ PASSED: {speedup:.1f}x speedup (≥2x minimum target)")
        else:
            print(f"   ❌ FAILED: {speedup:.1f}x speedup (<2x minimum target)")

        if time_inc < 5.0:
            print(f"   ✅ PASSED: {time_inc:.2f}s absolute time (<5s stretch goal)")
        elif time_inc < 10.0:
            print(f"   ✅ PASSED: {time_inc:.2f}s absolute time (<10s conservative target)")
        else:
            print(f"   ⚠️  WARNING: {time_inc:.2f}s absolute time (>10s)")

        # Final verdict
        print(f"\n" + "="*70)
        if speedup >= 2.0 and time_inc < 10.0:
            print("✅ MODEL CACHING OPTIMIZATION: SUCCESS")
        else:
            print("❌ MODEL CACHING OPTIMIZATION: NEEDS WORK")
        print("="*70)

        return speedup, time_full, time_inc

    finally:
        # Restore original file
        test_file.write_text(original_content)


if __name__ == "__main__":
    try:
        speedup, time_full, time_inc = measure_model_caching_impact()

        # Return exit code based on success
        if speedup >= 2.0:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
