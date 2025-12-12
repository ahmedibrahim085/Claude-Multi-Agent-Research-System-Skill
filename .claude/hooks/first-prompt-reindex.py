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
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

import reindex_manager


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

    # This IS first prompt - spawn background reindex
    try:
        project_root = Path.cwd()

        # Spawn background reindex using PROVEN pattern (Popen + DEVNULL + NO communicate)
        spawned = reindex_manager.spawn_background_reindex(project_root, trigger='first-prompt')

        # Mark as processed to prevent running again this session
        reindex_manager.mark_first_prompt_shown()

        if spawned:
            # Success - background process running
            # Return message via stdout so it's visible to user
            print("🔄 Checking for index updates in background...")
        # else: spawned=False means script not found, but don't show error on first prompt

    except Exception as e:
        # Unexpected error during spawn - still mark as shown to prevent retry loops
        try:
            reindex_manager.mark_first_prompt_shown()
        except:
            pass
        # Don't show error to user on first prompt (silent failure)

    # Always exit 0 (don't block user prompt on reindex issues)
    sys.exit(0)


if __name__ == '__main__':
    main()
