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
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

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

# Config cache (Fix #9: Optimize multiple config loads)
_config_cache: Optional[Dict[str, Any]] = None


def get_reindex_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load reindex configuration with sensible defaults (cached - Fix #9)

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

    Note on logs/ directory:
        - 'logs' NOT in exclude_dirs (so logs/state/ files ARE indexed)
        - Pattern-based exclusion handles transcripts: *_transcript.txt, *_tool_calls.jsonl
        - State files (logs/state/*.json) indexed correctly (no pattern matches them)

    Args:
        force_reload: If True, bypass cache and reload from file

    Returns:
        Dict with configuration values (merged with defaults)

    Raises:
        ValueError: If config contains invalid types (validation enabled)
    """
    global _config_cache

    # Use cache if available (Fix #9: Optimize multiple config loads)
    if _config_cache is not None and not force_reload:
        return _config_cache

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
        ]
    }

    try:
        if config_loader is None:
            return defaults

        config = config_loader.load_config()
        reindex_config = config.get('semantic_search', {}).get('reindex', {})

        # Merge with defaults (user config overrides)
        merged = {**defaults, **reindex_config}

        # Validate config types (Fix #6: Config validation)
        _validate_config(merged)

        # Cache for future calls (Fix #9: Optimize)
        _config_cache = merged
        return merged
    except ValueError as e:
        # Config validation failed - show error but use defaults
        print(f"⚠️  Invalid reindex config: {e}", file=sys.stderr)
        print(f"   Using defaults instead", file=sys.stderr)
        # Cache defaults
        _config_cache = defaults
        return defaults
    except Exception:
        # Graceful degradation: Use defaults
        _config_cache = defaults
        return defaults


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate reindex configuration types (Fix #6: Config validation)

    Raises:
        ValueError: If config contains invalid types
    """
    # Validate cooldown_seconds (must be positive integer)
    cooldown = config.get('cooldown_seconds')
    if not isinstance(cooldown, int) or cooldown <= 0:
        raise ValueError(f"cooldown_seconds must be positive integer, got: {cooldown}")

    # Validate file_include_patterns (must be non-empty list of strings)
    include = config.get('file_include_patterns')
    if not isinstance(include, list):
        raise ValueError(f"file_include_patterns must be list of strings")
    if not include:  # FIX: Issue #13 - Empty list breaks reindex (no files match)
        raise ValueError(f"file_include_patterns cannot be empty (at least one pattern required)")
    if not all(isinstance(p, str) for p in include):
        raise ValueError(f"file_include_patterns must be list of strings")

    # Validate file_exclude_dirs (must be list of strings)
    exclude_dirs = config.get('file_exclude_dirs')
    if not isinstance(exclude_dirs, list) or not all(isinstance(d, str) for d in exclude_dirs):
        raise ValueError(f"file_exclude_dirs must be list of strings")

    # Validate file_exclude_patterns (must be list of strings)
    exclude_patterns = config.get('file_exclude_patterns')
    if not isinstance(exclude_patterns, list) or not all(isinstance(p, str) for p in exclude_patterns):
        raise ValueError(f"file_exclude_patterns must be list of strings")


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

def _acquire_reindex_lock(project_path: Path) -> bool:
    """Try to acquire reindex lock using atomic claim file.

    Concurrency Control (FIX: Issue #1 - Prevents index corruption):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Uses atomic file creation (os.O_CREAT | os.O_EXCL) to prevent concurrent
    reindex operations that could corrupt the FAISS index.

    Context:
    - Original design (commit 9dcd3c2): Removed locking, assumed no concurrency
    - Assumption valid for session-start only (sequential execution)
    - Post-tool-use reindex broke assumption (parallel Write operations possible)
    - This fix restores concurrency safety with minimal complexity

    Why atomic claim file instead of fcntl.flock:
    - Simpler (no cross-platform considerations)
    - Stale lock detection (check file age)
    - PID tracking for debugging
    - Follows Unix philosophy (everything is a file)

    Stale lock handling:
    - If claim file exists and is > 60s old, it's stale (process crashed)
    - Remove stale claim and try again
    - Timeout of 60s chosen because: reindex timeout is 50s, + 10s buffer

    Race conditions handled:
    - Check-then-remove stale: If two processes both see stale and remove,
      only one will succeed at creating new claim (os.O_EXCL is atomic)
    - File removed between check and create: FileNotFoundError on stat,
      caught and treated as "already removed by another process"

    Args:
        project_path: Path to project

    Returns:
        True if lock acquired, False if another process is reindexing
    """
    claim_file = get_project_storage_dir(project_path) / '.reindex_claim'

    # Check for existing claim (stale or active)
    if claim_file.exists():
        try:
            # Check age
            age = time.time() - claim_file.stat().st_mtime
            if age > 60:
                # Stale claim (process crashed or timed out)
                try:
                    claim_file.unlink()
                except FileNotFoundError:
                    pass  # Another process removed it
            else:
                # Recent claim, active reindex in progress
                return False
        except FileNotFoundError:
            # File removed between exists() and stat() - continue to create
            pass

    # Try to create claim file atomically
    try:
        claim_data = f"{os.getpid()}:{time.time():.3f}"
        fd = os.open(str(claim_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        try:
            os.write(fd, claim_data.encode())
        finally:
            os.close(fd)  # FIX: Always close fd, prevents fd leak
        return True  # Lock acquired
    except FileExistsError:
        # Another process created the file between our check and create
        return False
    except Exception:
        # Write or close failed - clean up partial claim file (FIX: prevents 60s block)
        try:
            claim_file.unlink()
        except Exception:
            pass  # Best effort cleanup
        raise  # Propagate error to caller


def _release_reindex_lock(project_path: Path) -> None:
    """Release reindex lock by removing claim file (best effort, never raises).

    FIX: Catch all exceptions to prevent masking original exceptions from finally block.
    If cleanup fails (PermissionError, OSError), stale lock detection handles it (60s timeout).

    Args:
        project_path: Path to project
    """
    try:
        claim_file = get_project_storage_dir(project_path) / '.reindex_claim'
        claim_file.unlink()
    except Exception:  # FIX: Catch ALL exceptions, not just FileNotFoundError
        # Best effort cleanup - don't propagate exceptions from cleanup code
        # Stale lock detection will remove leaked locks after 60s
        pass


def run_incremental_reindex_sync(project_path: Path) -> Optional[bool]:
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

    - Atomic claim file locking (FIX: Issue #1 - Restored for post-tool-use)
      * Original: Had lock files, removed in commit 9dcd3c2 (no concurrency)
      * That assumption broke with post-tool-use reindex (parallel Writes possible)
      * Current: Lightweight atomic claim file prevents concurrent reindex
      * Stale lock detection: 60s timeout (reindex timeout 50s + 10s buffer)
      * Trade-off: Simple locking, handles 99.9% of cases, minimal complexity

    Performance:
    - Typical: ~2-5 seconds (Merkle tree detects changed files)
    - Worst case: ~50 seconds (timeout, then abort)
    - Best case: <1 second (no changes detected)

    Args:
        project_path: Path to project

    Returns:
        True if successful, False if failed, None if skipped (another process reindexing)
        (FIX: Issue #15 - Return None to indicate "skipped, not failed")
    """
    try:
        project_root = get_project_root()
        script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental-reindex'

        # Pre-flight check: Script exists?
        if not script.exists():
            print(f"⚠️  Reindex script not found: {script}", file=sys.stderr)
            print(f"   Skill may not be installed correctly", file=sys.stderr)
            return False

        # Acquire lock to prevent concurrent reindex (FIX: Issue #1)
        if not _acquire_reindex_lock(project_path):
            # Another process is reindexing, skip silently
            # FIX: Issue #15 - Return None to indicate "skipped" (not success/failure)
            # Prevents misleading "index updated" message when we didn't do anything
            return None

        try:
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
        finally:
            # Always release lock, even if reindex failed
            _release_reindex_lock(project_path)

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

        # FIX: Issue #14 - Handle future timestamps (clock skew or tampering)
        if elapsed < 0:
            # Timestamp is in future - likely clock skew or manual state file edit
            # Treat as stale, allow reindex (safer than blocking forever)
            return True

        # Cooldown expired?
        return elapsed >= cooldown_seconds

    except Exception:
        # If anything fails, allow reindex (graceful degradation)
        return True


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: FILE FILTERING (PRECISE + CONFIGURABLE)
# ═══════════════════════════════════════════════════════════════════════════

def should_reindex_after_write(file_path: str, cooldown_seconds: Optional[int] = None) -> bool:
    """Check if reindex should run after Write operation

    File Filtering Logic (4-Layer Filter):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Include patterns (*.py, *.md, *.json, etc.) - configurable
       - Must match at least one include pattern
       - Typical: Code, docs, config files

    2. Exclude directories (dist/, build/, node_modules/, etc.) - configurable
       - Simple directory check (no special cases)
       - Note: 'logs' NOT in default excludes
       - Why: Pattern-based exclusion handles log files (see Layer 3)

    3. Exclude patterns (*_transcript.txt, *.log, etc.) - configurable
       - Filename-based exclusions
       - Handles: Session transcripts, tool call logs, temp files
       - Example: logs/session_*_transcript.txt → excluded by pattern

    4. Cooldown check (prevents rapid reindex spam)
       - Uses get_last_reindex_time() (any reindex type)
       - Default: 300 seconds (5 minutes)
       - Override: Pass cooldown_seconds parameter

    How logs/ Directory is Handled:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Directory-level: 'logs' NOT excluded (all *.json files checked)
    - Pattern-level: *_transcript.txt, *_tool_calls.jsonl → excluded
    - Result: logs/state/*.json indexed ✓, session logs excluded ✓

    Configuration:
    - Loaded from .claude/config.json (semantic_search.reindex)
    - Sensible defaults (works out of box)
    - Advanced users can tune per-project
    - Note: User config REPLACES defaults (not merged) - see Fix #7

    Args:
        file_path: Absolute path to file that was written
        cooldown_seconds: Optional cooldown override (None = use config)

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

        # Layer 2: Exclude directories (simple check - Fix #2: Removed unnecessary complexity)
        exclude_dirs = config['file_exclude_dirs']
        for part in file_path_obj.parts:
            if part in exclude_dirs:
                return False  # In excluded directory

        # Layer 3: Exclude patterns (filename match)
        exclude_patterns = config['file_exclude_patterns']
        if any(file_path_obj.match(pattern) for pattern in exclude_patterns):
            return False  # Matches exclude pattern

        # Layer 4: Cooldown check (Fix #1, #5: Use parameter if provided)
        project_path = get_project_root()
        cooldown = cooldown_seconds if cooldown_seconds is not None else config['cooldown_seconds']

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
    """Auto-reindex after file modification operations (Write/Edit/NotebookEdit)

    Business Logic:
    ━━━━━━━━━━━━━━━━
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. File not indexable (logs/transcript, build artifacts) → Skip
    3. Cooldown active → Skip (prevents rapid reindex spam)
    4. All checks pass → Run incremental (~5s)

    File Filtering:
    - Include: Code (*.py, *.ts), Docs (*.md), Config (*.json)
    - Exclude directories: dist/, build/, node_modules/
    - Exclude patterns: *_transcript.txt, *_tool_calls.jsonl, *.log
    - How logs/ works: Directory NOT excluded, pattern-based filtering for transcripts

    Cooldown:
    - Default: 300 seconds (5 minutes)
    - Can override per-call (for different hooks)
    - Prevents spam when multiple files modified rapidly

    Args:
        file_path: Absolute path to file that was written, modified, or edited
        cooldown_seconds: Optional cooldown override (None = use config)

    Returns:
        None (prints messages directly, never raises)
    """
    try:
        # Step 1: Check prerequisites
        if not read_prerequisites_state():
            return

        # Step 2: Check if file should trigger reindex (Fix #1: Pass cooldown parameter)
        if not should_reindex_after_write(file_path, cooldown_seconds):
            return

        # Step 3: Check if index exists
        project_path = get_project_root()
        if not check_index_exists(project_path):
            return

        # Step 4: Run incremental reindex synchronously (~5 seconds)
        file_name = Path(file_path).name
        print(f"🔄 Updating semantic search index (file modified: {file_name})...")
        result = run_incremental_reindex_sync(project_path)

        # FIX: Issue #15 - Handle None (skipped), True (success), False (failed)
        if result is True:
            print("✅ Semantic search index updated\n")
        elif result is None:
            # Skipped (another process is reindexing) - no message needed
            pass
        # If False: Errors already printed by run_incremental_reindex_sync

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
        result = run_incremental_reindex_sync(project_path)

        # FIX: Issue #15 - Handle None (skipped), True (success), False (failed)
        if result is True:
            print("✅ Semantic search index updated\n")
        elif result is None:
            # Skipped (another process is reindexing) - no message needed
            pass
        # If False: Errors already printed by run_incremental_reindex_sync

    except Exception as e:
        # Don't fail hook if auto-indexing fails
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)
