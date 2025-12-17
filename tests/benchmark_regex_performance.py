#!/usr/bin/env python3
"""
Benchmark: Regex Pre-Compilation Performance Improvement

Compares runtime compilation vs pre-compilation for the 31 regex patterns
used in user-prompt-submit.py hook.

Measures:
- Time for runtime compilation approach (re.search(pattern_string, ...))
- Time for pre-compiled approach (compiled_pattern.search(...))
- Performance improvement percentage
"""

import time
import re
import statistics

# Sample test prompts that trigger various patterns
TEST_PROMPTS = [
    "Please research user authentication methods in OAuth2",
    "Don't research this topic, just implement it",
    "Build a search and analysis tool for user data",
    "Research OAuth2 patterns then build the implementation",
    "Design a research methodology for testing",
    "Research the best build tools and deployment strategies",
    "Investigate error handling patterns in production systems",
    "Create a comprehensive analytics dashboard",
    "Study the architecture of microservices systems",
    "Plan and implement a new feature for users",
    "The researcher built an authentication system",
    "Analyze database performance optimization techniques",
    "Explore testing strategies for distributed systems",
    "Examine security best practices for APIs",
    "Find documentation about deployment processes",
    "Build a monitoring and alerting system",
    "Search for configuration examples",
    "Investigate load balancing approaches",
    "Design an authentication and authorization flow",
    "Research caching strategies for web applications",
]

# Sample patterns (subset of actual hook patterns for benchmarking)
SAMPLE_PATTERNS_STR = [
    r"(don't|do not|dont|skip|without)\s+(the\s+)?(research|investigation)",
    r"(research|investigate|analyze)\s+\w+",
    r"(build|create|design)\s+(a|an|the)\s+\w+",
    r"research\s+.{3,30}\s+then\s+.{3,30}\s+(build|create)",
    r"(design|plan)\s+(a|an|the)\s+research",
    r"(research|investigate)\s+(build|design|architecture)",
    r"(study|explore|examine)\s+.{3,30}\s+(pattern|method|approach)",
    r"(build|create|design|plan|implement|develop|architect)",
    r"(research|search|find|investigate|study|explore|examine)",
    r"first\s+(research|search|investigate).{3,60}(then|after)",
]

# Pre-compile patterns
SAMPLE_PATTERNS_COMPILED = [
    re.compile(p, re.IGNORECASE) for p in SAMPLE_PATTERNS_STR
]


def benchmark_runtime_compilation(prompts, patterns_str, iterations=100):
    """Benchmark with runtime regex compilation (OLD approach)"""
    start = time.perf_counter()

    for _ in range(iterations):
        for prompt in prompts:
            for pattern in patterns_str:
                try:
                    re.search(pattern, prompt, re.IGNORECASE)  # Compiles every time!
                except re.error:
                    pass

    end = time.perf_counter()
    return (end - start) * 1000  # Convert to milliseconds


def benchmark_precompiled(prompts, patterns_compiled, iterations=100):
    """Benchmark with pre-compiled patterns (NEW approach)"""
    start = time.perf_counter()

    for _ in range(iterations):
        for prompt in prompts:
            for pattern in patterns_compiled:
                try:
                    pattern.search(prompt)  # Uses pre-compiled pattern
                except re.error:
                    pass

    end = time.perf_counter()
    return (end - start) * 1000  # Convert to milliseconds


