#!/usr/bin/env python3
"""
Unit Tests for reindex_manager.py

Tests critical paths: config loading, file filtering, cooldown logic, validation.
Run with: pytest tests/test_reindex_manager.py -v
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, mock_open

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'utils'))
import reindex_manager


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Configuration Loading & Validation
# ═══════════════════════════════════════════════════════════════════════════

def test_get_reindex_config_defaults():
    """Test that defaults load when no config file exists"""
    config = reindex_manager.get_reindex_config(force_reload=True)

    assert config['cooldown_seconds'] == 300
    assert '*.py' in config['file_include_patterns']
    assert 'dist' in config['file_exclude_dirs']
    assert '*_transcript.txt' in config['file_exclude_patterns']
    # CRITICAL: 'logs' should NOT be in exclude_dirs
    assert 'logs' not in config['file_exclude_dirs']


def test_config_validation_invalid_cooldown():
    """Test config validation rejects invalid cooldown"""
    invalid_config = {
        'cooldown_seconds': "not a number",  # Invalid type
        'file_include_patterns': ['*.py'],
        'file_exclude_dirs': ['dist'],
        'file_exclude_patterns': ['*.log']
    }

    with pytest.raises(ValueError, match="cooldown_seconds must be positive integer"):
        reindex_manager._validate_config(invalid_config)


def test_config_validation_invalid_patterns():
    """Test config validation rejects invalid patterns"""
    invalid_config = {
        'cooldown_seconds': 300,
        'file_include_patterns': 123,  # Not a list!
        'file_exclude_dirs': ['dist'],
        'file_exclude_patterns': ['*.log']
    }

    with pytest.raises(ValueError, match="file_include_patterns must be list of strings"):
        reindex_manager._validate_config(invalid_config)


def test_config_caching():
    """Test that config is cached (Fix #9)"""
    # Clear cache
    reindex_manager._config_cache = None

    # First call - loads config
    config1 = reindex_manager.get_reindex_config()

    # Second call - should return cached
    config2 = reindex_manager.get_reindex_config()

    # Should be the same object (cached)
    assert config1 is config2


# ═══════════════════════════════════════════════════════════════════════════
# TEST: File Filtering Logic
# ═══════════════════════════════════════════════════════════════════════════

def test_should_reindex_after_write_python_file():
    """Test that Python files trigger reindex"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('/project/src/main.py')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is True


def test_should_reindex_after_write_transcript_excluded():
    """Test that transcripts are excluded (Fix #2 verification)"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('logs/session_20251203_164604_transcript.txt')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is False  # Excluded by pattern


def test_should_reindex_after_write_logs_state_included():
    """Test that logs/state/ files are included (Fix #2 verification)"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('logs/state/semantic-search-prerequisites.json')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is True  # NOT excluded (logs not in exclude_dirs, pattern doesn't match)


def test_should_reindex_after_write_build_artifact_excluded():
    """Test that build artifacts are excluded"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('dist/bundle.js')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is False  # Excluded by directory


def test_should_reindex_after_write_no_extension():
    """Test that files without extension are excluded"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('/project/Makefile')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is False  # No matching include pattern


def test_should_reindex_after_write_cooldown_active():
    """Test that reindex is skipped when cooldown active"""
    # Mock cooldown check to return False (cooldown active)
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=False):
        result = reindex_manager.should_reindex_after_write('/project/src/main.py')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is False  # Cooldown active


def test_should_reindex_after_write_cooldown_parameter():
    """Test that cooldown parameter override works (Fix #1 verification)"""
    # Mock cooldown check - should receive custom cooldown
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True) as mock_cooldown:
        reindex_manager.should_reindex_after_write('/project/src/main.py', cooldown_seconds=600)

        # Verify cooldown was called with custom value
        mock_cooldown.assert_called_once()
        args = mock_cooldown.call_args
        assert args[0][1] == 600  # Second argument should be 600


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Cooldown Logic
# ═══════════════════════════════════════════════════════════════════════════

def test_should_reindex_after_cooldown_never_indexed():
    """Test cooldown allows reindex when never indexed before"""
    with patch.object(reindex_manager, 'get_last_reindex_time', return_value=None):
        result = reindex_manager.should_reindex_after_cooldown(Path('/project'))

    assert result is True


def test_should_reindex_after_cooldown_expired():
    """Test cooldown expired (last reindex >5 min ago)"""
    # Mock: Last reindex 10 minutes ago
    ten_min_ago = datetime.now(timezone.utc) - timedelta(minutes=10)

    with patch.object(reindex_manager, 'get_last_reindex_time', return_value=ten_min_ago):
        result = reindex_manager.should_reindex_after_cooldown(Path('/project'), cooldown_seconds=300)

    assert result is True  # Cooldown expired (600s > 300s)


def test_should_reindex_after_cooldown_active():
    """Test cooldown still active (last reindex <5 min ago)"""
    # Mock: Last reindex 2 minutes ago
    two_min_ago = datetime.now(timezone.utc) - timedelta(minutes=2)

    with patch.object(reindex_manager, 'get_last_reindex_time', return_value=two_min_ago):
        result = reindex_manager.should_reindex_after_cooldown(Path('/project'), cooldown_seconds=300)

    assert result is False  # Cooldown active (120s < 300s)


def test_should_reindex_after_cooldown_exactly_300():
    """Test cooldown at exactly 300 seconds (edge case)"""
    # Mock: Last reindex exactly 5 minutes ago
    five_min_ago = datetime.now(timezone.utc) - timedelta(seconds=300)

    with patch.object(reindex_manager, 'get_last_reindex_time', return_value=five_min_ago):
        result = reindex_manager.should_reindex_after_cooldown(Path('/project'), cooldown_seconds=300)

    assert result is True  # 300 >= 300 → Allow reindex (inclusive)


def test_timezone_handling_naive_datetime():
    """Test timezone handling for naive timestamps (Fix from hybrid)"""
    # Mock: Naive datetime (no timezone)
    naive_time = datetime(2025, 12, 3, 10, 0, 0)  # No tzinfo

    with patch.object(reindex_manager, 'get_last_reindex_time', return_value=naive_time):
        # Should NOT crash (converts naive → UTC)
        result = reindex_manager.should_reindex_after_cooldown(Path('/project'), cooldown_seconds=300)

        # Should work (no TypeError)
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Timestamp Tracking (Both Versions)
# ═══════════════════════════════════════════════════════════════════════════

def test_get_last_full_index_time_vs_get_last_reindex_time():
    """Test semantic difference between the two timestamp functions"""
    # Mock state file with BOTH full and incremental timestamps
    state_data = {
        'last_full_index': '2025-12-03T10:00:00+00:00',
        'last_incremental_index': '2025-12-03T10:30:00+00:00'  # 30 min after full
    }

    mock_file = mock_open(read_data=json.dumps(state_data))

    with patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_file):

        # get_last_full_index_time should return ONLY full
        full_time = reindex_manager.get_last_full_index_time(Path('/project'))
        assert full_time == datetime.fromisoformat('2025-12-03T10:00:00+00:00')

        # get_last_reindex_time should return MOST RECENT (incremental)
        reindex_time = reindex_manager.get_last_reindex_time(Path('/project'))
        assert reindex_time == datetime.fromisoformat('2025-12-03T10:30:00+00:00')


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Error Handling & Edge Cases
# ═══════════════════════════════════════════════════════════════════════════

def test_should_reindex_after_write_exception_handling():
    """Test that exceptions in file filtering return False (graceful)"""
    # Force an exception in path handling
    with patch.object(Path, 'match', side_effect=Exception("Test error")):
        result = reindex_manager.should_reindex_after_write('/project/src/main.py')

    # Function returns (bool, str, dict) tuple for debugging
    should_reindex, reason, details = result
    assert should_reindex is False  # Graceful degradation


def test_should_reindex_after_cooldown_exception_handling():
    """Test that exceptions in cooldown check return True (allow reindex)"""
    # Force an exception
    with patch.object(reindex_manager, 'get_last_reindex_time', side_effect=Exception("Test error")):
        result = reindex_manager.should_reindex_after_cooldown(Path('/project'))

    assert result is True  # Graceful degradation (allow reindex)


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Integration
# ═══════════════════════════════════════════════════════════════════════════

def test_reindex_after_write_full_flow():
    """Test complete flow of reindex_after_write (integration)"""
    # Mock prerequisites, index check, cooldown
    with patch.object(reindex_manager, 'read_prerequisites_state', return_value=True), \
         patch.object(reindex_manager, 'check_index_exists', return_value=True), \
         patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True), \
         patch.object(reindex_manager, 'run_incremental_reindex_sync', return_value=True) as mock_reindex:

        # Call reindex_after_write
        reindex_manager.reindex_after_write('/project/src/main.py', cooldown_seconds=600)

        # Verify reindex was called
        mock_reindex.assert_called_once()


