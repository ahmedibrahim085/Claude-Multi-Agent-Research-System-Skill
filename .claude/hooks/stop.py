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
    # Read input from stdin
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

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

    # Trigger auto-reindex on stop (batches all file changes from conversation turn)
    # NEW Architecture: Replaces post-tool-use hook for better efficiency
    # Stop hook fires once per conversation turn vs after every Write/Edit operation
    try:
        reindex_manager.reindex_on_stop()
    except Exception as e:
        # Don't fail hook if reindexing fails
        print(f"Auto-reindex on stop failed: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == '__main__':
    main()
