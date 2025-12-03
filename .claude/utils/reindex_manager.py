#!/usr/bin/env python3
"""
Reindex Manager Utility - Hybrid Approach (Best of Both Worlds)

Centralized reindex logic for semantic search index management.
Used by session-start and post-tool-use hooks.

Design Philosophy:
━━━━━━━━━━━━━━━━━━
- Add, Don't Replace: Keep original functions + add new features
- Layer Features: New functionality built on top of proven code
- Document Context: Preserve "why" not just "what"
- No Breaking Changes: Additive API design
- Configuration with Defaults: Works out of box, tunable for advanced users

Pattern: Follows existing utils pattern (state_manager.py, session_logger.py)
"""

import subprocess
import hashlib
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Add utils to path for config_loader
sys.path.insert(0, str(Path(__file__).parent))

try:
    import config_loader
except ImportError:
    # Fallback if config_loader not available
    config_loader = None


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def get_reindex_config() -> Dict[str, Any]:
    """Load reindex configuration with sensible defaults

    Config file: .claude/config.json
    Section: semantic_search.reindex

    Defaults:
        cooldown_seconds: 300 (5 minutes)
            - Prevents rapid reindex spam
            - Typical incremental: ~5 seconds
            - User can tune per-project needs

        file_include_patterns: Extensions to index
            - Code: *.py, *.ts, *.js, *.tsx, *.jsx, *.go, *.rs, *.java
            - Docs: *.md, *.txt, *.rst, *.adoc
            - Config: *.json, *.yaml, *.yml, *.toml, *.ini

        file_exclude_dirs: Directories to ignore
            - Build: dist, build, target, out
            - Dependencies: node_modules, __pycache__, .git
            - Temp: .cache, .tmp, temp

        file_exclude_patterns: Filename patterns to ignore
            - Logs: *_transcript.txt, *_tool_calls.jsonl, *.log
            - Temp: *.tmp, *.temp
            - Compiled: *.pyc, *.pyo, *.so, *.dylib

        logs_state_include: true (CRITICAL!)
            - Override exclude for logs/state/ directory
            - State files are important configs, must be indexed
            - Examples: semantic-search-prerequisites.json, research-workflow-state.json

    Returns:
        Dict with configuration values (merged with defaults)
    """
    defaults = {
        'cooldown_seconds': 300,
        'file_include_patterns': [
            # Code files
            '*.py', '*.ts', '*.js', '*.tsx', '*.jsx', '*.go', '*.rs', '*.java',
            '*.c', '*.cpp', '*.h', '*.hpp', '*.cs', '*.rb', '*.php', '*.swift',
            '*.kt', '*.scala', '*.r', '*.m', '*.sh', '*.bash', '*.zsh',
            # Documentation
            '*.md', '*.txt', '*.rst', '*.adoc', '*.org',
            # Config files
            '*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.conf', '*.cfg', '*.xml'
        ],
        'file_exclude_dirs': [
            # Build artifacts
            'dist', 'build', 'target', 'out',
            # Dependencies
            'node_modules', '__pycache__', 'vendor',
            # Version control
            '.git', '.svn', '.hg',
            # Temp
            '.cache', '.tmp', 'temp'
        ],
        'file_exclude_patterns': [
            # Logs
            '*_transcript.txt', '*_tool_calls.jsonl', '*.log',
            # Temp
            '*.tmp', '*.temp',
            # Compiled
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dylib', '*.dll'
        ],
        'logs_state_include': True  # CRITICAL: Don't exclude logs/state/
    }

    try:
        if config_loader is None:
            return defaults

        config = config_loader.load_config()
        reindex_config = config.get('semantic_search', {}).get('reindex', {})

        # Merge with defaults (user config overrides)
        return {**defaults, **reindex_config}
    except Exception:
        # Graceful degradation: Use defaults
        return defaults


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: PATH & STATE UTILITIES
# ═══════════════════════════════════════════════════════════════════════════

def get_project_root() -> Path:
    """Get project root directory

    This module is in .claude/utils/, so go up two levels to reach project root.

    Returns:
        Path to project root directory
    """
    return Path(__file__).parent.parent.parent