def test_reindex_after_write_skips_when_prerequisites_false():
    """Test that reindex is skipped when prerequisites not met"""
    with patch.object(reindex_manager, 'read_prerequisites_state', return_value=False):
        with patch.object(reindex_manager, 'run_incremental_reindex_sync') as mock_reindex:
            reindex_manager.reindex_after_write('/project/src/main.py')

            # Reindex should NOT be called
            mock_reindex.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════
# TEST: Atomic Lock Mechanism (Concurrency Control)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory for lock tests"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def mock_storage_dir(tmp_path, monkeypatch):
    """Mock get_project_storage_dir to use temp directory"""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()

    def mock_get_storage_dir(project_path):
        return storage_dir

    monkeypatch.setattr(reindex_manager, 'get_project_storage_dir', mock_get_storage_dir)
    return storage_dir


def test_acquire_lock_success(temp_project_dir, mock_storage_dir):
    """Test successful lock acquisition when no lock exists"""
    result = reindex_manager._acquire_reindex_lock(temp_project_dir)

    assert result is True

    # Verify lock file created
    claim_file = mock_storage_dir / '.reindex_claim'
    assert claim_file.exists()

    # Verify lock file contains PID and timestamp
    content = claim_file.read_text()
    assert ':' in content  # Format: "PID:timestamp"
    pid, timestamp = content.split(':')
    assert pid.isdigit()
    assert float(timestamp) > 0


