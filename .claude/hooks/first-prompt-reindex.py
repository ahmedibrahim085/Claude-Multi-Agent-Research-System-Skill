#!/usr/bin/env python3
"""Dedicated hook for first-prompt background reindex trigger

ARCHITECTURE DECISION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This hook runs in PARALLEL with user-prompt-submit.py (skill enforcement hook).
Both hooks execute simultaneously for UserPromptSubmit event.

PURPOSE:
- Trigger background reindex on FIRST user prompt after session start
- Independent of semantic search keywords (runs on EVERY first prompt)
- Fast session startup (session-start hook no longer blocks on reindex)

RATIONALE:
- Session-start blocking caused 50s timeout (killed before completion)
- First-prompt triggering allows fast startup + background completion
- Dedicated hook = separation of concerns (not tied to semantic search)
- Parallel execution = no performance impact on skill enforcement

PERFORMANCE:
- Hook overhead: <100ms (just spawn, no waiting)
- Background process: Full reindex completes in 3-10 minutes
- User experience: Fast session + silent background update

SAFETY:
- Kill-and-restart architecture prevents orphan processes
- Claim file prevents concurrent reindex
- Process group termination ensures clean shutdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

import reindex_manager


def should_recheck_prerequisites(state_file: Path) -> bool:
    """Determine if prerequisites should be re-checked

    Recheck if:
    - State file doesn't exist (fresh clone)
    - State file older than 24 hours (stale)
    - Prerequisites marked as not ready (false)

    Returns:
        True if prerequisites should be re-checked
    """
    if not state_file.exists():
        return True

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)

        # Check if prerequisites are false
        if not state.get('SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY', False):
            return True

        # Check if state file is stale (> 24 hours old)
        last_checked = state.get('last_checked')
        if last_checked:
            try:
                last_check_time = datetime.fromisoformat(last_checked.replace('Z', '+00:00'))
                age = datetime.now(timezone.utc) - last_check_time
                if age > timedelta(hours=24):
                    return True
            except (ValueError, AttributeError):
                # Invalid timestamp format
                return True

        return False
    except Exception:
        # Error reading state file
        return True


def run_check_prerequisites() -> bool:
    """Run check-prerequisites script to detect global installations

    Returns:
        True if prerequisites ready after check, False otherwise
    """
    try:
        project_root = Path.cwd()
        check_script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'check-prerequisites'

        if not check_script.exists():
            return False

        # Run check-prerequisites (it updates state file automatically)
        result = subprocess.run(
            [str(check_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )

        # Read updated state
        state_file = project_root / 'logs' / 'state' / 'semantic-search-prerequisites.json'
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            return state.get('SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY', False)

        return False
    except Exception:
        return False


def main():
    """Trigger background reindex on first prompt after session start"""

    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Invalid input, exit silently
        sys.exit(0)

    # Check if this is first prompt of session
    if not reindex_manager.should_show_first_prompt_status():
        # Not first prompt, exit immediately (no work needed)
        sys.exit(0)

    # This IS first prompt - check prerequisites first
    try:
        project_root = Path.cwd()
        state_dir = project_root / 'logs' / 'state'
        state_dir.mkdir(parents=True, exist_ok=True)  # Ensure state dir exists
        state_file = state_dir / 'semantic-search-prerequisites.json'

        # Auto-detect prerequisites on fresh clone / stale state
        prereqs_ready = False
        if should_recheck_prerequisites(state_file):
            print("🔍 Detecting semantic-search prerequisites...", flush=True)
            prereqs_ready = run_check_prerequisites()
            if prereqs_ready:
                print("✓ Semantic-search prerequisites found (using global components)", flush=True)
            else:
                print("⚠️  Semantic-search prerequisites not found", flush=True)
                print("   Setup: https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill#installation", flush=True)
        else:
            prereqs_ready = reindex_manager.read_prerequisites_state()

        # Only spawn reindex if prerequisites are ready
        if prereqs_ready:
            # Spawn background reindex using PROVEN pattern (Popen + DEVNULL + NO communicate)
            spawned = reindex_manager.spawn_background_reindex(project_root, trigger='first-prompt')

            # Mark as processed to prevent running again this session
            reindex_manager.mark_first_prompt_shown()

            if spawned:
                # Success - background process running
                print("🔄 Indexing project in background...", flush=True)
            # else: spawned=False means script not found, but don't show error
        else:
            # Prerequisites not ready - mark as shown to prevent retry
            reindex_manager.mark_first_prompt_shown()

    except Exception as e:
        # Log error to stderr for debugging (not visible to user)
        import traceback
        print(f"DEBUG first-prompt-reindex: Exception occurred: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()

        # Still mark as shown to prevent retry loops
        try:
            reindex_manager.mark_first_prompt_shown()
        except:
            pass

    # Always exit 0 (don't block user prompt on reindex issues)
    sys.stdout.flush()  # Ensure all output is sent before exit
    sys.exit(0)


if __name__ == '__main__':
    main()