def read_prerequisites_state() -> bool:
    """Read semantic-search prerequisites state (fast - just file read)

    Prerequisites include:
    - MCP server installed (claude-context-local)
    - sentence-transformers package installed
    - Model downloaded (google/embeddinggemma-300m)

    State file: logs/state/semantic-search-prerequisites.json

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
    """Get project-specific storage directory (matches Python implementation)

    Storage structure:
        ~/.claude_code_search/projects/{project_name}_{hash}/
        ├── index/
        │   ├── code.index (FAISS index)
        │   └── merkle_snapshot.json (change detection)
        └── index_state.json (timestamps)

    Hash algorithm: MD5 (first 8 chars) for consistent project identification

    Args:
        project_path: Path to project

    Returns:
        Path to project-specific storage directory
    """
    storage_dir = Path.home() / '.claude_code_search'
    project_name = project_path.name
    project_hash = hashlib.md5(str(project_path).encode()).hexdigest()[:8]
    return storage_dir / "projects" / f"{project_name}_{project_hash}"


def check_index_exists(project_path: Path) -> bool:
    """Check if semantic search index exists for project

    Checks for: index/code.index file (FAISS index)

    Args:
        project_path: Path to project

    Returns:
        True if index exists, False otherwise
    """
    try:
        index_dir = get_project_storage_dir(project_path) / "index"
        return (index_dir / "code.index").exists()
    except Exception:
        return False


def get_index_state_file(project_path: Path) -> Path:
    """Get index state file path

    State file contains:
        - last_full_index: Timestamp of last full reindex
        - last_incremental_index: Timestamp of last incremental reindex
        - total_chunks: Number of chunks in index
        - files_indexed: Number of files indexed

    Args:
        project_path: Path to project

    Returns:
        Path to index_state.json file
    """
    return get_project_storage_dir(project_path) / "index_state.json"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: TIMESTAMP TRACKING (BOTH VERSIONS - HYBRID APPROACH)
# ═══════════════════════════════════════════════════════════════════════════

def get_last_full_index_time(project_path: Path) -> Optional[datetime]:
    """Get timestamp of last FULL index (ORIGINAL behavior preserved)

    Semantic Difference from get_last_reindex_time():
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - This function: Returns ONLY last_full_index timestamp
    - Other function: Returns MOST RECENT of (full, incremental)

    Use Cases:
    - Cooldown logic that only cares about full reindex spam
    - Metrics tracking (when was last full rebuild?)
    - Debugging (distinguish full vs incremental)

    Why Keep Both?
    - Original code may depend on "full only" semantics
    - Different use cases have different requirements
    - No breaking changes (additive API)

    Args:
        project_path: Path to project

    Returns:
        datetime of last full index, or None if never indexed
    """
    try:
        state_file = get_index_state_file(project_path)

        if not state_file.exists():
            return None

        with open(state_file, 'r') as f:
            state = json.load(f)

        last_full = state.get('last_full_index')
        if last_full:
            return datetime.fromisoformat(last_full)

        return None
    except Exception:
        return None


def get_last_reindex_time(project_path: Path) -> Optional[datetime]:
    """Get timestamp of last reindex operation (full OR incremental) - NEW

    Semantic Difference from get_last_full_index_time():
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - This function: Returns MOST RECENT of (full, incremental)
    - Other function: Returns ONLY last_full_index timestamp

    Rationale:
    - Incremental reindex also updates index (adds/removes chunks)
    - Both operations should reset cooldown
    - More accurate cooldown: Prevents spam regardless of reindex type

    Use Cases:
    - Cooldown logic that prevents ANY reindex spam
    - Determining if index is stale
    - Metrics tracking (overall activity)

    Args:
        project_path: Path to project

    Returns:
        datetime of last reindex (most recent), or None if never indexed
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


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: REINDEX EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

