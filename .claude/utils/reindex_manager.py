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
import signal
import time
import random
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
            - IndexFlatIP auto-fallback: Full reindex always happens (3-10 min)
            - User can tune per-project needs

        file_include_patterns: Extensions to index
            - Code: *.py, *.ts, *.js, *.tsx, *.jsx, *.go, *.rs, *.java, *.c, *.cpp, etc.
            - Docs: *.md, *.txt, *.rst, *.adoc, *.org
            - Config: *.json, *.yaml, *.yml, *.toml, *.ini, *.xml, etc.

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

def _kill_existing_reindex_process(project_path: Path) -> bool:
    """Kill existing reindex process if found (parent-only operation, does NOT acquire lock).

    Architectural Role:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    This is a PARENT-ONLY function for implementing kill-if-held behavior.
    - Previously used by run_incremental_reindex_sync() (DELETED 2025-12-15)
    - Kills existing process but does NOT acquire lock
    - Subprocess will acquire lock after parent spawns it

    Clean Separation of Concerns:
    - Parent: Decides whether to kill (this function)
    - Subprocess: Acquires lock, runs reindex, releases lock
    - No shared lock ownership!

    Args:
        project_path: Path to project

    Returns:
        True if killed or no process found, False if failed to kill
    """
    storage_dir = get_project_storage_dir(project_path)
    claim_file = storage_dir / '.reindex_claim'

    # Check if claim file exists
    if not claim_file.exists():
        return True  # No process running

    try:
        # Check age
        age = time.time() - claim_file.stat().st_mtime
        if age > 60:
            # Stale claim (process crashed or timed out) - remove it
            try:
                claim_file.unlink()
            except FileNotFoundError:
                pass
            return True

        # Recent claim - try to kill the process
        # Step 1: Parse PID from claim file
        try:
            claim_content = claim_file.read_text().strip()
            pid = int(claim_content.split(':')[0])
        except (ValueError, IndexError, FileNotFoundError, OSError) as e:
            # Corrupted or unreadable - remove and return success
            print(f"DEBUG: Corrupted claim file, removing: {e}", file=sys.stderr)
            try:
                claim_file.unlink()
            except FileNotFoundError:
                pass
            return True

        # Step 2: Verify PID is running incremental-reindex
        process_verified = False
        try:
            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'command='],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                command = result.stdout.strip()
                if 'incremental-reindex' in command or 'incremental_reindex.py' in command:
                    process_verified = True
                    print(f"DEBUG: Verified PID {pid} running incremental-reindex", file=sys.stderr)
                else:
                    # Not our process - don't kill it
                    print(f"DEBUG: PID {pid} not incremental-reindex (cmd: {command[:80]}), not killing", file=sys.stderr)
                    return False
            else:
                # Process doesn't exist - remove stale claim
                try:
                    claim_file.unlink()
                except FileNotFoundError:
                    pass
                return True
        except Exception as e:
            print(f"DEBUG: ps command failed ({e}), removing claim file", file=sys.stderr)
            try:
                claim_file.unlink()
            except:
                pass
            return True

        # Step 3: Kill the verified process (max 3 retries)
        if process_verified:
            killed = False
            for attempt in range(3):
                print(f"DEBUG: Kill attempt {attempt + 1}/3 for PID {pid}", file=sys.stderr)
                try:
                    # Try process group kill first
                    try:
                        os.killpg(pid, signal.SIGTERM)
                        time.sleep(0.5)
                        os.killpg(pid, signal.SIGKILL)
                        print(f"DEBUG: Sent SIGTERM+SIGKILL to process group {pid}", file=sys.stderr)
                    except (ProcessLookupError, OSError) as e:
                        # Try regular kill
                        print(f"DEBUG: Process group kill failed ({e}), trying regular kill", file=sys.stderr)
                        try:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.5)
                            os.kill(pid, signal.SIGKILL)
                            print(f"DEBUG: Sent SIGTERM+SIGKILL to process {pid}", file=sys.stderr)
                        except ProcessLookupError:
                            print(f"DEBUG: Process {pid} already dead", file=sys.stderr)
                        except PermissionError:
                            print(f"⚠️  Cannot kill reindex process {pid} (permission denied)", file=sys.stderr)
                            return False
                    except PermissionError:
                        print(f"⚠️  Cannot kill reindex process group {pid} (permission denied)", file=sys.stderr)
                        return False

                    # Verify process died
                    time.sleep(0.2)
                    try:
                        os.kill(pid, 0)  # Check if exists
                        print(f"DEBUG: Process {pid} still alive after kill", file=sys.stderr)
                        if attempt == 2:
                            print(f"⚠️  Reindex process {pid} won't die after 3 attempts", file=sys.stderr)
                            return False
                        time.sleep(0.5)
                        continue
                    except ProcessLookupError:
                        # Process dead!
                        print(f"DEBUG: Process {pid} successfully killed", file=sys.stderr)
                        killed = True

                    # Remove claim file
                    try:
                        claim_file.unlink()
                        print(f"DEBUG: Removed claim file", file=sys.stderr)
                    except FileNotFoundError:
                        pass
                    except PermissionError as e:
                        print(f"⚠️  Cannot remove claim file: {e}", file=sys.stderr)

                    time.sleep(random.uniform(0.1, 0.5))
                    break

                except ProcessLookupError:
                    # Already dead
                    try:
                        claim_file.unlink()
                    except FileNotFoundError:
                        pass
                    killed = True
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f"⚠️  Failed to kill reindex after 3 attempts: {e}", file=sys.stderr)
                        return False
                    time.sleep(random.uniform(0.1, 0.5))

            return killed

        return True

    except FileNotFoundError:
        # Claim file disappeared
        return True
    except Exception as e:
        print(f"DEBUG: Unexpected error in kill process: {e}", file=sys.stderr)
        return False


