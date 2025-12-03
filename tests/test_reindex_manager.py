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

    assert result is True


def test_should_reindex_after_write_transcript_excluded():
    """Test that transcripts are excluded (Fix #2 verification)"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('logs/session_20251203_164604_transcript.txt')

    assert result is False  # Excluded by pattern


def test_should_reindex_after_write_logs_state_included():
    """Test that logs/state/ files are included (Fix #2 verification)"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('logs/state/semantic-search-prerequisites.json')

    assert result is True  # NOT excluded (logs not in exclude_dirs, pattern doesn't match)


def test_should_reindex_after_write_build_artifact_excluded():
    """Test that build artifacts are excluded"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('dist/bundle.js')

    assert result is False  # Excluded by directory


def test_should_reindex_after_write_no_extension():
    """Test that files without extension are excluded"""
    # Mock cooldown check to return True
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=True):
        result = reindex_manager.should_reindex_after_write('/project/Makefile')

    assert result is False  # No matching include pattern


def test_should_reindex_after_write_cooldown_active():
    """Test that reindex is skipped when cooldown active"""
    # Mock cooldown check to return False (cooldown active)
    with patch.object(reindex_manager, 'should_reindex_after_cooldown', return_value=False):
        result = reindex_manager.should_reindex_after_write('/project/src/main.py')

    assert result is False  # Cooldown active


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

    assert result is False  # Graceful degradation


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


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