def run_incremental_reindex_sync(project_path: Path) -> bool:
    """Run incremental reindex synchronously (simple, fast, visible errors)

    Design Rationale (PRESERVED FROM ORIGINAL):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Synchronous execution: No background processes (avoids Claude Code Bug #1481)
      * Bug #1481: Popen with start_new_session=True still blocks Claude Code
      * Root cause: Claude Code waits for ALL child processes (even detached)
      * Solution: Use subprocess.run() synchronously within 60s timeout

    - 50-second timeout: Leaves 10s buffer from hook's 60s hard limit
      * Typical incremental: ~5 seconds (well under limit)
      * Full reindex: ~3 minutes (too long, must be manual)
      * Buffer accounts for: hook overhead, state file I/O, error handling

    - Visible errors: capture_output=True (not DEVNULL)
      * Previous version: DEVNULL caused silent failures
      * IndexFlatIP bug went undetected for hours
      * Current: User sees errors immediately, can take action

    - No lock files: Simplified from previous over-engineering
      * Previous: PID-based lock files, stale lock cleanup, concurrency logic
      * Current: Simple synchronous execution (no concurrency possible)
      * Trade-off: Can't prevent concurrent manual reindex, but acceptable

    Performance:
    - Typical: ~2-5 seconds (Merkle tree detects changed files)
    - Worst case: ~50 seconds (timeout, then abort)
    - Best case: <1 second (no changes detected)

    Args:
        project_path: Path to project

    Returns:
        True if successful, False if failed (never raises)
    """
    try:
        project_root = get_project_root()
        script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental-reindex'

        # Pre-flight check: Script exists?
        if not script.exists():
            print(f"⚠️  Reindex script not found: {script}", file=sys.stderr)
            print(f"   Skill may not be installed correctly", file=sys.stderr)
            return False

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
            print(f"⚠️  Index update failed: {error_msg[:300]}", file=sys.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"⚠️  Index update timed out (>50s) - will retry next session", file=sys.stderr)
        print(f"   This may indicate a very large changeset", file=sys.stderr)
        return False

    except PermissionError as e:
        print(f"⚠️  Permission denied: {e}", file=sys.stderr)
        print(f"   Check permissions for: {get_project_storage_dir(project_path)}", file=sys.stderr)
        return False

    except FileNotFoundError as e:
        print(f"⚠️  File not found: {e}", file=sys.stderr)
        print(f"   Run manual setup: scripts/index --full {project_path}", file=sys.stderr)
        return False

    except Exception as e:
        # Unexpected errors - show traceback only in debug mode
        print(f"⚠️  Unexpected reindex error: {type(e).__name__}: {e}", file=sys.stderr)
        if os.environ.get('DEBUG'):
            import traceback
            traceback.print_exc(file=sys.stderr)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: COOLDOWN LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def should_reindex_after_cooldown(project_path: Path, cooldown_seconds: Optional[int] = None) -> bool:
    """Check if cooldown period has expired since last reindex

    Timezone Handling (FIXED IN HYBRID):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - State files may have timezone-naive timestamps (no tzinfo)
    - Comparison requires both datetimes to be timezone-aware
    - Solution: Convert naive → UTC before comparison
    - Safe: Assumes UTC if no timezone (reasonable default)
    - Prevents: TypeError: can't subtract offset-naive and offset-aware datetimes

    Cooldown Source:
    - Uses get_last_reindex_time() (checks ANY reindex: full OR incremental)
    - Rationale: Both operations update index, both should reset cooldown

    Args:
        project_path: Path to project
        cooldown_seconds: Cooldown period in seconds (None = load from config)

    Returns:
        True if cooldown expired or never indexed, False if still in cooldown
    """
    if cooldown_seconds is None:
        config = get_reindex_config()
        cooldown_seconds = config['cooldown_seconds']

    try:
        last_reindex = get_last_reindex_time(project_path)

        # Never indexed → allow reindex
        if last_reindex is None:
            return True

        # Calculate time since last reindex
        now = datetime.now(timezone.utc)

        # Handle timezone-aware and naive datetimes (FIX from hybrid)
        if last_reindex.tzinfo is None:
            last_reindex = last_reindex.replace(tzinfo=timezone.utc)

        elapsed = (now - last_reindex).total_seconds()

        # Cooldown expired?
        return elapsed >= cooldown_seconds

    except Exception:
        # If anything fails, allow reindex (graceful degradation)
        return True


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: FILE FILTERING (PRECISE + CONFIGURABLE)
# ═══════════════════════════════════════════════════════════════════════════

