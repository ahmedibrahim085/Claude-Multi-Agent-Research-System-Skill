#!/usr/bin/env python3
"""
Session Logger Utility

Provides logging functionality for research agent sessions, matching the
reference implementation from claude-agent-sdk-demos/research-agent.

Creates two log files per session:
- transcript.txt: Human-readable tool call log with agent names
- tool_calls.jsonl: Structured JSON log for programmatic analysis

Directory structure: logs/session_YYYYMMDD_HHMMSS/
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import config loader
try:
    from . import config_loader
except ImportError:
    # Fallback if run standalone
    sys.path.insert(0, str(Path(__file__).parent))
    import config_loader


def get_session_log_dir(session_id: str) -> Path:
    """Get logs directory (flat structure, configurable)"""
    project_root = Path.cwd()
    logs_dir = config_loader.get_path('logs')
    return project_root / logs_dir


def get_transcript_path(session_id: str) -> Path:
    """Get transcript file path (flat structure)"""
    return get_session_log_dir(session_id) / f"{session_id}_transcript.txt"


def get_jsonl_path(session_id: str) -> Path:
    """Get JSONL file path (flat structure)"""
    return get_session_log_dir(session_id) / f"{session_id}_tool_calls.jsonl"


def initialize_session_logs(session_id: str) -> None:
    """Initialize session log files (flat structure)"""
    log_dir = get_session_log_dir(session_id)

    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    # Create initial files if they don't exist
    transcript_path = get_transcript_path(session_id)
    tool_calls_path = get_jsonl_path(session_id)

    if not transcript_path.exists():
        header = f"""Research Agent Session Log
Session ID: {session_id}
Started: {datetime.now().isoformat()}
{'='*80}

"""
        transcript_path.write_text(header, encoding='utf-8')

    if not tool_calls_path.exists():
        tool_calls_path.write_text('', encoding='utf-8')


def identify_agent(tool_name: str, tool_input: Dict[str, Any], state: Optional[Dict] = None) -> str:
    """Identify agent type from context"""

    # Priority 1: Check active skill (if skill is orchestrating)
    if state:
        current_skill = state.get('currentSkill')
        # Only if skill is active (no endTime)
        if current_skill and not current_skill.get('endTime'):
            skill_name = current_skill.get('name')
            if skill_name == 'multi-agent-researcher':
                return 'research-orchestrator'
            elif skill_name == 'spec-workflow-orchestrator':
                return 'spec-orchestrator'
            elif skill_name == 'semantic-search':
                return 'semantic-search-orchestrator'

    # Priority 2: Environment variable (if SDK provides it)
    if os.environ.get('CLAUDE_AGENT_TYPE'):
        return os.environ['CLAUDE_AGENT_TYPE']

    # Priority 3: Detect from file paths (use configured paths)
    if tool_name == 'Write' and tool_input.get('file_path'):
        file_path = tool_input['file_path']
        research_notes_dir = config_loader.get_path('research_notes')
        reports_dir = config_loader.get_path('reports')

        if file_path.startswith(research_notes_dir + '/'):
            return 'researcher'
        if file_path.startswith(reports_dir + '/'):
            return 'report-writer'

    # Priority 4: Detect semantic-search agents from Task tool prompt
    if tool_name == 'Task' and tool_input.get('prompt'):
        prompt = tool_input['prompt']
        if 'You are the semantic-search-reader agent' in prompt:
            return 'semantic-search-reader'
        if 'You are the semantic-search-indexer agent' in prompt:
            return 'semantic-search-indexer'

    # Priority 5: Detect from Task tool (spawning subagents)
    if tool_name == 'Task' and tool_input.get('subagent_type'):
        return 'orchestrator'

    # Priority 6: Check if we're in an active research session
    if state and state.get('currentResearch'):
        sessions = state.get('sessions', [])
        session = next((s for s in sessions if s['id'] == state['currentResearch']), None)

        if session:
            # If synthesis phase is active, likely report-writer
            if session.get('phases', {}).get('synthesis', {}).get('status') == 'in_progress':
                return 'report-writer'

            # If research phase is active
            if session.get('phases', {}).get('research', {}).get('status') == 'in_progress':
                # WebSearch suggests researcher
                if tool_name == 'WebSearch':
                    return 'researcher'
                # Task suggests orchestrator spawning researchers
                if tool_name == 'Task':
                    return 'orchestrator'

    # Default: assume orchestrator
    return 'orchestrator'


def get_agent_id(agent_type: str, tool_name: str, tool_input: Dict[str, Any], state: Optional[Dict] = None) -> str:
    """Get agent ID with counter (e.g., RESEARCHER-1, RESEARCHER-2)"""

    if agent_type == 'orchestrator':
        return 'ORCHESTRATOR'

    if agent_type == 'report-writer':
        return 'REPORT-WRITER'

    if agent_type == 'researcher':
        # Try to identify which researcher by checking research_notes filename
        if tool_name == 'Write' and tool_input.get('file_path'):
            file_path = tool_input['file_path']
            if state and state.get('currentResearch'):
                sessions = state.get('sessions', [])
                session = next((s for s in sessions if s['id'] == state['currentResearch']), None)

                if session:
                    outputs = session.get('phases', {}).get('research', {}).get('outputs', [])
                    # Count how many research notes exist + 1 for current
                    researcher_num = len(outputs) + 1
                    return f'RESEARCHER-{researcher_num}'

        # Default researcher numbering
        return 'RESEARCHER-?'

    if agent_type == 'research-orchestrator':
        return 'RESEARCH-ORCHESTRATOR'

    if agent_type == 'spec-orchestrator':
        return 'SPEC-ORCHESTRATOR'

    if agent_type == 'semantic-search-orchestrator':
        return 'SEMANTIC-SEARCH-ORCHESTRATOR'

    if agent_type == 'semantic-search-reader':
        return 'SEMANTIC-READER'

    if agent_type == 'semantic-search-indexer':
        return 'SEMANTIC-INDEXER'

    return agent_type.upper()


def format_bytes(num_bytes: int) -> str:
    """Format bytes to human-readable size"""
    if num_bytes == 0:
        return '0 B'

    units = ['B', 'KB', 'MB', 'GB']
    k = 1024
    i = 0
    size = float(num_bytes)

    while size >= k and i < len(units) - 1:
        size /= k
        i += 1

    return f'{size:.1f} {units[i]}'


def log_to_transcript(session_id: str, log_data: Dict[str, Any]) -> None:
    """Log tool call to transcript.txt (human-readable)"""
    transcript_path = get_transcript_path(session_id)

    # Format timestamp
    timestamp = datetime.fromisoformat(log_data['timestamp'])
    time_str = timestamp.strftime('%H:%M:%S')

    # Format tool input (truncate if too long)
    input_str = json.dumps(log_data['toolInput'], indent=2)
    if len(input_str) > 500:
        input_str = input_str[:500] + '...\n  [truncated]'

    # Format output size
    output_info = ''
    if log_data.get('outputSize'):
        output_info = f" ({format_bytes(log_data['outputSize'])})"

    success_marker = ' ✅' if log_data.get('success', True) else ' ❌ FAILED'

    entry = f"""
