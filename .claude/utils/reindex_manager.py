#!/usr/bin/env python3
"""
Reindex Manager Utility

Centralized reindex logic for semantic search index management.
Used by session-start and post-tool-use hooks.

Pattern: Follows existing utils pattern (state_manager.py, session_logger.py)
"""

import subprocess
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


def get_project_root() -> Path:
    """Get project root directory (for hooks, go up from .claude/hooks/)"""
    # This module is in .claude/utils/, so go up two levels
    return Path(__file__).parent.parent.parent


def read_prerequisites_state() -> bool:
    """Read semantic-search prerequisites state (fast - just file read)

    Returns:
        True if prerequisites ready, False otherwise
    """
    try:
        project_root = get_project_root()
        state_file = project_root / 'logs' / 'state' / 'semantic-search-prerequisites.json'

        if not state_file.exists():
            return False

        with open(state_file, 'r') as f:
            state = json.load(f)

        return state.get('SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY', False)
    except Exception:
        return False


def get_project_storage_dir(project_path: Path) -> Path:
    """Get project-specific storage directory (matches Python implementation)"""
    storage_dir = Path.home() / '.claude_code_search'
    project_name = project_path.name
    project_hash = hashlib.md5(str(project_path).encode()).hexdigest()[:8]
    return storage_dir / "projects" / f"{project_name}_{project_hash}"


def check_index_exists(project_path: Path) -> bool:
    """Check if semantic search index exists for project"""
    try:
        index_dir = get_project_storage_dir(project_path) / "index"
        return (index_dir / "code.index").exists()
    except Exception:
        return False


def get_index_state_file(project_path: Path) -> Path:
    """Get index state file path"""
    return get_project_storage_dir(project_path) / "index_state.json"


def get_last_reindex_time(project_path: Path) -> Optional[datetime]:
    """Get timestamp of last reindex operation (full or incremental)

    Returns:
        datetime of last reindex, or None if never indexed
    """
    try:
        state_file = get_index_state_file(project_path)

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            state = json.load(f)

        # Check both last_full_index and last_incremental_index
        last_full = state.get('last_full_index')
        last_incremental = state.get('last_incremental_index')

        # Return the most recent timestamp
        timestamps = []
        if last_full:
            timestamps.append(datetime.fromisoformat(last_full))
        if last_incremental:
            timestamps.append(datetime.fromisoformat(last_incremental))

        if timestamps:
            return max(timestamps)

        return None
    except Exception:
        return None


