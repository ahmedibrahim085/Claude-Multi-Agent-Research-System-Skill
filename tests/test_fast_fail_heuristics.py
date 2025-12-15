#!/usr/bin/env python3
"""
Tests for fast-fail heuristics optimization (TDD approach)

RED PHASE: These tests will FAIL initially (functions don't exist yet)
"""

import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts'))

# Import will fail initially - that's expected in RED phase
try:
    from incremental_reindex import FixedIncrementalIndexer
except ImportError:
    pytest.skip("FixedIncrementalIndexer not yet modified", allow_module_level=True)


class TestGitStatusHeuristic:
    """Test git status clean heuristic"""

    def test_git_status_clean_returns_true_when_no_changes(self):
        """Git status with no changes should return True"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('subprocess.run') as mock_run:
            # Mock git status returning empty (clean)
            mock_run.return_value = Mock(
                stdout='',
                returncode=0
            )

            result = reindexer._git_status_clean()

            assert result is True
            mock_run.assert_called_once()
            # Verify git command
            args = mock_run.call_args[0][0]
            assert 'git' in args
            assert 'status' in args
            assert '--porcelain' in args

    def test_git_status_dirty_returns_false_when_changes_exist(self):
        """Git status with changes should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('subprocess.run') as mock_run:
            # Mock git status returning changes
            mock_run.return_value = Mock(
                stdout=' M file.py\n',
                returncode=0
            )

            result = reindexer._git_status_clean()

            assert result is False

    def test_git_status_handles_command_failure_gracefully(self):
        """Git command failure should return False (safe fallback)"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('subprocess.run') as mock_run:
            # Mock git command failing
            mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

            result = reindexer._git_status_clean()

            # Should return False (fall back to full validation)
            assert result is False


class TestSnapshotTimestampHeuristic:
    """Test snapshot timestamp recency heuristic"""

    def test_snapshot_recent_returns_true_when_fresh(self):
        """Snapshot modified <5 min ago should return True"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            # Mock snapshot modified 2 minutes ago
            mock_stat.return_value = Mock(st_mtime=time.time() - 120)

            result = reindexer._snapshot_timestamp_recent()

            assert result is True

    def test_snapshot_old_returns_false_when_stale(self):
        """Snapshot modified >5 min ago should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            # Mock snapshot modified 10 minutes ago
            mock_stat.return_value = Mock(st_mtime=time.time() - 600)

            result = reindexer._snapshot_timestamp_recent()

            assert result is False

    def test_snapshot_missing_returns_false(self):
        """Missing snapshot should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('pathlib.Path.exists', return_value=False):
            result = reindexer._snapshot_timestamp_recent()

            assert result is False


class TestFileCountHeuristic:
    """Test file count stability heuristic"""

    def test_file_count_stable_returns_true_when_within_threshold(self):
        """File count within 5% of snapshot should return True"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        # Mock MerkleDAG with 1000 files
        mock_dag = Mock()
        mock_dag.get_all_files.return_value = [Mock()] * 1000

        with patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=True), \
             patch.object(reindexer.snapshot_manager, 'load_snapshot', return_value=mock_dag), \
             patch('pathlib.Path.glob') as mock_glob:
            # Mock current file count: 1020 files (2% increase, within 5%)
            mock_glob.return_value = [Mock()] * 1020

            result = reindexer._file_count_stable()

            assert result is True

    def test_file_count_unstable_returns_false_when_exceeds_threshold(self):
        """File count >5% different from snapshot should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        # Mock MerkleDAG with 1000 files
        mock_dag = Mock()
        mock_dag.get_all_files.return_value = [Mock()] * 1000

        with patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=True), \
             patch.object(reindexer.snapshot_manager, 'load_snapshot', return_value=mock_dag), \
             patch('pathlib.Path.glob') as mock_glob:
            # Mock current file count: 1100 files (10% increase, exceeds 5%)
            mock_glob.return_value = [Mock()] * 1100

            result = reindexer._file_count_stable()

            assert result is False

    def test_file_count_no_snapshot_returns_false(self):
        """No snapshot should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=False):
            result = reindexer._file_count_stable()

            assert result is False


class TestCacheTimestampHeuristic:
    """Test cache timestamp match heuristic"""

    def test_cache_synced_returns_true_when_timestamps_match(self):
        """Cache timestamp matching snapshot should return True"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        snapshot_time = time.time() - 100

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            # Mock both having same timestamp
            mock_stat.return_value = Mock(st_mtime=snapshot_time)

            result = reindexer._cache_timestamp_synced()

            assert result is True

    def test_cache_desynced_returns_false_when_timestamps_differ(self):
        """Cache timestamp different from snapshot should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat') as mock_stat:
            # Mock different timestamps
            mock_stat.side_effect = [
                Mock(st_mtime=time.time() - 100),  # snapshot
                Mock(st_mtime=time.time() - 50),   # cache (newer)
            ]

            result = reindexer._cache_timestamp_synced()

            assert result is False

    def test_cache_missing_returns_false(self):
        """Missing cache should return False"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch('pathlib.Path.exists', side_effect=[True, False]):
            result = reindexer._cache_timestamp_synced()

            assert result is False


