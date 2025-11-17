#!/usr/bin/env python3
"""
State Manager Utility

Manages research workflow state for tracking phases, quality gates,
and agent assignments across sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


STATE_FILE = Path('.claude/state/research-workflow-state.json')


def load_state() -> Dict[str, Any]:
    """Load state from JSON file"""
    if not STATE_FILE.exists():
        return create_initial_state()

    try:
        with STATE_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading state: {e}", flush=True)
        return create_initial_state()


def save_state(state: Dict[str, Any]) -> None:
    """Save state to JSON file"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    try:
        with STATE_FILE.open('w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        print(f"Error saving state: {e}", flush=True)


def create_initial_state() -> Dict[str, Any]:
    """Create initial state structure"""
    return {
        'version': '1.0.0',
        'sessions': [],
        'currentResearch': None
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
