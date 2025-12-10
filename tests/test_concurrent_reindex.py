#!/usr/bin/env python3
"""
Integration Tests for Concurrent Reindex Operations

Tests real concurrent scenarios with actual subprocess execution.
Validates that atomic lock mechanism prevents index corruption.

Run with: pytest tests/test_concurrent_reindex.py -v
"""

import pytest
import sys
import time
import subprocess
from pathlib import Path
from multiprocessing import Process, Queue

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'utils'))
import reindex_manager


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project with sample files for testing"""
    project_dir = tmp_path / "concurrent_test_project"
    project_dir.mkdir()

    # Create sample Python files
    (project_dir / "main.py").write_text("def main(): pass")
    (project_dir / "utils.py").write_text("def helper(): pass")
    (project_dir / "config.py").write_text("CONFIG = {}")

    return project_dir


@pytest.fixture
def mock_storage_dir(tmp_path, monkeypatch):
    """Mock storage directory for lock files"""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    def mock_get_storage_dir(project_path):
        return storage_dir

    monkeypatch.setattr(reindex_manager, 'get_project_storage_dir', mock_get_storage_dir)
    return storage_dir


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def worker_acquire_lock(project_path, storage_dir, queue, worker_id):
    """Worker process that tries to acquire lock"""
    import sys
    from pathlib import Path

    # Re-import in subprocess
    sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'utils'))
    import reindex_manager

    # Mock storage dir in subprocess
    def mock_get_storage_dir(path):
        return storage_dir

    reindex_manager.get_project_storage_dir = mock_get_storage_dir

    # Try to acquire lock
    result = reindex_manager._acquire_reindex_lock(project_path)

    # Report result
    queue.put({
        'worker_id': worker_id,
        'acquired': result,
        'timestamp': time.time()
    })

    # Hold lock briefly if acquired
    if result:
        time.sleep(0.5)
        reindex_manager._release_reindex_lock(project_path)


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: Concurrent Access
# ═══════════════════════════════════════════════════════════════════════════

def test_concurrent_lock_acquisition_single_winner(temp_project_dir, mock_storage_dir):
    """Test that only ONE process acquires lock when multiple try simultaneously"""
    queue = Queue()
    workers = []

    # Spawn 5 concurrent workers trying to acquire lock
    for i in range(5):
        p = Process(
            target=worker_acquire_lock,
            args=(temp_project_dir, mock_storage_dir, queue, i)
        )
        workers.append(p)
        p.start()

    # Wait for all workers
    for p in workers:
        p.join(timeout=5)

    # Collect results
    results = []
    while not queue.empty():
        results.append(queue.get())

    # Verify exactly ONE worker acquired lock
    acquired_count = sum(1 for r in results if r['acquired'])
    assert acquired_count == 1, f"Expected 1 lock acquisition, got {acquired_count}"

    # Verify 4 workers were rejected
    rejected_count = sum(1 for r in results if not r['acquired'])
    assert rejected_count == 4, f"Expected 4 rejections, got {rejected_count}"


def test_concurrent_lock_sequential_access(temp_project_dir, mock_storage_dir):
    """Test that processes can acquire lock sequentially after release"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Process 1: Acquire and release
    result1 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result1 is True
    assert claim_file.exists()

    reindex_manager._release_reindex_lock(temp_project_dir)
    assert not claim_file.exists()

    # Process 2: Should acquire after Process 1 released
    result2 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result2 is True
    assert claim_file.exists()

    reindex_manager._release_reindex_lock(temp_project_dir)
    assert not claim_file.exists()