class TestFastFailIntegration:
    """Test fast-fail integration into auto_reindex()"""

    def test_fast_fail_skips_when_3_of_4_heuristics_pass(self):
        """auto_reindex() should skip when 3/4 heuristics pass"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch.object(reindexer, '_git_status_clean', return_value=True), \
             patch.object(reindexer, '_snapshot_timestamp_recent', return_value=True), \
             patch.object(reindexer, '_file_count_stable', return_value=True), \
             patch.object(reindexer, '_cache_timestamp_synced', return_value=False), \
             patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=True):

            result = reindexer.auto_reindex(force_full=False)

            # Should skip (3/4 heuristics passed)
            assert result['success'] is True
            assert result.get('skipped') is True
            assert result.get('fast_fail') is True
            assert 'time_taken' in result
            # Verify it's fast (<200ms target)
            assert result['time_taken'] < 0.2

    def test_fast_fail_proceeds_when_only_2_of_4_heuristics_pass(self):
        """auto_reindex() should build Merkle DAG when only 2/4 heuristics pass"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch.object(reindexer, '_git_status_clean', return_value=True), \
             patch.object(reindexer, '_snapshot_timestamp_recent', return_value=True), \
             patch.object(reindexer, '_file_count_stable', return_value=False), \
             patch.object(reindexer, '_cache_timestamp_synced', return_value=False), \
             patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=True), \
             patch('incremental_reindex.MerkleDAG') as mock_dag:

            # Mock Merkle DAG to avoid actual build
            mock_dag_instance = Mock()
            mock_dag_instance.build = Mock()
            mock_dag.return_value = mock_dag_instance

            # This will likely fail because we haven't mocked everything,
            # but the important part is it tried to build Merkle DAG
            try:
                result = reindexer.auto_reindex(force_full=False)
            except:
                pass

            # Verify Merkle DAG was instantiated (fell through to full validation)
            mock_dag.assert_called_once()

    def test_fast_fail_skipped_when_no_snapshot_exists(self):
        """Fast-fail should be skipped when no snapshot exists (first run)"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=False), \
             patch.object(reindexer, '_full_index') as mock_full:
            mock_full.return_value = {'success': True}

            result = reindexer.auto_reindex(force_full=False)

            # Should go directly to full index (no fast-fail attempted)
            mock_full.assert_called_once()


class TestPerformanceRequirements:
    """Test performance requirements are met"""

    def test_fast_fail_path_meets_200ms_target(self):
        """Fast-fail path should complete in <200ms"""
        reindexer = FixedIncrementalIndexer(project_path=Path("/fake/path"))

        with patch.object(reindexer, '_git_status_clean', return_value=True), \
             patch.object(reindexer, '_snapshot_timestamp_recent', return_value=True), \
             patch.object(reindexer, '_file_count_stable', return_value=True), \
             patch.object(reindexer, '_cache_timestamp_synced', return_value=True), \
             patch.object(reindexer.snapshot_manager, 'has_snapshot', return_value=True):

            start = time.time()
            result = reindexer.auto_reindex(force_full=False)
            elapsed = time.time() - start

            # CRITICAL: Must meet <200ms target
            assert elapsed < 0.2, f"Fast-fail took {elapsed*1000:.0f}ms, target is 200ms"
            assert result.get('fast_fail') is True