def _acquire_reindex_lock(project_path: Path, kill_if_held: bool = True) -> bool:
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
    storage_dir = get_project_storage_dir(project_path)
    claim_file = storage_dir / '.reindex_claim'
    print(f"DEBUG _acquire_reindex_lock: claim_file = {claim_file}", file=sys.stderr)
    print(f"DEBUG _acquire_reindex_lock: storage_dir exists = {storage_dir.exists()}", file=sys.stderr)

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
                # Recent claim (<60s) - behavior depends on kill_if_held parameter
                # kill_if_held=True: Kill and restart (synchronous hook context)
                # kill_if_held=False: Skip if process running (background script context)

                # Step 1: Parse PID from claim file
                try:
                    claim_content = claim_file.read_text().strip()
                    pid = int(claim_content.split(':')[0])
                except (ValueError, IndexError, FileNotFoundError, OSError) as e:
                    # Corrupted or unreadable - remove and continue to atomic creation
                    print(f"DEBUG: Corrupted claim file, removing: {e}", file=sys.stderr)
                    try:
                        claim_file.unlink()
                    except FileNotFoundError:
                        pass
                    # Fall through to atomic creation (don't return here)
                else:
                    # Successfully parsed PID
                    # Step 2: Verify PID is running incremental-reindex (SAFETY: prevent killing wrong process)
                    process_verified = False
                    try:
                        result = subprocess.run(
                            ['ps', '-p', str(pid), '-o', 'command='],
                            capture_output=True,
                            text=True,
                            timeout=1
                        )
                        if result.returncode == 0:
                            command = result.stdout.strip()
                            # Kill-and-restart ONLY for incremental-reindex processes
                            # Check for both hyphen (bash script) and underscore (Python script)
                            if 'incremental-reindex' in command or 'incremental_reindex.py' in command:
                                # Production reindex process found
                                process_verified = True
                                print(f"DEBUG: Verified PID {pid} running incremental-reindex", file=sys.stderr)

                                # If kill_if_held=False, just skip (don't kill)
                                if not kill_if_held:
                                    print(f"DEBUG: Another reindex running (PID {pid}), skipping (kill_if_held=False)", file=sys.stderr)
                                    return False
                            else:
                                # Process exists but is NOT incremental-reindex
                                # This could be:
                                # - Test process (pytest, multiprocessing worker, etc.)
                                # - Unrelated process (PID genuinely reused)
                                # SAFE: Respect the lock and return False (don't remove claim)
                                # This prevents killing test processes and respects valid locks
                                print(f"DEBUG: PID {pid} not incremental-reindex (cmd: {command[:80]}), respecting lock", file=sys.stderr)
                                return False  # Abort - other process owns the lock
                        else:
                            # Process doesn't exist but claim is RECENT (<60s)
                            # Process may have just finished - respect the lock window
                            print(f"DEBUG: PID {pid} doesn't exist but claim is recent, respecting lock", file=sys.stderr)
                            return False  # Respect recent claim even if process gone
                    except Exception as e:
                        # ps command failed - assume stale
                        print(f"DEBUG: ps command failed ({e}), assuming stale claim", file=sys.stderr)
                        try:
                            claim_file.unlink()
                        except:
                            pass

                    # Step 3: If process verified, try to kill it (max 3 retries with random delays)
                    if process_verified:
                        killed = False
                        for attempt in range(3):
                            print(f"DEBUG: Kill attempt {attempt + 1}/3 for PID {pid}", file=sys.stderr)
                            try:
                                # Try process group kill first (preferred - kills bash wrapper + Python subprocess)
                                try:
                                    os.killpg(pid, signal.SIGTERM)
                                    time.sleep(0.5)
                                    os.killpg(pid, signal.SIGKILL)
                                    print(f"DEBUG: Sent SIGTERM+SIGKILL to process group {pid}", file=sys.stderr)
                                except (ProcessLookupError, OSError) as e:
                                    # Process group kill failed - try regular kill
                                    print(f"DEBUG: Process group kill failed ({e}), trying regular kill", file=sys.stderr)
                                    try:
                                        os.kill(pid, signal.SIGTERM)
                                        time.sleep(0.5)
                                        os.kill(pid, signal.SIGKILL)
                                        print(f"DEBUG: Sent SIGTERM+SIGKILL to process {pid}", file=sys.stderr)
                                    except ProcessLookupError:
                                        print(f"DEBUG: Process {pid} already dead", file=sys.stderr)
                                    except PermissionError:
                                        # Can't kill - not our process (DECISION: return False)
                                        print(f"⚠️  Cannot kill reindex process {pid} (permission denied)", file=sys.stderr)
                                        return False  # Skip reindex
                                except PermissionError:
                                    # Process group permission denied (DECISION: return False)
                                    print(f"⚠️  Cannot kill reindex process group {pid} (permission denied)", file=sys.stderr)
                                    return False  # Skip reindex

                                # Verify process actually died (SAFETY: check before claiming success)
                                time.sleep(0.2)  # Brief wait for process to die
                                try:
                                    os.kill(pid, 0)  # Check if process exists
                                    # Process still alive!
                                    print(f"DEBUG: Process {pid} still alive after kill", file=sys.stderr)
                                    if attempt == 2:  # Last attempt (DECISION: return False after 3 attempts)
                                        print(f"⚠️  Reindex process {pid} won't die after 3 attempts", file=sys.stderr)
                                        return False  # Give up
                                    time.sleep(0.5)  # Wait longer before retry
                                    continue  # Retry
                                except ProcessLookupError:
                                    # Process dead - success!
                                    print(f"DEBUG: Process {pid} successfully killed", file=sys.stderr)
                                    killed = True

                                # Remove claim file (best effort)
                                try:
                                    claim_file.unlink()
                                    print(f"DEBUG: Removed claim file", file=sys.stderr)
                                except FileNotFoundError:
                                    pass  # Already gone
                                except PermissionError as e:
                                    # Can't remove - log but continue (atomic creation might fail)
                                    print(f"⚠️  Cannot remove claim file: {e}", file=sys.stderr)

                                # Random delay to prevent race conditions
                                delay = random.uniform(0.1, 0.5)
                                print(f"DEBUG: Random delay {delay:.3f}s", file=sys.stderr)
                                time.sleep(delay)
                                break  # Success - exit retry loop

                            except ProcessLookupError:
                                # Process already dead during kill
                                print(f"DEBUG: Process {pid} already dead during kill", file=sys.stderr)
                                try:
                                    claim_file.unlink()
                                except FileNotFoundError:
                                    pass
                                killed = True
                                break  # Success

                            except Exception as e:
                                # Unexpected error
                                if attempt == 2:  # Last attempt
                                    print(f"⚠️  Failed to kill reindex after 3 attempts: {e}", file=sys.stderr)
                                    return False  # Give up
                                time.sleep(random.uniform(0.1, 0.5))

                        if not killed:
                            # All retries exhausted
                            return False
                    # else: process not verified (not running or wrong process), fall through to atomic creation
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