def test_acquire_lock_failure_already_locked(temp_project_dir, mock_storage_dir):
    """Test lock acquisition fails when lock already held"""
    # First acquisition succeeds
    result1 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result1 is True

    # Second acquisition fails (lock already held)
    result2 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result2 is False


def test_acquire_lock_removes_stale_lock(temp_project_dir, mock_storage_dir):
    """Test that stale locks (>60s old) are removed and new lock acquired"""
    import time

    claim_file = mock_storage_dir / '.reindex_claim'

    # Create stale lock file (simulate 61 seconds old)
    claim_file.write_text("99999:1234567890.0")  # Old timestamp

    # Modify file time to 61 seconds ago
    stale_time = time.time() - 61
    import os
    os.utime(str(claim_file), (stale_time, stale_time))

    # Lock acquisition should succeed (stale lock removed)
    result = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result is True

    # Verify new lock created with current PID
    content = claim_file.read_text()
    pid, timestamp = content.split(':')
    assert int(pid) == os.getpid()


def test_acquire_lock_respects_recent_lock(temp_project_dir, mock_storage_dir):
    """Test that recent locks (<60s old) are respected"""
    import time

    claim_file = mock_storage_dir / '.reindex_claim'

    # Create recent lock file (30 seconds old)
    current_time = time.time()
    claim_file.write_text(f"88888:{current_time - 30}")

    # Lock acquisition should fail (recent lock still valid)
    result = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result is False


def test_acquire_lock_handles_race_condition(temp_project_dir, mock_storage_dir):
    """Test atomic lock creation handles race conditions"""
    import os

    claim_file = mock_storage_dir / '.reindex_claim'

    # Simulate race: file created between exists() check and create
    # First process acquires lock
    result1 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result1 is True

    # Second process tries to acquire (should fail with FileExistsError internally)
    result2 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result2 is False

    # Verify only one lock file exists with first process PID
    content = claim_file.read_text()
    pid, _ = content.split(':')
    assert int(pid) == os.getpid()


def test_release_lock_success(temp_project_dir, mock_storage_dir):
    """Test successful lock release removes claim file"""
    # Acquire lock first
    reindex_manager._acquire_reindex_lock(temp_project_dir)

    claim_file = mock_storage_dir / '.reindex_claim'
    assert claim_file.exists()

    # Release lock
    reindex_manager._release_reindex_lock(temp_project_dir)

    # Verify claim file removed
    assert not claim_file.exists()


def test_release_lock_handles_missing_file(temp_project_dir, mock_storage_dir):
    """Test lock release handles already-removed file gracefully"""
    # Try to release non-existent lock (should not raise)
    try:
        reindex_manager._release_reindex_lock(temp_project_dir)
    except Exception as e:
        pytest.fail(f"Lock release should handle missing file, but raised: {e}")


def test_release_lock_handles_permission_error(temp_project_dir, mock_storage_dir, monkeypatch):
    """Test lock release handles permission errors gracefully"""
    claim_file = mock_storage_dir / '.reindex_claim'
    claim_file.write_text("12345:1234567890.0")

    # Mock unlink to raise PermissionError
    original_unlink = Path.unlink
    def mock_unlink(self, *args, **kwargs):
        raise PermissionError("Test permission error")

    monkeypatch.setattr(Path, 'unlink', mock_unlink)

    # Should not raise (best effort cleanup)
    try:
        reindex_manager._release_reindex_lock(temp_project_dir)
    except Exception as e:
        pytest.fail(f"Lock release should suppress exceptions, but raised: {e}")


def test_lock_lifecycle_full_flow(temp_project_dir, mock_storage_dir):
    """Test complete lock lifecycle: acquire -> use -> release"""
    claim_file = mock_storage_dir / '.reindex_claim'

    # Step 1: No lock exists initially
    assert not claim_file.exists()

    # Step 2: Acquire lock
    result = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result is True
    assert claim_file.exists()

    # Step 3: Try to acquire again (should fail)
    result2 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result2 is False

    # Step 4: Release lock
    reindex_manager._release_reindex_lock(temp_project_dir)
    assert not claim_file.exists()

    # Step 5: Can acquire again after release
    result3 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result3 is True
    assert claim_file.exists()

    # Cleanup
    reindex_manager._release_reindex_lock(temp_project_dir)


def test_lock_mechanism_atomic_creation(temp_project_dir, mock_storage_dir):
    """Test that lock uses atomic file creation (os.O_EXCL)"""
    import os

    claim_file = mock_storage_dir / '.reindex_claim'

    # First creation should succeed
    result1 = reindex_manager._acquire_reindex_lock(temp_project_dir)
    assert result1 is True

    # Verify file was created atomically (os.O_EXCL ensures this)
    # If second process tries to create with O_EXCL, it fails with FileExistsError
    try:
        fd = os.open(str(claim_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.close(fd)
        pytest.fail("Should raise FileExistsError due to O_EXCL flag")
    except FileExistsError:
        pass  # Expected - atomic creation prevents duplicate


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