def should_reindex_after_write(file_path: str) -> bool:
    """Check if reindex should run after Write operation

    File Filtering Logic (Layered + Precise):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Include patterns (*.py, *.md, etc.) - configurable
       - Must match at least one include pattern
       - Examples: *.py, *.ts, *.md, *.json

    2. Exclude directories (dist/, build/, etc.) - configurable
       - SPECIAL CASE: logs/state/* always INCLUDED (override exclude)
       - Bug fix: Previous version excluded ALL of logs/
       - Critical: State files are important configs (must be indexed)

    3. Exclude patterns (*_transcript.txt, *.log) - configurable
       - Filename-based exclusions
       - Examples: *_transcript.txt, *_tool_calls.jsonl, *.log

    4. Cooldown check (prevents rapid reindex spam)
       - Uses get_last_reindex_time() (any reindex type)
       - Default: 300 seconds (5 minutes)

    Configuration:
    - Loaded from .claude/config.json (semantic_search.reindex)
    - Sensible defaults (works out of box)
    - Advanced users can tune per-project

    Args:
        file_path: Absolute path to file that was written

    Returns:
        True if should reindex, False if should skip
    """
    config = get_reindex_config()
    file_path_obj = Path(file_path)

    try:
        # Layer 1: Include patterns (extension match)
        include_patterns = config['file_include_patterns']
        if not any(file_path_obj.match(pattern) for pattern in include_patterns):
            return False  # Extension not in include list

        # Layer 2: Exclude directories (BUT check special cases FIRST)
        exclude_dirs = config['file_exclude_dirs']
        logs_state_include = config['logs_state_include']

        if logs_state_include:
            # Special case: logs/state/* always included (important configs)
            # Check if path contains BOTH 'logs' and 'state' components
            parts = file_path_obj.parts
            if 'logs' in parts and 'state' in parts:
                # Check if 'state' comes after 'logs' (is a subdirectory)
                try:
                    logs_idx = parts.index('logs')
                    state_idx = parts.index('state')
                    if state_idx > logs_idx:
                        # This IS logs/state/* → INCLUDE (skip exclude check)
                        pass  # Don't return False, continue to layer 3
                    else:
                        # 'state' exists but not under 'logs' → Normal exclude check
                        for part in parts:
                            if part in exclude_dirs:
                                return False
                except ValueError:
                    # One of the parts not found (shouldn't happen, but defensive)
                    for part in parts:
                        if part in exclude_dirs:
                            return False
            else:
                # Not logs/state/* → Normal exclude check
                for part in parts:
                    if part in exclude_dirs:
                        return False  # In excluded directory
        else:
            # logs_state_include disabled → Normal exclude check for all
            for part in parts:
                if part in exclude_dirs:
                    return False  # In excluded directory

        # Layer 3: Exclude patterns (filename match)
        exclude_patterns = config['file_exclude_patterns']
        if any(file_path_obj.match(pattern) for pattern in exclude_patterns):
            return False  # Matches exclude pattern

        # Layer 4: Cooldown check
        project_path = get_project_root()
        cooldown = config['cooldown_seconds']

        if not should_reindex_after_cooldown(project_path, cooldown):
            return False  # Cooldown still active

        # All checks passed → Reindex
        return True

    except Exception:
        # If anything fails, skip reindex (graceful degradation)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: HOOK WRAPPERS (SIMPLE INTERFACES - PRESERVED FROM ORIGINAL)
# ═══════════════════════════════════════════════════════════════════════════

