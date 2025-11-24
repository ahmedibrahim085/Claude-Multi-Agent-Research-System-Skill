#!/usr/bin/env python3
"""
State Manager Utility

Manages research workflow state for tracking phases, quality gates,
and agent assignments across sessions.

Architecture:
- logs/state/current.json: Current state (currentSkill, currentResearch) - tiny, never grows
- logs/session_*_state.json: Historical data per session (skillHistory, sessions)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


# Current state file (small, persistent across sessions)
CURRENT_STATE_FILE = Path('logs/state/current.json')

# Legacy state file (for backwards compatibility during migration)
LEGACY_STATE_FILE = Path('logs/state/research-workflow-state.json')


def load_state() -> Dict[str, Any]:
    """
    Load current state from current.json (for backwards compatibility).

    Returns state with both current fields and empty arrays for historical data.
    Historical data should be read from session files when needed.
    """
    current = load_current_state()

    # Return format compatible with existing code (includes empty historical arrays)
    return {
        'version': current.get('version', '1.0'),
        'currentSkill': current.get('currentSkill'),
        'currentResearch': current.get('currentResearch'),
        'skillHistory': [],  # Historical data lives in session files
        'sessions': []       # Historical data lives in session files
    }


def save_state(state: Dict[str, Any]) -> None:
    """
    Save current state to current.json (for backwards compatibility).

    Only saves current fields (currentSkill, currentResearch).
    Historical data (skillHistory, sessions) should be written to session files.
    """
    current_state = {
        'version': state.get('version', '1.0'),
        'currentSkill': state.get('currentSkill'),
        'currentResearch': state.get('currentResearch')
    }
    save_current_state(current_state)


def load_current_state() -> Dict[str, Any]:
    """Load current state from current.json (tiny file, never grows)"""
    if not CURRENT_STATE_FILE.exists():
        return create_initial_current_state()

    try:
        with CURRENT_STATE_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading current state: {e}", flush=True)
        return create_initial_current_state()


def save_current_state(current_state: Dict[str, Any]) -> None:
    """Save current state to current.json"""
    CURRENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with CURRENT_STATE_FILE.open('w', encoding='utf-8') as f:
            json.dump(current_state, f, indent=2)
    except IOError as e:
        print(f"Error saving current state: {e}", flush=True)


def create_initial_current_state() -> Dict[str, Any]:
    """Create initial current state structure (tiny, never grows)"""
    return {
        'version': '1.0',
        'currentSkill': None,
        'currentResearch': None
    }


def create_initial_state() -> Dict[str, Any]:
    """Create initial state structure (for backwards compatibility)"""
    return {
        'version': '1.0.0',
        'sessions': [],
        'currentResearch': None,
        'skillHistory': [],
        'currentSkill': None
    }


def create_session(topic: str, subtopics: List[str]) -> Dict[str, Any]:
    """Create new research session"""
    session_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return {
        'id': session_id,
        'topic': topic,
        'status': 'in_progress',
        'startedAt': datetime.now().isoformat(),
        'completedAt': None,
        'phases': {
            'decomposition': {
                'status': 'completed',
                'subtopics': subtopics,
                'completedAt': datetime.now().isoformat()
            },
            'research': {
                'status': 'in_progress',
                'parallelInstances': len(subtopics),
                'outputs': [],
                'startedAt': datetime.now().isoformat(),
                'completedAt': None
            },
            'synthesis': {
                'status': 'pending',
                'agent': 'unknown',
                'output': None,
                'startedAt': None,
                'completedAt': None
            },
            'delivery': {
                'status': 'pending',
                'startedAt': None,
                'completedAt': None
            }
        },
        'qualityGates': {
            'research': {
                'status': 'pending',
                'checkedAt': None,
                'expected': len(subtopics),
                'actual': 0
            },
            'synthesis': {
                'status': 'pending',
                'checkedAt': None,
                'expectedAgent': 'report-writer',
                'actualAgent': 'unknown'
            }
        }
    }


def get_current_session(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get current active research session"""
    if not state.get('currentResearch'):
        return None

    sessions = state.get('sessions', [])
    return next((s for s in sessions if s['id'] == state['currentResearch']), None)