def spawn_background_reindex(project_path: Path, trigger: str = 'unknown') -> bool:
    """Spawn background reindex using PROVEN pattern from OLD code (pre-9dcd3c2)

    Design Rationale:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    This function uses the EXACT pattern that worked in OLD session-start.py
    and post-tool-use.py hooks before commit 9dcd3c2. Pattern proven to:
    - Spawn truly detached background process
    - Complete full reindex without blocking hook
    - Work with kill-and-restart architecture for safety

    Key Differences from Synchronous Version:
    - stdout/stderr: DEVNULL (not PIPE) → no output buffering
    - NO communicate() call → hook exits immediately
    - NO timeout → process runs to completion
    - Lock managed BY SCRIPT (not by this function)

    Lock Management:
    - incremental_reindex.py manages its own locks
    - Script acquires lock at start, releases at end
    - If lock held, script exits immediately (skipped)
    - Hook just spawns unconditionally

    Performance:
    - Hook overhead: <100ms (just spawn, no waiting)
    - Full reindex: 3-10 minutes (completes in background)
    - User experience: Hook exits immediately, index updates silently

    Args:
        project_path: Path to project
        trigger: Trigger source for logging (first-prompt, stop-hook, etc.)

    Returns:
        True if process spawned successfully, False if script not found
    """
    try:
        project_root = get_project_root()
        script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental-reindex'

        # Pre-flight check: Script exists?
        if not script.exists():
            print(f"⚠️  Reindex script not found: {script}", file=sys.stderr)
            print(f"   Skill may not be installed correctly", file=sys.stderr)
            return False

        # PROVEN PATTERN: Popen + DEVNULL + start_new_session + NO communicate()
        # This is the EXACT pattern from OLD session-start.py (commit 9dcd3c2^)
        proc = subprocess.Popen(
            [str(script), str(project_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True  # Create new process group (detach from parent)
        )
        # DO NOT call communicate() - hook exits immediately, process continues

        # Log operation start (NEW: Forensic diagnostics)
        log_reindex_start(
            trigger=trigger,
            mode='background',
            pid=proc.pid,
            kill_if_held=False,  # Background mode doesn't use kill-if-held
            skipped=False
        )

        return True

    except Exception as e:
        # Unexpected errors during spawn
        print(f"⚠️  Failed to spawn background reindex: {type(e).__name__}: {e}", file=sys.stderr)
        if os.environ.get('DEBUG'):
            import traceback
            traceback.print_exc(file=sys.stderr)
        return False


def reindex_on_stop_background(cooldown_seconds: Optional[int] = None) -> dict:
    """Auto-reindex on stop hook using background pattern (follows first-prompt architecture)

    NEW Architecture: Background spawn (no timeout) instead of synchronous (50s timeout)
    - OLD: Synchronous with 50s timeout → fails for reindexes > 50s
    - NEW: Background spawn → completes 200-350s reindexes successfully
    - BENEFIT: No timeout failures, matches first-prompt's proven pattern

    Trigger Behavior (from official docs at code.claude.com/docs/en/hooks):
    - Fires when "main Claude Code agent has finished responding"
    - Does NOT fire "if stoppage occurred due to a user interrupt"
    - Fires ONCE per conversation turn (NOT after each spawned agent)

    Business Logic (Gate Checks):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. Cooldown active → Skip (prevents spam on rapid conversation turns)
    3. Concurrent reindex running → Skip (prevents orphaned START events)
    4. All checks pass → Spawn background reindex

    Differences from First-Prompt:
    - ADDS prerequisites check (first-prompt has no prerequisites gate)
    - ADDS cooldown check (first-prompt has one-time gate instead)
    - ADDS concurrent PID check (prevents orphaned START events in forensic logs)
    - KEEPS decision dict return (stop.py needs it for session logging)

    Differences from Old reindex_on_stop():
    - REMOVES index exists check (script creates index if missing - TRUE redundancy)
    - REPLACES synchronous call with background spawn
    - REMOVES 50s timeout (background mode has no timeout)
    - CHANGES decision codes (reindex_spawned vs reindex_success/failed)

    Args:
        cooldown_seconds: Optional cooldown override (None = use config, default 300s)

    Returns:
        dict: Decision data with keys:
            - decision: "skip" or "run"
            - reason: Human-readable reason code
            - details: Additional context (structured dict)
            - timestamp: ISO timestamp of decision
    """

    # ═══════════════════════════════════════════════════════════════════
    # SECTION 1: Initialize (KEEP - stop.py needs timestamp in dict)
    # ═══════════════════════════════════════════════════════════════════
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        # ═══════════════════════════════════════════════════════════════
        # SECTION 2: Gate Check - Prerequisites (KEEP - unique to stop-hook)
        # ═══════════════════════════════════════════════════════════════
        # REASON: Prevents spawning doomed reindex when skill not installed
        if not read_prerequisites_state():
            return {
                "decision": "skip",
                "reason": "prerequisites_not_ready",
                "details": {
                    "trigger": "stop_hook",
                    "state_file": "logs/state/semantic-search-prerequisites.json"
                },
                "timestamp": timestamp
            }

        # ═══════════════════════════════════════════════════════════════
        # SECTION 3: Gate Check - Cooldown (KEEP - unique to stop-hook)
        # ═══════════════════════════════════════════════════════════════
        # REASON: Prevents spam spawning on rapid session restarts
        project_path = get_project_root()
        config = get_reindex_config()
        cooldown = cooldown_seconds if cooldown_seconds is not None else config['cooldown_seconds']

        if not should_reindex_after_cooldown(project_path, cooldown):
            last_reindex = get_last_reindex_time(project_path)
            elapsed = 0
            if last_reindex:
                now = datetime.now(timezone.utc)
                if last_reindex.tzinfo is None:
                    last_reindex = last_reindex.replace(tzinfo=timezone.utc)
                elapsed = (now - last_reindex).total_seconds()

            return {
                "decision": "skip",
                "reason": "cooldown_active",
                "details": {
                    "trigger": "stop_hook",
                    "cooldown_seconds": cooldown,
                    "elapsed_seconds": int(elapsed),
                    "remaining_seconds": int(cooldown - elapsed)
                },
                "timestamp": timestamp
            }

        # ═══════════════════════════════════════════════════════════════
        # SECTION 4: Gate Check - Concurrent PID (ADD - prevents orphaned events)
        # ═══════════════════════════════════════════════════════════════
        # CRITICAL: Script exits at line 690 BEFORE finally block at line 703
        # If script detects concurrent, NO END event logged (orphaned START)
        # Parent check logs START with skipped=True, preventing orphaned events
        storage_dir = get_project_storage_dir(project_path)
        claim_file = storage_dir / '.reindex_claim'  # underscore, not dash!

        if claim_file.exists():
            try:
                # Parse PID from claim file
                claim_content = claim_file.read_text().strip()
                pid = int(claim_content.split(':')[0])

                # Verify process exists and is incremental-reindex
                result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'command='],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # PID exists - verify it's our process
                    command = result.stdout.strip()
                    if 'incremental-reindex' in command or 'incremental_reindex.py' in command:
                        # Process verified - truly concurrent reindex running
                        # Log START event with skipped=True (prevents orphaned event)
                        log_reindex_start(
                            trigger='stop-hook',
                            mode='background',
                            pid=None,
                            skipped=True,
                            skip_reason='concurrent_reindex'
                        )
                        return {
                            "decision": "skip",
                            "reason": "concurrent_reindex",
                            "details": {
                                "trigger": "stop_hook",
                                "concurrent_pid": pid
                            },
                            "timestamp": timestamp
                        }
                    else:
                        # PID alive but wrong process - orphaned claim
                        claim_file.unlink()
                else:
                    # PID dead - orphaned claim from crash/kill
                    claim_file.unlink()

            except (ValueError, IndexError, FileNotFoundError, OSError):
                # Corrupted/invalid claim - remove and continue
                try:
                    claim_file.unlink()
                except FileNotFoundError:
                    pass

        # ═══════════════════════════════════════════════════════════════
        # SECTION 5: Show Message (COPY from first-prompt)
        # ═══════════════════════════════════════════════════════════════
        # REASON: User wants visibility, message shows even if spawn fails
        print("🔄 Checking for index updates in background...", flush=True)

        # ═══════════════════════════════════════════════════════════════
        # SECTION 6: Spawn Background (COPY from first-prompt)
        # ═══════════════════════════════════════════════════════════════
        # NO index exists check - script handles missing index (TRUE redundancy)
        # Script creates empty index (line 88), loads existing (line 103),
        # populates via full reindex (line 548)
        spawned = spawn_background_reindex(project_path, trigger='stop-hook')

        # ═══════════════════════════════════════════════════════════════
        # SECTION 7: Return Decision Dict (KEEP structure, MODIFY codes)
        # ═══════════════════════════════════════════════════════════════
        # REASON: stop.py session logging needs dict (lines 119-141)
        # MODIFIED: Decision codes for background mode (can't know success/failure)

        if spawned:
            # Process spawned successfully
            # ✅ FORENSIC LOGGING: spawn_background_reindex already logged START event (line 1149-1155)
            # ⏳ END EVENT: Will be logged by script's finally block when done (line 735-754)
            return {
                "decision": "run",
                "reason": "reindex_spawned",  # MODIFIED: was reindex_success/failed
                "details": {"trigger": "stop_hook"},
                "timestamp": timestamp
            }
        else:
            # Script not found (rare - installation issue)
            return {
                "decision": "skip",
                "reason": "script_not_found",
                "details": {"trigger": "stop_hook"},
                "timestamp": timestamp
            }

    except Exception as e:
        # ═══════════════════════════════════════════════════════════════
        # SECTION 8: Exception Handling (KEEP - stop.py expects dict)
        # ═══════════════════════════════════════════════════════════════
        # REASON: Hook must not crash, stop.py expects dict return
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)
        return {
            "decision": "skip",
            "reason": "exception",
            "details": {"trigger": "stop_hook", "error": str(e)},
            "timestamp": timestamp
        }


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: COOLDOWN LOGIC
# ═══════════════════════════════════════════════════════════════════════════