def auto_reindex_on_session_start(input_data: dict) -> None:
    """Auto-reindex on session start (hook wrapper - ORIGINAL interface preserved)

    Design Rationale (PRESERVED - DO NOT DELETE THIS CONTEXT):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Synchronous execution: No background processes (avoids Claude Code Bug #1481)
      * Bug #1481: Popen with start_new_session=True still blocks Claude Code
      * Root cause: Claude Code waits for ALL child processes (even detached)
      * Discovery: User research into GitHub issues revealed Bug #1481
      * Solution: Use subprocess.run() synchronously within 60s timeout

    - 50-second timeout: Leaves 10s buffer from hook's 60s hard limit
      * Typical incremental: ~5 seconds (well under limit)
      * Full reindex: ~3 minutes (too long, must be manual)
      * Buffer accounts for: hook overhead, state file I/O, error handling

    - Visible errors: capture_output=True (not DEVNULL)
      * Previous version: DEVNULL caused silent failures
      * IndexFlatIP bug went undetected for hours
      * Current: User sees errors immediately, can take action

    - No lock files: Simplified from previous over-engineering
      * Previous: PID-based lock files, stale lock cleanup, concurrency logic
      * Removed: 128 lines of complexity
      * Current: Simple synchronous execution (no concurrency)
      * Commit: 9dcd3c2 - "REFACTOR: Simplify auto-reindex to synchronous execution"

    Interface Design (HYBRID):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - ORIGINAL: Takes full input_data dict (simple for caller)
    - NEW: Delegates to _core() with clean signature (testable)
    - Best of both: Simple interface + clean testing

    Why Keep Full input_data?
    - Future extensibility: Hook input may contain more context
    - Simple caller code: Just pass input_data (one line)
    - Backward compatible: No breaking changes

    Args:
        input_data: Full hook input dict (contains source, context, etc.)

    Returns:
        None (prints messages directly, never raises)
    """
    source = input_data.get('source', 'unknown')
    _reindex_on_session_start_core(source)


def reindex_after_write(file_path: str, cooldown_seconds: Optional[int] = None) -> None:
    """Auto-reindex after Write operation (hook wrapper for post-tool-use)

    Business Logic:
    ━━━━━━━━━━━━━━━━
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. File not indexable (logs/transcript, build artifacts) → Skip
    3. Cooldown active → Skip (prevents rapid reindex spam)
    4. All checks pass → Run incremental (~5s)

    File Filtering:
    - Include: Code (*.py, *.ts), Docs (*.md), Config (*.json)
    - Exclude: Logs (*_transcript.txt), Build (dist/), Dependencies (node_modules/)
    - Special: logs/state/* always included (important configs)

    Cooldown:
    - Default: 300 seconds (5 minutes)
    - Can override per-call (for different hooks)
    - Prevents spam when multiple files modified rapidly

    Args:
        file_path: Absolute path to file that was written
        cooldown_seconds: Optional cooldown override (None = use config)

    Returns:
        None (prints messages directly, never raises)
    """
    try:
        # Step 1: Check prerequisites
        if not read_prerequisites_state():
            return

        # Step 2: Check if file should trigger reindex (includes cooldown check)
        if not should_reindex_after_write(file_path):
            return

        # Step 3: Check if index exists
        project_path = get_project_root()
        if not check_index_exists(project_path):
            return

        # Step 4: Run incremental reindex synchronously (~5 seconds)
        file_name = Path(file_path).name
        print(f"🔄 Updating semantic search index (file modified: {file_name})...")
        success = run_incremental_reindex_sync(project_path)

        if success:
            print("✅ Semantic search index updated\n")
        # Errors already printed by run_incremental_reindex_sync

    except Exception as e:
        # Don't fail hook if auto-indexing fails
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: INTERNAL CORE LOGIC (CLEAN FOR TESTING)
# ═══════════════════════════════════════════════════════════════════════════

def _reindex_on_session_start_core(trigger: str) -> None:
    """Core reindex logic for session start (internal - clean signature for testing)

    Business Logic:
    ━━━━━━━━━━━━━━━━
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. Trigger is 'clear' or 'compact' → Skip (no code changes)
    3. Trigger is 'startup' or 'resume' + no index → Skip with message
    4. Trigger is 'startup' or 'resume' + index exists → Run incremental (~5s)

    Trigger Sources:
    - 'startup': Fresh Claude Code launch
    - 'resume': Session restored after context compaction
    - 'clear': User cleared conversation (no file changes)
    - 'compact': Context compacted (no file changes)

    Why Skip on 'clear'/'compact'?
    - No code changes occurred
    - Reindex would find no changes (Merkle tree detects this)
    - Saves ~5 seconds per clear/compact event

    Args:
        trigger: Session start trigger source

    Returns:
        None (prints messages directly, never raises)
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