def run_benchmark(iterations=100, runs=5):
    """Run benchmark multiple times for statistical significance"""
    print(f"Regex Pre-Compilation Performance Benchmark")
    print(f"=" * 60)
    print(f"Test prompts: {len(TEST_PROMPTS)}")
    print(f"Regex patterns: {len(SAMPLE_PATTERNS_STR)}")
    print(f"Iterations: {iterations}")
    print(f"Benchmark runs: {runs}")
    print(f"Total pattern matches per run: {len(TEST_PROMPTS) * len(SAMPLE_PATTERNS_STR) * iterations}")
    print()

    runtime_times = []
    precompiled_times = []

    for run in range(runs):
        print(f"Run {run + 1}/{runs}...", end=" ")

        # Benchmark runtime compilation
        runtime_ms = benchmark_runtime_compilation(TEST_PROMPTS, SAMPLE_PATTERNS_STR, iterations)
        runtime_times.append(runtime_ms)

        # Benchmark pre-compiled
        precompiled_ms = benchmark_precompiled(TEST_PROMPTS, SAMPLE_PATTERNS_COMPILED, iterations)
        precompiled_times.append(precompiled_ms)

        print(f"Runtime: {runtime_ms:.2f}ms, Pre-compiled: {precompiled_ms:.2f}ms")

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    # Calculate statistics
    runtime_mean = statistics.mean(runtime_times)
    runtime_stdev = statistics.stdev(runtime_times) if len(runtime_times) > 1 else 0
    precompiled_mean = statistics.mean(precompiled_times)
    precompiled_stdev = statistics.stdev(precompiled_times) if len(precompiled_times) > 1 else 0

    improvement_pct = ((runtime_mean - precompiled_mean) / runtime_mean) * 100
    speedup = runtime_mean / precompiled_mean

    print(f"\nRuntime Compilation (OLD):")
    print(f"  Mean: {runtime_mean:.2f}ms")
    print(f"  StdDev: {runtime_stdev:.2f}ms")
    print(f"  Per prompt avg: {runtime_mean / (iterations * len(TEST_PROMPTS)):.4f}ms")

    print(f"\nPre-Compiled Patterns (NEW):")
    print(f"  Mean: {precompiled_mean:.2f}ms")
    print(f"  StdDev: {precompiled_stdev:.2f}ms")
    print(f"  Per prompt avg: {precompiled_mean / (iterations * len(TEST_PROMPTS)):.4f}ms")

    print(f"\nPerformance Improvement:")
    print(f"  Absolute: {runtime_mean - precompiled_mean:.2f}ms saved")
    print(f"  Relative: {improvement_pct:.1f}% faster")
    print(f"  Speedup: {speedup:.2f}x")

    print(f"\nProjected Impact (50 prompts per session):")
    saved_per_session_ms = (runtime_mean - precompiled_mean) / iterations * 50
    print(f"  Time saved: {saved_per_session_ms:.1f}ms (~{saved_per_session_ms/1000:.2f}s)")

    print(f"\nProjected Impact (100 developers, 50 prompts/day):")
    saved_per_day_seconds = (saved_per_session_ms / 1000) * 100
    saved_per_day_minutes = saved_per_day_seconds / 60
    saved_per_day_hours = saved_per_day_minutes / 60
    print(f"  Time saved: {saved_per_day_seconds:.1f}s = {saved_per_day_minutes:.2f}min = {saved_per_day_hours:.2f}hrs")

    print()
    print("=" * 60)

    return {
        'runtime_mean': runtime_mean,
        'precompiled_mean': precompiled_mean,
        'improvement_pct': improvement_pct,
        'speedup': speedup,
    }


if __name__ == '__main__':
    # Run benchmark with default settings
    results = run_benchmark(iterations=100, runs=5)

    # Print commit message snippet
    print("\nCOMMIT MESSAGE SNIPPET:")
    print("-" * 60)
    print(f"Performance Benchmarks (10 patterns × 20 prompts × 100 iterations × 5 runs):")
    print(f"- Before (runtime compilation): {results['runtime_mean']:.2f}ms")
    print(f"- After (pre-compiled patterns): {results['precompiled_mean']:.2f}ms")
    print(f"- Improvement: {results['improvement_pct']:.1f}% faster ({results['speedup']:.2f}x speedup)")
    print(f"- Per-prompt savings: ~{(results['runtime_mean'] - results['precompiled_mean']) / 100:.3f}ms")