def validate_quality_gate(state: Dict[str, Any], session_id: str, gate: str) -> bool:
    """Validate quality gate for a session"""
    sessions = state.get('sessions', [])
    session = next((s for s in sessions if s['id'] == session_id), None)

    if not session:
        return False

    if gate == 'research':
        quality_gate = session['qualityGates']['research']
        outputs = session['phases']['research']['outputs']
        expected = quality_gate['expected']
        actual = len(outputs)

        quality_gate['actual'] = actual
        quality_gate['checkedAt'] = datetime.now().isoformat()

        if actual >= expected and expected > 0:
            quality_gate['status'] = 'passed'
            return True
        else:
            quality_gate['status'] = 'failed'
            return False

    elif gate == 'synthesis':
        quality_gate = session['qualityGates']['synthesis']
        expected_agent = quality_gate['expectedAgent']
        actual_agent = session['phases']['synthesis']['agent']

        quality_gate['actualAgent'] = actual_agent
        quality_gate['checkedAt'] = datetime.now().isoformat()

        if actual_agent == expected_agent:
            quality_gate['status'] = 'passed'
            return True
        else:
            quality_gate['status'] = 'failed'
            return False

    return False


# ═══════════════════════════════════════════════════════════════════════════
# SKILL TRACKING (Non-Destructive Extension)
# ═══════════════════════════════════════════════════════════════════════════

def calculate_duration(start_time: str, end_time: str) -> str:
    """Calculate duration between two ISO timestamps"""
    try:
        start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        delta = end - start

        minutes = int(delta.total_seconds() / 60)
        seconds = int(delta.total_seconds() % 60)

        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "unknown"


def get_current_skill() -> Optional[Dict[str, Any]]:
    """Get currently active skill (if any)"""
    state = load_state()
    return state.get('currentSkill')


def set_current_skill(skill_name: str, start_time: str) -> Optional[Dict[str, Any]]:
    """
    Start tracking a new skill invocation.
    If same skill already active, ends it first and increments invocation number.

    Args:
        skill_name: Name of the skill (e.g., 'multi-agent-researcher')
        start_time: ISO timestamp when skill started

    Returns:
        The ended skill (if one was active), or None.
        Caller should write this to session state file.
    """
    current_state = load_current_state()
    current = current_state.get('currentSkill')

    ended_skill = None

    # Calculate invocation number
    if current and current.get('name') == skill_name:
        # Same skill re-invoked - end previous, increment counter
        invocation_number = current.get('invocationNumber', 1) + 1

        # End previous invocation if not already ended
        if not current.get('endTime'):
            current['endTime'] = start_time  # End at exact moment new one starts
            current['trigger'] = 'ReInvocation'
            current['duration'] = calculate_duration(
                current['startTime'],
                current['endTime']
            )
            ended_skill = current

    else:
        # Different skill or first invocation
        invocation_number = 1

        # End any active skill first
        if current and not current.get('endTime'):
            current['endTime'] = start_time
            current['trigger'] = 'NewSkill'
            current['duration'] = calculate_duration(
                current['startTime'],
                current['endTime']
            )
            ended_skill = current

    # Set new current skill
    current_state['currentSkill'] = {
        'name': skill_name,
        'startTime': start_time,
        'endTime': None,
        'invocationNumber': invocation_number
    }

    save_current_state(current_state)
    return ended_skill


def end_current_skill(end_time: str, trigger: str) -> Optional[Dict[str, Any]]:
    """
    End the currently active skill.

    Args:
        end_time: ISO timestamp when skill ended
        trigger: What caused the end (Stop, SessionEnd, ReInvocation, etc.)

    Returns:
        The ended skill entry (caller should write to session state), or None if no active skill
    """
    current_state = load_current_state()
    current = current_state.get('currentSkill')

    if not current:
        return None

    # Don't override if already ended
    if current.get('endTime'):
        return current

    # End it
    current['endTime'] = end_time
    current['trigger'] = trigger
    current['duration'] = calculate_duration(
        current['startTime'],
        current['endTime']
    )

    # Clear current skill (set to None)
    current_state['currentSkill'] = None
    save_current_state(current_state)

    # Return ended skill (caller writes to session state)
    return current


def get_skill_invocation_count(skill_name: str) -> int:
    """
    Get invocation count for currently active skill.

    Note: Historical counts require reading session state files.
    This function only returns 1 if the specified skill is currently active, 0 otherwise.
    """
    current_state = load_current_state()
    current = current_state.get('currentSkill')

    if current and current.get('name') == skill_name:
        return 1
    return 0
