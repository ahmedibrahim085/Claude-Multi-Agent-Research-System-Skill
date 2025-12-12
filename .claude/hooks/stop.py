#!/usr/bin/env python3
"""
Stop Hook - Detect skill completion and end skill tracking

Fires when main Claude agent finishes responding (not on user interrupt).
Checks if the stop represents actual skill completion by looking for
completion patterns in the transcript.
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
    import reindex_manager
except ImportError as e:
    print(f"Failed to import utilities: {e}", file=sys.stderr)
    sys.exit(0)


def read_last_messages(transcript_path: str, n: int = 5) -> list:
    """Read last N messages from transcript JSONL file"""
    try:
        transcript_file = Path(transcript_path)
        if not transcript_file.exists():
            return []

        with transcript_file.open('r', encoding='utf-8') as f:
            lines = f.readlines()
            # Get last N non-empty lines
            messages = []
            for line in reversed(lines):
                if line.strip():
                    try:
                        messages.append(json.loads(line))
                        if len(messages) >= n:
                            break
                    except json.JSONDecodeError:
                        continue
            return list(reversed(messages))
    except Exception as e:
        print(f"Error reading transcript: {e}", file=sys.stderr)
        return []


def has_completion_pattern(transcript_path: str, skill_name: str) -> bool:
    """Check if transcript contains skill completion markers"""
    # Completion patterns for each skill
    patterns = {
        'multi-agent-researcher': [
            'Research Complete:',
            '# Research Complete:',
            'files/reports/',
            'Comprehensive research completed',
            'report has been delivered',
            'research report is now available',
        ],
        'spec-workflow-orchestrator': [
            'Planning phase complete',
            '✅ Planning phase complete',
            'Development-ready specifications available',
            'docs/projects/',
            'specifications are now ready',
            'planning deliverables complete',
        ]
    }

    skill_patterns = patterns.get(skill_name, [])
    if not skill_patterns:
        # Unknown skill - can't detect completion
        return False

    messages = read_last_messages(transcript_path, n=5)

    for msg in messages:
        if msg.get('role') == 'assistant':
            content = str(msg.get('content', ''))
            # Check if any completion pattern matches
            if any(pattern.lower() in content.lower() for pattern in skill_patterns):
                return True

    return False


def main():
    # DIAGNOSTIC: File-based logging to verify hook execution
    debug_log = Path("logs/stop-hook-debug.log")
    debug_log.parent.mkdir(parents=True, exist_ok=True)
    with open(debug_log, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Stop hook STARTED\n")

    # Read input from stdin
    try:
        data = json.loads(sys.stdin.read())
        with open(debug_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] stdin read successfully\n")
    except json.JSONDecodeError as e:
        with open(debug_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] JSON error: {e}\n")
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    # ═════════════════════════════════════════════════════════════════════════════
    # SECTION 1: Auto-reindex on stop (runs ALWAYS, regardless of skill state)
    # ═════════════════════════════════════════════════════════════════════════════
    with open(debug_log, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Starting auto-reindex section\n")
    # Trigger auto-reindex on stop (batches all file changes from conversation turn)
    # NEW Architecture: Replaces post-tool-use hook for better efficiency
    # Stop hook fires once per conversation turn vs after every Write/Edit operation
    try:
        decision = reindex_manager.reindex_on_stop_background()

        # DIAGNOSTIC: Log decision
        with open(debug_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] reindex_on_stop_background() returned: {decision.get('decision')} - {decision.get('reason')}\n")

        # Log the decision to session logs for visibility and debugging
        try:
            session_id = session_logger.get_session_id()
            session_logger.log_auto_reindex_decision(session_id, decision)

            # Add human-readable output to transcript
            if decision.get('decision') == 'run':
                reason = decision.get('reason', 'unknown')
                if reason == 'reindex_spawned':
                    # Background mode - process spawned but outcome unknown
                    print(f"✅ Stop hook: Index update spawned in background", flush=True)
                else:
                    # Unexpected reason for 'run' decision
                    print(f"✅ Stop hook: Auto-reindex {reason}", flush=True)
            elif decision.get('decision') == 'skip':
                reason = decision.get('reason', 'unknown')
                # Only show important skip reasons (not verbose for every cooldown)
                if reason not in ['cooldown_active', 'no_changes']:
                    print(f"⏭️  Stop hook: Auto-reindex skipped ({reason})", flush=True)
        except Exception as log_error:
            # Logging failure shouldn't fail the hook
            print(f"Failed to log reindex decision: {log_error}", file=sys.stderr)
    except Exception as e:
        # Don't fail hook if reindexing fails
        print(f"Auto-reindex on stop failed: {e}", file=sys.stderr)


    # ═════════════════════════════════════════════════════════════════════════════
    # SECTION 2: Logging (runs ALWAYS, before skill completion tracking)
    # ═════════════════════════════════════════════════════════════════════════════

    # DIAGNOSTIC: Log hook completion (ALWAYS, before early exits)
    with open(debug_log, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] Stop hook COMPLETED\n\n")

    # ═════════════════════════════════════════════════════════════════════════════
    # SECTION 3: Skill completion tracking (runs ONLY when skill is active)
    # ═════════════════════════════════════════════════════════════════════════════
    current_skill = state_manager.get_current_skill()

    if not current_skill:
        sys.exit(0)  # No active skill

    # Check if already ended
    if current_skill.get('endTime'):
        sys.exit(0)  # Already ended

    # Check if this Stop represents skill completion
    transcript_path = data.get('transcript_path', '')
    skill_name = current_skill.get('name')

    if has_completion_pattern(transcript_path, skill_name):
        # Skill completed!
        try:
            from datetime import timezone
            timestamp = datetime.now(timezone.utc).isoformat()
            ended_skill = state_manager.end_current_skill(timestamp, 'Stop')

            if ended_skill:
                invocation = ended_skill.get('invocationNumber', 1)
                duration = ended_skill.get('duration', 'unknown')
                print(f"🏁 SKILL END: {skill_name} (invocation #{invocation}, duration: {duration})", flush=True)

                # Write ended skill to session state file (historical data)
                try:
                    session_id = session_logger.get_session_id()
                    session_logger.append_skill_invocation(session_id, ended_skill)
                except Exception as e:
                    print(f"Failed to write skill to session state: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to end skill: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == '__main__':
    main()