[{time_str}] {log_data['agentId']} → {log_data['toolName']}{success_marker}
  Input: {input_str}
  Output: {'Success' if log_data.get('success', True) else 'Failed'}{output_info}
  Duration: {log_data.get('duration', 'N/A')}ms
{'─'*80}
"""

    with transcript_path.open('a', encoding='utf-8') as f:
        f.write(entry)


def log_to_jsonl(session_id: str, log_data: Dict[str, Any]) -> None:
    """Log tool call to tool_calls.jsonl (structured)"""
    jsonl_path = get_jsonl_path(session_id)

    # Create compact JSON record
    record = {
        'ts': log_data['timestamp'],
        'agent': log_data['agentId'],
        'tool': log_data['toolName'],
        'input': log_data['toolInput'],
        'success': log_data.get('success', True),
        'output_size': log_data.get('outputSize'),
        'duration_ms': log_data.get('duration')
    }

    with jsonl_path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')


def log_tool_call(
    session_id: str,
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_output: Any,
    state: Optional[Dict] = None,
    start_time: Optional[float] = None
) -> None:
    """Log a tool call to both transcript and JSONL"""

    agent_type = identify_agent(tool_name, tool_input, state)
    agent_id = get_agent_id(agent_type, tool_name, tool_input, state)

    # Calculate output size
    output_size = None
    if tool_output:
        try:
            output_size = len(json.dumps(tool_output))
        except:
            pass

    # Calculate duration
    duration = None
    if start_time:
        duration = int((datetime.now().timestamp() - start_time) * 1000)

    log_data = {
        'timestamp': datetime.now().isoformat(),
        'agent': agent_type,
        'agentId': agent_id,
        'toolName': tool_name,
        'toolInput': tool_input,
        'toolOutput': tool_output,
        'success': not (isinstance(tool_output, dict) and tool_output.get('error')),
        'outputSize': output_size,
        'duration': duration
    }

    # Ensure log directory exists
    initialize_session_logs(session_id)

    # Write to both logs
    log_to_transcript(session_id, log_data)
    log_to_jsonl(session_id, log_data)


def log_auto_reindex_decision(session_id: str, decision_data: Dict[str, Any]) -> None:
    """Log auto-reindex decision to transcript (tracing for debugging)

    Logs all reindex decisions (skip or run) with detailed reasons.
    This provides full visibility into auto-reindex behavior for debugging.

    Args:
        session_id: Session identifier
        decision_data: Decision data from reindex_manager.reindex_after_write()
            - decision: "skip" or "run"
            - reason: Reason code
            - details: Additional context
            - timestamp: ISO timestamp
    """
    transcript_path = get_transcript_path(session_id)

    # Format timestamp
    timestamp = datetime.fromisoformat(decision_data['timestamp'])
    time_str = timestamp.strftime('%H:%M:%S')

    # Format decision
    decision = decision_data['decision'].upper()
    reason = decision_data['reason']
    details = decision_data['details']
    file_name = details.get('file', 'unknown')

    # Format human-readable message based on reason
    if reason == "prerequisites_not_ready":
        message = f"Prerequisites not met ({details.get('state_file', 'N/A')})"
    elif reason == "not_indexable_pattern":
        ext = details.get('extension', 'N/A')
        message = f"File not indexable (extension {ext} not in include patterns)"
    elif reason == "excluded_directory":
        directory = details.get('directory', 'N/A')
        message = f"File in excluded directory ({directory}/)"
    elif reason == "excluded_pattern":
        pattern = details.get('pattern', 'N/A')
        message = f"File matches exclude pattern ({pattern})"
    elif reason == "cooldown_active":
        remaining = details.get('remaining_seconds', 0)
        cooldown = details.get('cooldown_seconds', 0)
        message = f"Cooldown active ({remaining}s remaining of {cooldown}s)"
    elif reason == "index_not_found":
        message = "Index not found (run manual index first)"
    elif reason == "concurrent_reindex":
        message = "Another process is reindexing"
    elif reason == "reindex_success":
        message = "Incremental reindex completed successfully"
    elif reason == "reindex_failed":
        message = "Reindex failed (see error above)"
    elif reason == "exception":
        error = details.get('error', 'unknown')
        message = f"Exception: {error}"
    else:
        message = f"Reason: {reason}"

    # Format log entry
    entry = f"[{time_str}] AUTO-REINDEX → {decision}: {file_name} - {message}\n"

    with transcript_path.open('a', encoding='utf-8') as f:
        f.write(entry)


def get_session_id() -> str:
    """Get session ID from various sources"""

    # Try to get from environment
    if os.environ.get('CLAUDE_SESSION_ID'):
        return os.environ['CLAUDE_SESSION_ID']

    # Generate session ID based on timestamp
    now = datetime.now()
    return f"session_{now.strftime('%Y%m%d_%H%M%S')}"

# ═══════════════════════════════════════════════════════════════════════════
# SESSION STATE MANAGEMENT (Per-Session Historical Data)
# ═══════════════════════════════════════════════════════════════════════════

def get_session_state_path(session_id: str) -> Path:
    """Get path for session state file"""
    return get_session_log_dir(session_id) / f"{session_id}_state.json"


def initialize_session_state(session_id: str) -> None:
    """Initialize session state file with empty structure"""
    state_path = get_session_state_path(session_id)
    
    if state_path.exists():
        return  # Already initialized
    
    initial_state = {
        'version': '1.0',
        'sessionId': session_id,
        'sessionStart': datetime.now().isoformat(),
        'sessionEnd': None,
        'skillInvocations': [],
        'researchSessions': []
    }
    
    try:
        with state_path.open('w', encoding='utf-8') as f:
            json.dump(initial_state, f, indent=2)
    except IOError as e:
        print(f"Error initializing session state: {e}", flush=True)


def load_session_state(session_id: str) -> Dict[str, Any]:
    """Load session state from file"""
    state_path = get_session_state_path(session_id)
    
    if not state_path.exists():
        initialize_session_state(session_id)
        return load_session_state(session_id)
    
    try:
        with state_path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading session state: {e}", flush=True)
        return {
            'version': '1.0',
            'sessionId': session_id,
            'sessionStart': datetime.now().isoformat(),
            'sessionEnd': None,
            'skillInvocations': [],
            'researchSessions': []
        }


def save_session_state(session_id: str, state: Dict[str, Any]) -> None:
    """Save session state to file"""
    state_path = get_session_state_path(session_id)
    
    try:
        with state_path.open('w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        print(f"Error saving session state: {e}", flush=True)


def append_skill_invocation(session_id: str, skill_invocation: Dict[str, Any]) -> None:
    """Append a skill invocation to session state"""
    state = load_session_state(session_id)
    state['skillInvocations'].append(skill_invocation)
    save_session_state(session_id, state)


def finalize_session_state(session_id: str) -> None:
    """Mark session as ended in session state file"""
    state = load_session_state(session_id)
    state['sessionEnd'] = datetime.now().isoformat()
    save_session_state(session_id, state)