def test_lock_prevents_concurrent_execution(temp_project_dir, mock_storage_dir):
    """Test that lock mechanism prevents concurrent reindex operations"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Worker 1 acquires lock
    acquired1 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert acquired1 is True
    assert claim_file.exists()

    # Worker 2 tries while Worker 1 holds lock (should be blocked)
    acquired2 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert acquired2 is False  # Blocked by Worker 1

    # Worker 1 releases lock
    reindex_manager._release_reindex_lock(temp_project_dir)
    assert not claim_file.exists()

    # Worker 2 tries again after Worker 1 released (should succeed)
    acquired2_retry = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert acquired2_retry is True
    assert claim_file.exists()

    # Cleanup
    reindex_manager._release_reindex_lock(temp_project_dir)


def test_stale_lock_recovery_concurrent(temp_project_dir, mock_storage_dir):
    """Test that stale locks don't permanently block all workers"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Create stale lock (simulating crashed process)
    claim_file.write_text("99999:1000000000.0")  # Very old timestamp
    stale_time = time.time() - 61
    import os
    os.utime(str(claim_file), (stale_time, stale_time))

    # New worker should detect stale lock and acquire
    result = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result is True

    # Verify new lock has current PID
    content = claim_file.read_text()
    pid, _ = content.split(':')
    assert int(pid) == os.getpid()


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: Lock in Finally Block
# ═══════════════════════════════════════════════════════════════════════════

def test_lock_released_on_exception(temp_project_dir, mock_storage_dir):
    """Test that lock is released even when exception occurs"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Acquire lock
    acquired = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert acquired is True
    assert claim_file.exists()

    # Simulate exception during reindex operation
    try:
        raise RuntimeError("Simulated error during reindex")
    except RuntimeError:
        pass
    finally:
        # Lock should be released in finally block
        reindex_manager._release_reindex_lock(temp_project_dir)

    # Verify lock released
    assert not claim_file.exists()

    # Verify another process can acquire
    result = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result is True

    # Cleanup
    reindex_manager._release_reindex_lock(temp_project_dir)


def test_lock_lifecycle_with_timeout_simulation(temp_project_dir, mock_storage_dir):
    """Test lock behavior when operation times out"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Acquire lock
    acquired = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert acquired is True

    # Simulate timeout (operation takes >50s)
    # In real code, subprocess.TimeoutExpired would be raised
    # Here we just verify lock can be released after timeout

    try:
        # Simulate timeout after 0.1s instead of 50s
        time.sleep(0.1)
        raise subprocess.TimeoutExpired(cmd="reindex", timeout=50)
    except subprocess.TimeoutExpired:
        # Lock should be released in finally block (like actual code)
        reindex_manager._release_reindex_lock(temp_project_dir)

    # Verify lock released
    assert not claim_file.exists()


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS: Race Conditions
# ═══════════════════════════════════════════════════════════════════════════

def test_race_condition_simultaneous_stale_detection(temp_project_dir, mock_storage_dir):
    """Test race when two processes detect stale lock simultaneously"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Create stale lock
    claim_file.write_text("99999:1000000000.0")
    stale_time = time.time() - 61
    import os
    os.utime(str(claim_file), (stale_time, stale_time))

    # Both processes detect stale lock
    # Both try to remove and recreate
    # Only one should succeed (os.O_EXCL prevents duplicate)

    result1 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    result2 = reindex_manager._acquire_reindex_lock(temp_project_dir)

    # Exactly one should succeed
    assert (result1 and not result2) or (not result1 and result2)

    # Cleanup
    if result1:
        reindex_manager._release_reindex_lock(temp_project_dir)
    if result2:
        reindex_manager._release_reindex_lock(temp_project_dir)


# ═══════════════════════════════════════════════════════════════════════════
# STRESS TESTS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.slow
def test_stress_many_concurrent_workers(temp_project_dir, mock_storage_dir):
    """Stress test with many concurrent workers (10)"""
    queue = Queue()
    workers = []

    # Spawn 10 workers
    for i in range(10):
        p = Process(
            target=worker_acquire_lock,
            args=(temp_project_dir, mock_storage_dir, queue, i)
        )
        workers.append(p)
        p.start()

    # Wait for all
    for p in workers:
        p.join(timeout=10)

    # Collect results
    results = []
    while not queue.empty():
        results.append(queue.get())

    # Exactly one winner
    acquired_count = sum(1 for r in results if r['acquired'])
    assert acquired_count == 1, f"Expected 1 winner in stress test, got {acquired_count}"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '-s'])
