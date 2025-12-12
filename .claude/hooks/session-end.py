#!/usr/bin/env python3
"""
SessionEnd Hook - Cleanup skill state on session termination

Fires when a Claude Code session ends (clear, logout, exit).
Ensures any active skill is properly ended and moved to history.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

try:
    import state_manager
    import session_logger
except ImportError as e:
    print(f"Failed to import utilities: {e}", file=sys.stderr)
    sys.exit(0)


def main():
    # Read input from stdin
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    current_skill = state_manager.get_current_skill()

    if current_skill and not current_skill.get('endTime'):
        # Force end on session termination
        try:
            from datetime import timezone
            timestamp = datetime.now(timezone.utc).isoformat()
            reason = data.get('reason', 'unknown')
            ended_skill = state_manager.end_current_skill(timestamp, 'SessionEnd')

            if ended_skill:
                skill_name = ended_skill['name']
                invocation = ended_skill.get('invocationNumber', 1)
                duration = ended_skill.get('duration', 'unknown')
                print(f"🧹 CLEANUP: {skill_name} ended (invocation #{invocation}, duration: {duration}, reason: {reason})", flush=True)

                # Write ended skill to session state file (historical data)
                try:
                    session_id = session_logger.get_session_id()
                    session_logger.append_skill_invocation(session_id, ended_skill)
                except Exception as e:
                    print(f"Failed to write skill to session state: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to end skill on session termination: {e}", file=sys.stderr)

    # Finalize session state (mark session as ended)
    try:
        session_id = session_logger.get_session_id()
        session_logger.finalize_session_state(session_id)
    except Exception as e:
        print(f"Failed to finalize session state: {e}", file=sys.stderr)

    # Clear session reindex state to prepare for next session
    # This ensures first-prompt reindex will trigger on next session start
    try:
        import reindex_manager
        reindex_manager.clear_session_reindex_state()
    except Exception as e:
        print(f"Failed to clear session reindex state: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == '__main__':
    main()