def get_reindex_timing_analysis(project_path: Path, cooldown_seconds: Optional[int] = None) -> dict:
    """Get formatted timing analysis for reindex operations

    Returns structured data with explicit timezone labels to prevent
    timezone confusion in analysis. Use this function's output directly
    for reporting - NEVER calculate timestamps mentally.

    Args:
        project_path: Path to project
        cooldown_seconds: Cooldown period in seconds (None = load from config)

    Returns:
        dict with keys:
            - has_previous_reindex: bool
            - last_reindex_utc: str (HH:MM:SS UTC) or None
            - last_reindex_local: str (HH:MM:SS TZ) or None
            - current_utc: str (HH:MM:SS UTC)
            - current_local: str (HH:MM:SS TZ)
            - elapsed_seconds: float or None
            - elapsed_minutes: float or None
            - elapsed_display: str or None
            - cooldown_seconds: int
            - cooldown_expired: bool
            - cooldown_status: str (human-readable)
    """
    if cooldown_seconds is None:
        config = get_reindex_config()
        cooldown_seconds = config['cooldown_seconds']

    try:
        last_reindex = get_last_reindex_time(project_path)
        now_utc = datetime.now(timezone.utc)

        # No previous reindex
        if last_reindex is None:
            return {
                'has_previous_reindex': False,
                'last_reindex_utc': None,
                'last_reindex_local': None,
                'current_utc': now_utc.strftime("%H:%M:%S UTC"),
                'current_local': now_utc.astimezone().strftime("%H:%M:%S %Z"),
                'elapsed_seconds': None,
                'elapsed_minutes': None,
                'elapsed_display': 'Never indexed',
                'cooldown_seconds': cooldown_seconds,
                'cooldown_expired': True,
                'cooldown_status': 'No previous reindex (cooldown N/A)'
            }

        # Handle timezone-naive timestamps
        if last_reindex.tzinfo is None:
            last_reindex = last_reindex.replace(tzinfo=timezone.utc)

        # Calculate elapsed
        elapsed_seconds = (now_utc - last_reindex).total_seconds()
        elapsed_minutes = elapsed_seconds / 60

        # Format elapsed time
        if elapsed_seconds < 0:
            elapsed_display = f"{-elapsed_seconds:.0f} sec in future (clock skew)"
            cooldown_expired = True  # Allow reindex
            cooldown_status = 'Future timestamp (clock skew) - cooldown bypassed'
        elif elapsed_seconds < 60:
            elapsed_display = f"{elapsed_seconds:.0f} sec"
            cooldown_expired = elapsed_seconds >= cooldown_seconds
            if cooldown_expired:
                cooldown_status = f'Cooldown expired ({elapsed_seconds:.0f}s >= {cooldown_seconds}s)'
            else:
                remaining = cooldown_seconds - elapsed_seconds
                cooldown_status = f'Cooldown active ({remaining:.0f}s remaining)'
        elif elapsed_seconds < 3600:
            minutes = int(elapsed_seconds // 60)
            secs = int(elapsed_seconds % 60)
            elapsed_display = f"{minutes} min {secs} sec"
            cooldown_expired = elapsed_seconds >= cooldown_seconds
            if cooldown_expired:
                cooldown_status = f'Cooldown expired ({elapsed_minutes:.1f} min >= {cooldown_seconds / 60:.1f} min)'
            else:
                remaining = cooldown_seconds - elapsed_seconds
                cooldown_status = f'Cooldown active ({remaining / 60:.1f} min remaining)'
        else:
            hours = int(elapsed_seconds // 3600)
            minutes = int((elapsed_seconds % 3600) // 60)
            elapsed_display = f"{hours} hr {minutes} min"
            cooldown_expired = elapsed_seconds >= cooldown_seconds
            if cooldown_expired:
                cooldown_status = f'Cooldown expired ({elapsed_minutes:.1f} min >= {cooldown_seconds / 60:.1f} min)'
            else:
                remaining = cooldown_seconds - elapsed_seconds
                cooldown_status = f'Cooldown active ({remaining / 60:.1f} min remaining)'

        # Convert to local timezone for display
        last_reindex_local = last_reindex.astimezone()
        now_local = now_utc.astimezone()

        return {
            'has_previous_reindex': True,
            'last_reindex_utc': last_reindex.strftime("%H:%M:%S UTC"),
            'last_reindex_local': last_reindex_local.strftime("%H:%M:%S %Z"),
            'current_utc': now_utc.strftime("%H:%M:%S UTC"),
            'current_local': now_local.strftime("%H:%M:%S %Z"),
            'elapsed_seconds': elapsed_seconds,
            'elapsed_minutes': elapsed_minutes,
            'elapsed_display': elapsed_display,
            'cooldown_seconds': cooldown_seconds,
            'cooldown_expired': cooldown_expired,
            'cooldown_status': cooldown_status
        }

    except Exception as e:
        # Graceful fallback
        now_utc = datetime.now(timezone.utc)
        return {
            'has_previous_reindex': False,
            'last_reindex_utc': None,
            'last_reindex_local': None,
            'current_utc': now_utc.strftime("%H:%M:%S UTC"),
            'current_local': now_utc.astimezone().strftime("%H:%M:%S %Z"),
            'elapsed_seconds': None,
            'elapsed_minutes': None,
            'elapsed_display': f'Error: {str(e)}',
            'cooldown_seconds': cooldown_seconds or 300,
            'cooldown_expired': True,  # Allow reindex on error
            'cooldown_status': f'Error checking timing: {str(e)}'
        }


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
    # Use new timing analysis function for consistent behavior
    timing = get_reindex_timing_analysis(project_path, cooldown_seconds)
    return timing['cooldown_expired']
# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: INTERNAL CORE LOGIC (CLEAN FOR TESTING)
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: SESSION REINDEX STATE TRACKING (PHASE 3)
# ═══════════════════════════════════════════════════════════════════════════


def initialize_session_state(source: str = 'unknown') -> None:
    """Initialize session state for new session (resets first-prompt tracking)

    Called by session-start hook to ensure clean state for new session.
    Resets first_semantic_search_shown to False so first-prompt hook can trigger.

    FIX: Compaction Bug - Only reset on FRESH restart, not on compaction
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Problem: Context compaction creates new session_id, causing first-prompt
    to incorrectly trigger reindex on continuation sessions.

    Solution: Check SessionStart 'source' parameter to differentiate:
    - source='startup' → Fresh Claude Code launch → RESET flag
    - source='clear'   → User cleared conversation → RESET flag
    - source='resume'  → Compaction/continuation → PRESERVE flag
    - source='unknown' → Unknown (safe default) → PRESERVE flag

    Critical for first-prompt reindex architecture:
    - Session-start: Initializes state (this function)
    - First-prompt: Checks state, triggers reindex if not shown yet
    - Must reset on fresh restart, preserve on compaction

    Args:
        source: SessionStart source ('startup', 'clear', 'resume', 'unknown')
    """
    try:
        import session_logger
        state_file = Path("logs/state/session-reindex-tracking.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)

        session_id = session_logger.get_session_id()

        # Load existing state or create new
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except (json.JSONDecodeError, OSError):
                state = {}
        else:
            state = {}

        # Check if this is a new session
        old_session_id = state.get("session_id")
        is_new_session = old_session_id != session_id

        # CRITICAL FIX: If session_id changed, ALWAYS reset flag
        # - New session = fresh start, regardless of source parameter
        # - source='resume' just means "context continuation", but if session_id changed,
        #   it's still a NEW session that should trigger first-prompt reindex
        # - Only SAME session_id can be true continuation (shouldn't happen with is_new_session check)
        if is_new_session:
            # New session detected - ALWAYS reset flag
            state["session_id"] = session_id
            state["first_semantic_search_shown"] = False
            print(f"DEBUG: Session state reset - NEW SESSION (source={source}, old={old_session_id}, new={session_id})", file=sys.stderr)

            # Preserve last_reindex info from previous session (useful for status display)
            # state["last_reindex"] is kept as-is

            state_file.write_text(json.dumps(state, indent=2))

    except Exception as e:
        # Don't fail session start if state init fails
        print(f"DEBUG: Failed to initialize session state: {e}", file=sys.stderr)


def record_session_reindex_event(trigger: str, result: str, details: dict = None) -> None:
    """Record reindex event in session state for first-prompt UX

    **Phase 3: Session Reindex State Tracking**

    Purpose:
    - Track when auto-reindex last ran in this session
    - Show index freshness on first semantic-search use
    - Detect timeout scenarios (SessionStart reindex >50s)
    - Foundation for future async support (when Bug #1481 fixed)

    Design Rationale:
    - Synchronous architecture: No race condition (reindex completes before first prompt)
    - Informational UX: "Index updated 5 minutes ago" messaging
    - Graceful timeout handling: Show "May be stale, run manual reindex" on timeout
    - Session-scoped: Clear state on Stop hook (fresh per session)

    Args:
        trigger: Reindex trigger source ("session_start", "stop_hook", "manual")
        result: Reindex result ("success", "skipped", "failed", "timeout")
        details: Optional dict with additional context (e.g., {"error": "..."})

    State File: logs/state/session-reindex-tracking.json
    Schema:
        {
            "session_id": "20251210_123456",
            "last_reindex": {
                "trigger": "session_start",
                "result": "success",
                "timestamp": "2025-12-10T12:34:56Z",
                "details": {}
            },
            "first_semantic_search_shown": false
        }
    """
    try:
        import session_logger
        state_file = Path("logs/state/session-reindex-tracking.json")
        state_file.parent.mkdir(parents=True, exist_ok=True)

        session_id = session_logger.get_session_id()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Load existing state or create new
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except (json.JSONDecodeError, OSError):
                state = {}
        else:
            state = {}

        # Update with new reindex event
        state.update({
            "session_id": session_id,
            "last_reindex": {
                "trigger": trigger,
                "result": result,
                "timestamp": timestamp,
                "details": details or {}
            },
            "first_semantic_search_shown": state.get("first_semantic_search_shown", False)
        })

        state_file.write_text(json.dumps(state, indent=2))

    except Exception as e:
        # Don't fail caller if state tracking fails
        print(f"DEBUG: Failed to record session reindex event: {e}", file=sys.stderr)


def get_session_reindex_info() -> dict:
    """Get session reindex info for first-prompt UX

    Returns:
        dict with keys:
            - has_info: bool - whether session reindex info exists
            - trigger: str - reindex trigger source ("session_start", etc.)
            - result: str - reindex result ("success", "timeout", etc.)
            - timestamp: str - ISO timestamp of last reindex
            - age_seconds: int - seconds since last reindex
            - age_display: str - human-readable age ("5 minutes ago")
            - details: dict - additional context
    """
    try:
        state_file = Path("logs/state/session-reindex-tracking.json")

        if not state_file.exists():
            return {"has_info": False}

        state = json.loads(state_file.read_text())
        last_reindex = state.get("last_reindex", {})

        if not last_reindex:
            return {"has_info": False}

        # Calculate age
        timestamp_str = last_reindex.get("timestamp", "")
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            age_seconds = int((datetime.now(timezone.utc) - timestamp).total_seconds())

            # Human-readable age
            if age_seconds < 60:
                age_display = f"{age_seconds} seconds ago"
            elif age_seconds < 3600:
                minutes = age_seconds // 60
                age_display = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                hours = age_seconds // 3600
                age_display = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            age_seconds = 0
            age_display = "unknown"

        return {
            "has_info": True,
            "trigger": last_reindex.get("trigger", "unknown"),
            "result": last_reindex.get("result", "unknown"),
            "timestamp": timestamp_str,
            "age_seconds": age_seconds,
            "age_display": age_display,
            "details": last_reindex.get("details", {})
        }

    except Exception as e:
        print(f"DEBUG: Failed to get session reindex info: {e}", file=sys.stderr)
        return {"has_info": False}


def should_show_first_prompt_status() -> bool:
    """Check if this is the first prompt of the session

    Used by:
    1. first-prompt-reindex.py: Decides whether to trigger background reindex
    2. user-prompt-submit.py: Decides whether to check for/display reindex status

    Returns:
        True if this is the first time being checked in this session.
        Returns True in fresh sessions (no previous reindex required).

    Note: Despite the name "show status", this is primarily used to trigger
    first-prompt actions. The second caller (user-prompt-submit) has a secondary
    check (get_session_reindex_info) that verifies if status info actually exists.
    """
    try:
        state_file = Path("logs/state/session-reindex-tracking.json")

        if not state_file.exists():
            # File missing - treat as first prompt (safe default: trigger actions)
            return True

        state = json.loads(state_file.read_text())

        # Return True if we haven't shown/triggered yet this session
        # REMOVED: bool(state.get("last_reindex")) check (was causing bug in fresh sessions)
        return not state.get("first_semantic_search_shown", False)

    except Exception:
        # On error, return True (safe default: trigger reindex rather than skip)
        return True


def mark_first_prompt_shown() -> None:
    """Mark that we've shown first-prompt status (don't show again this session)"""
    try:
        state_file = Path("logs/state/session-reindex-tracking.json")

        if not state_file.exists():
            return

        state = json.loads(state_file.read_text())
        state["first_semantic_search_shown"] = True
        state_file.write_text(json.dumps(state, indent=2))

    except Exception as e:
        # Don't fail caller if marking fails
        print(f"DEBUG: Failed to mark first prompt shown: {e}", file=sys.stderr)


def clear_session_reindex_state() -> None:
    """Clear session reindex state (called by Stop hook)

    Prepares for next session by removing tracking file.
    Next SessionStart will create fresh state.
    """
    try:
        state_file = Path("logs/state/session-reindex-tracking.json")
        state_file.unlink(missing_ok=True)  # Python 3.8+ - no error if missing

    except Exception as e:
        # Don't fail Stop hook if cleanup fails
        print(f"DEBUG: Failed to clear session reindex state: {e}", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: REINDEX OPERATION LOGGING (FORENSIC DIAGNOSTICS)
# ═══════════════════════════════════════════════════════════════════════════

def _get_reindex_log_path() -> Path:
    """Get path to reindex operations log file

    Returns:
        Path to logs/reindex-operations.jsonl
    """
    project_root = get_project_root()
    logs_dir = config_loader.get_path('logs') if config_loader else 'logs'
    log_file = project_root / logs_dir / 'reindex-operations.jsonl'

    # Ensure logs directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    return log_file


def _get_session_id() -> str:
    """Get current session ID (with fallback)

    Returns:
        Session ID string or 'unknown' if not available
    """
    try:
        import session_logger
        return session_logger.get_session_id()
    except Exception:
        return 'unknown'


def _generate_operation_id(trigger: str, pid: Optional[int] = None) -> str:
    """Generate unique operation ID for reindex operation

    Args:
        trigger: Trigger source (first-prompt, stop-hook, etc.)
        pid: Process ID (optional)

    Returns:
        Unique operation ID string

    Format: reindex_{YYYYMMDD_HHMMSS}_{trigger}_{pid}
    Example: reindex_20251211_205800_first-prompt_12345
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pid_str = str(pid) if pid else str(os.getpid())
    return f"reindex_{timestamp}_{trigger}_{pid_str}"


def _log_reindex_event(event_data: Dict[str, Any]) -> None:
    """Append reindex event to operation log (JSONL format)

    Args:
        event_data: Event data dictionary

    Log Format (JSONL):
        Each line is a JSON object with event data
        Follows pattern from session_logger.py for JSONL append
    """
    try:
        log_path = _get_reindex_log_path()

        # Ensure timestamp is present
        if 'timestamp' not in event_data:
            event_data['timestamp'] = datetime.now(timezone.utc).isoformat()

        # Append to JSONL file (pattern from session_logger.py)
        with log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(event_data) + '\n')

    except Exception as e:
        # Log to stderr but don't fail the operation
        print(f"WARNING: Failed to log reindex event: {e}", file=sys.stderr)


def log_reindex_start(
    trigger: str,
    mode: str,
    pid: Optional[int] = None,
    kill_if_held: bool = True,
    skipped: bool = False,
    skip_reason: Optional[str] = None
) -> str:
    """Log reindex operation start event

    Args:
        trigger: Trigger source (first-prompt, stop-hook, post-tool-use, manual)
        mode: Execution mode (background, sync)
        pid: Process ID (None if not started yet)
        kill_if_held: Kill-if-held mode flag
        skipped: Whether operation was skipped
        skip_reason: Reason for skipping (if skipped=True)

    Returns:
        Generated operation ID

    Example Log Entry:
        {
          "timestamp": "2025-12-11T20:58:00.123456+00:00",
          "event": "start",
          "operation_id": "reindex_20251211_205800_first-prompt_12345",
          "trigger": "first-prompt",
          "session_id": "session_20251211_205800",
          "pid": 12345,
          "ppid": 12344,
          "mode": "background",
          "kill_if_held": false,
          "skipped": false,
          "skip_reason": null
        }
    """
    operation_id = _generate_operation_id(trigger, pid)
    session_id = _get_session_id()

    event_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': 'start',
        'operation_id': operation_id,
        'trigger': trigger,
        'session_id': session_id,
        'pid': pid or os.getpid(),
        'ppid': os.getppid(),
        'mode': mode,
        'kill_if_held': kill_if_held,
        'skipped': skipped,
        'skip_reason': skip_reason
    }

    _log_reindex_event(event_data)
    return operation_id


def log_reindex_end(
    operation_id: str,
    start_timestamp: str,
    status: str,
    exit_code: Optional[int] = None,
    index_updated: bool = False,
    files_changed: Optional[int] = None,
    error_message: Optional[str] = None
) -> None:
    """Log reindex operation end event

    Args:
        operation_id: Operation ID from log_reindex_start()
        start_timestamp: ISO timestamp when operation started
        status: Final status (completed, failed, timeout, killed)
        exit_code: Process exit code (0=success, 1=error, -1=killed)
        index_updated: Whether index was successfully updated
        files_changed: Number of files changed (if available)
        error_message: Error message (if status=failed)

    Example Log Entry:
        {
          "timestamp": "2025-12-11T21:05:00.123456+00:00",
          "event": "end",
          "operation_id": "reindex_20251211_205800_first-prompt_12345",
          "session_id": "session_20251211_210500",
          "start_timestamp": "2025-12-11T20:58:00.123456+00:00",
          "duration_seconds": 420.5,
          "status": "completed",
          "exit_code": 0,
          "index_updated": true,
          "files_changed": 68
        }
    """
    end_time = datetime.now(timezone.utc)
    session_id = _get_session_id()

    # Calculate duration
    try:
        start_dt = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
        duration = (end_time - start_dt).total_seconds()
    except Exception:
        duration = None

    event_data = {
        'timestamp': end_time.isoformat(),
        'event': 'end',
        'operation_id': operation_id,
        'session_id': session_id,
        'start_timestamp': start_timestamp,
        'duration_seconds': duration,
        'status': status,
        'exit_code': exit_code,
        'index_updated': index_updated,
        'files_changed': files_changed,
        'error_message': error_message
    }

    _log_reindex_event(event_data)


def get_active_reindex_operations() -> list:
    """Get currently active (running) reindex operations

    Returns:
        List of active operation dicts with 'start' event but no matching 'end'

    Usage:
        Check if any reindex operations are currently running
    """
    try:
        log_path = _get_reindex_log_path()

        if not log_path.exists():
            return []

        # Parse JSONL log
        operations = {}
        with log_path.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                    op_id = event.get('operation_id')

                    if event.get('event') == 'start' and not event.get('skipped'):
                        operations[op_id] = event
                    elif event.get('event') == 'end':
                        operations.pop(op_id, None)
                except json.JSONDecodeError:
                    continue

        return list(operations.values())

    except Exception as e:
        print(f"WARNING: Failed to get active operations: {e}", file=sys.stderr)
        return []
