#!/usr/bin/env python3
"""Unit tests for kill-and-restart logic in _acquire_reindex_lock()"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'utils'))

from reindex_manager import _acquire_reindex_lock, _release_reindex_lock, get_project_storage_dir

def cleanup_claim_file(project_path):
    """Remove claim file if it exists"""
    storage_dir = get_project_storage_dir(project_path)
    claim_file = storage_dir / '.reindex_claim'
    try:
        claim_file.unlink()
    except FileNotFoundError:
        pass

def test_scenario_1_stale_claim_removed():
    """Test: Stale claim file (>60s old) gets removed"""
    project_path = Path.cwd()
    storage_dir = get_project_storage_dir(project_path)
    claim_file = storage_dir / '.reindex_claim'

    print("\n" + "=" * 60)
    print("SCENARIO 1: Stale claim file (>60s old)")
    print("=" * 60)

    # Create a stale claim file (set mtime to 70 seconds ago)
    claim_file.write_text(f"99999:{time.time() - 70}")
    os.utime(claim_file, (time.time() - 70, time.time() - 70))
    print(f"Created stale claim file (70s old): {claim_file}")

    # Try to acquire lock
    lock_acquired = _acquire_reindex_lock(project_path)
    print(f"Lock acquired: {lock_acquired}")

    # Assertions for pytest compatibility
    assert lock_acquired, "Should acquire lock when claim is stale"
    assert claim_file.exists(), "Claim file should exist after lock acquired"

    claim_content = claim_file.read_text()
    our_pid = str(os.getpid())
    assert our_pid in claim_content, f"Claim should have our PID, got: {claim_content}"

    print(f"✅ PASS: Stale claim removed, new claim created with our PID: {our_pid}")
    _release_reindex_lock(project_path)

def test_scenario_2_corrupted_claim_removed():
    """Test: Corrupted claim file gets removed"""
    project_path = Path.cwd()
    storage_dir = get_project_storage_dir(project_path)
    claim_file = storage_dir / '.reindex_claim'

    print("\n" + "=" * 60)
    print("SCENARIO 2: Corrupted claim file")
    print("=" * 60)

    # Create corrupted claim file (recent, but garbage content)
    claim_file.write_text("garbage:not:valid:data")
    print(f"Created corrupted claim file: garbage:not:valid:data")

    # Try to acquire lock
    lock_acquired = _acquire_reindex_lock(project_path)
    print(f"Lock acquired: {lock_acquired}")

    # Assertions for pytest compatibility
    assert lock_acquired, "Should acquire lock when claim is corrupted"
    assert claim_file.exists(), "Claim file should exist after lock acquired"

    claim_content = claim_file.read_text()
    our_pid = str(os.getpid())
    assert our_pid in claim_content, f"Claim should have our PID, got: {claim_content}"

    print(f"✅ PASS: Corrupted claim removed, new claim created")
    _release_reindex_lock(project_path)

def test_scenario_3_nonexistent_pid_removed():
    """Test: Claim file with non-existent PID gets removed"""
    project_path = Path.cwd()
    storage_dir = get_project_storage_dir(project_path)
    claim_file = storage_dir / '.reindex_claim'

    print("\n" + "=" * 60)
    print("SCENARIO 3: Claim file with non-existent PID")
    print("=" * 60)

    # Create claim with very high PID (unlikely to exist) and make it 65 seconds old
    # This makes it "stale" (>60s) so the non-existent PID check will trigger removal
    fake_pid = 999999
    claim_time = time.time() - 65  # 65 seconds ago (stale)
    claim_file.write_text(f"{fake_pid}:{claim_time}")
    os.utime(claim_file, (time.time() - 65, time.time() - 65))  # Set file mtime too
    print(f"Created claim file with non-existent PID: {fake_pid} (65s old, stale)")

    # Try to acquire lock
    print("\nAttempting to acquire lock...")
    lock_acquired = _acquire_reindex_lock(project_path)
    print(f"Lock acquired: {lock_acquired}")

    # Assertions for pytest compatibility
    assert lock_acquired, "Should acquire lock when PID doesn't exist"
    assert claim_file.exists(), "Claim file should exist after lock acquired"

    claim_content = claim_file.read_text()
    our_pid = str(os.getpid())
    assert our_pid in claim_content, f"Claim should have our PID, got: {claim_content}"

    print(f"✅ PASS: Non-existent PID detected, claim removed, new claim created")
    _release_reindex_lock(project_path)

def main():
    """Run all test scenarios"""
    project_path = Path.cwd()

    print("=" * 60)
    print("KILL-AND-RESTART UNIT TESTS")
    print("=" * 60)

    # Cleanup before tests
    cleanup_claim_file(project_path)

    results = []

    # Test 1: Stale claim
    try:
        test_scenario_1_stale_claim_removed()
        results.append(("Stale claim removed", True))
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        results.append(("Stale claim removed", False))
    cleanup_claim_file(project_path)

    # Test 2: Corrupted claim
    try:
        test_scenario_2_corrupted_claim_removed()
        results.append(("Corrupted claim removed", True))
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        results.append(("Corrupted claim removed", False))
    cleanup_claim_file(project_path)

    # Test 3: Non-existent PID
    try:
        test_scenario_3_nonexistent_pid_removed()
        results.append(("Non-existent PID removed", True))
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
        results.append(("Non-existent PID removed", False))
    cleanup_claim_file(project_path)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result for _, result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("OVERALL: ✅ ALL TESTS PASSED")
    else:
        print("OVERALL: ❌ SOME TESTS FAILED")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