def run_incremental_reindex_sync(project_path: Path) -> bool:
    """Run incremental reindex synchronously (simple, fast, visible errors)

    This runs within the hook's 60-second timeout.
    Typical duration: ~5 seconds for incremental updates.

    Args:
        project_path: Path to project

    Returns:
        True if successful, False if failed
    """
    try:
        project_root = get_project_root()
        script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental-reindex'

        # Run synchronously with timeout (leave 10s buffer from 60s limit)
        result = subprocess.run(
            [str(script), str(project_path)],
            timeout=50,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return True
        else:
            # Show error (not suppressed!)
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f"⚠️  Index update failed: {error_msg[:300]}\n", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"⚠️  Index update timed out (will retry next session)\n", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  Index update error: {e}\n", file=sys.stderr)
        return False


def should_reindex_after_cooldown(project_path: Path, cooldown_seconds: int = 300) -> bool:
    """Check if cooldown period has expired since last reindex

    Args:
        project_path: Path to project
        cooldown_seconds: Cooldown period in seconds (default: 300 = 5 minutes)

    Returns:
        True if cooldown expired or never indexed, False if still in cooldown
    """
    try:
        last_reindex = get_last_reindex_time(project_path)

        # Never indexed → allow reindex
        if last_reindex is None:
            return True

        # Calculate time since last reindex
        now = datetime.now(timezone.utc)

        # Handle timezone-aware and naive datetimes
        if last_reindex.tzinfo is None:
            last_reindex = last_reindex.replace(tzinfo=timezone.utc)

        elapsed = (now - last_reindex).total_seconds()

        # Cooldown expired?
        return elapsed >= cooldown_seconds

    except Exception:
        # If anything fails, allow reindex (graceful degradation)
        return True


def should_reindex_after_write(file_path: str, cooldown_seconds: int = 300) -> bool:
    """Check if reindex should run after Write operation

    File filtering logic:
    - Include: Code files (.py, .ts, .js, .tsx, .jsx, .go, .rs, .java, etc.)
    - Include: Documentation (.md, .txt, .rst, .adoc)
    - Include: Config files (.json, .yaml, .yml, .toml, .ini)
    - Exclude: Log files (logs/, .log)
    - Exclude: Build artifacts (dist/, build/, node_modules/, __pycache__)
    - Exclude: Git internals (.git/)
    - Exclude: Temporary files (.tmp, .temp, .cache)

    Args:
        file_path: Path to file that was written
        cooldown_seconds: Cooldown period in seconds (default: 300 = 5 minutes)

    Returns:
        True if should reindex, False if should skip
    """
    try:
        file_path_obj = Path(file_path)

        # Exclude patterns (directories and extensions)
        exclude_dirs = ['logs', '.git', 'dist', 'build', 'node_modules', '__pycache__', '.cache', '.tmp', 'temp']
        exclude_extensions = ['.log', '.tmp', '.temp', '.pyc', '.pyo', '.pyd', '.so', '.dylib', '.dll']

        # Check if file is in excluded directory
        for part in file_path_obj.parts:
            if part in exclude_dirs:
                return False

        # Check if file has excluded extension
        if file_path_obj.suffix in exclude_extensions:
            return False

        # Include patterns (extensions we want to index)
        include_extensions = [
            # Code files
            '.py', '.ts', '.js', '.tsx', '.jsx', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.m', '.sh', '.bash', '.zsh',
            # Documentation
            '.md', '.txt', '.rst', '.adoc', '.org',
            # Config files
            '.json', '.yaml', '.yml', '.toml', '.ini', '.conf', '.cfg', '.xml', '.env'
        ]

        # Check if file has included extension
        if file_path_obj.suffix not in include_extensions:
            return False

        # Check cooldown
        project_path = get_project_root()
        return should_reindex_after_cooldown(project_path, cooldown_seconds)

    except Exception:
        # If anything fails, skip reindex (graceful degradation)
        return False


def reindex_on_session_start(trigger: str) -> None:
    """Auto-reindex on session start (called by session-start hook)

    Business Logic:
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. Trigger is 'clear' or 'compact' → Skip (no code changes)
    3. Trigger is 'startup' or 'resume' + no index → Skip with message
    4. Trigger is 'startup' or 'resume' + index exists → Run incremental (~5s)

    Args:
        trigger: Session start trigger source ('startup', 'resume', 'clear', 'compact')
    """
    try:
        # Step 1: Check prerequisites (fast - just read state file)
        if not read_prerequisites_state():
            # Prerequisites not ready → skip indexing (manual setup not done)
            return

        # Step 2: Check trigger source
        if trigger in ['clear', 'compact']:
            # No code changes → skip indexing
            return

        # Step 3: Only auto-index on startup/resume
        if trigger not in ['startup', 'resume']:
            return

        # Step 4: Check if index exists (require manual first-time setup)
        project_path = get_project_root()

        if not check_index_exists(project_path):
            # No index yet → user needs to run manual setup
            print("ℹ️  Semantic search not yet indexed")
            print("   Run: .claude/skills/semantic-search/scripts/index <project_path> --full")
            print("   (First-time setup: ~3 minutes)\n")
            return

        # Step 5: Run incremental reindex synchronously (~5 seconds)
        print("🔄 Updating semantic search index...")
        success = run_incremental_reindex_sync(project_path)

        if success:
            print("✅ Semantic search index updated\n")
        # Errors already printed by run_incremental_reindex_sync

    except Exception as e:
        # Don't fail hook if auto-indexing fails
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)


def reindex_after_write(file_path: str, cooldown_seconds: int = 300) -> None:
    """Auto-reindex after Write operation (called by post-tool-use hook)

    Business Logic:
    1. Prerequisites FALSE → Skip
    2. File not indexable (logs, build artifacts) → Skip
    3. Cooldown active → Skip (prevents rapid reindex spam)
    4. All checks pass → Run incremental (~5s)

    Args:
        file_path: Path to file that was written
        cooldown_seconds: Cooldown period in seconds (default: 300 = 5 minutes)
    """
    try:
        # Step 1: Check prerequisites
        if not read_prerequisites_state():
            return

        # Step 2: Check if file should trigger reindex (includes cooldown check)
        if not should_reindex_after_write(file_path, cooldown_seconds):
            return

        # Step 3: Check if index exists
        project_path = get_project_root()
        if not check_index_exists(project_path):
            return

        # Step 4: Run incremental reindex synchronously (~5 seconds)
        print(f"🔄 Updating semantic search index (file modified: {Path(file_path).name})...")
        success = run_incremental_reindex_sync(project_path)

        if success:
            print("✅ Semantic search index updated\n")
        # Errors already printed by run_incremental_reindex_sync

    except Exception as e:
        # Don't fail hook if auto-indexing fails
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)
