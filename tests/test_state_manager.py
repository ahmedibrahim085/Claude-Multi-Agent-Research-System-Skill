#!/usr/bin/env python3
"""
Unit tests for state_manager.py

Tests for restored functions:
- validate_quality_gate(): Research workflow quality gate validation
- set_current_skill(): Skill invocation tracking with re-invocation support

Design: Uses real create_session() helper for realistic test data (YAGNI - don't mock what works)
"""

import pytest
import json
from datetime import datetime
from pathlib import Path

# Import functions under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'utils'))
from state_manager import (
    validate_quality_gate,
    set_current_skill,
    create_session,
    CURRENT_STATE_FILE
)


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_state_dir(tmp_path, monkeypatch):
    """Redirect CURRENT_STATE_FILE to temp directory for isolation"""
    state_dir = tmp_path / "logs" / "state"
    state_dir.mkdir(parents=True)
    state_file = state_dir / 'current.json'

    # Patch module-level constant
    import state_manager
    monkeypatch.setattr(state_manager, 'CURRENT_STATE_FILE', state_file)

    return state_dir


@pytest.fixture
def sample_session():
    """Create realistic session using create_session helper"""
    return create_session("Test Research Topic", ["subtopic1", "subtopic2", "subtopic3"])


@pytest.fixture
def sample_state(sample_session):
    """Complete state dict with session for validate_quality_gate tests"""
    return {
        'sessions': [sample_session],
        'currentResearch': sample_session['id']
    }


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: validate_quality_gate()
# ═══════════════════════════════════════════════════════════════════════════

class TestValidateQualityGate:
    """Test quality gate validation for research workflow phases"""

    def test_research_gate_pass(self, sample_state, sample_session):
        """Research gate passes when actual >= expected research notes"""
        # Setup: Add 3 outputs to match expected=3
        sample_session['phases']['research']['outputs'] = [
            'note1.md', 'note2.md', 'note3.md'
        ]

        result = validate_quality_gate(sample_state, sample_session['id'], 'research')

        assert result is True
        assert sample_session['qualityGates']['research']['status'] == 'passed'
        assert sample_session['qualityGates']['research']['actual'] == 3
        assert sample_session['qualityGates']['research']['checkedAt'] is not None

    def test_research_gate_fail(self, sample_state, sample_session):
        """Research gate fails when actual < expected research notes"""
        # Setup: Only 1 output when expected=3
        sample_session['phases']['research']['outputs'] = ['note1.md']

        result = validate_quality_gate(sample_state, sample_session['id'], 'research')

        assert result is False
        assert sample_session['qualityGates']['research']['status'] == 'failed'
        assert sample_session['qualityGates']['research']['actual'] == 1

    def test_synthesis_gate_pass(self, sample_state, sample_session):
        """Synthesis gate passes when report-writer does synthesis"""
        # Setup: Set synthesis agent to expected 'report-writer'
        sample_session['phases']['synthesis']['agent'] = 'report-writer'

        result = validate_quality_gate(sample_state, sample_session['id'], 'synthesis')

        assert result is True
        assert sample_session['qualityGates']['synthesis']['status'] == 'passed'
        assert sample_session['qualityGates']['synthesis']['actualAgent'] == 'report-writer'

    def test_synthesis_gate_fail(self, sample_state, sample_session):
        """Synthesis gate fails when wrong agent does synthesis"""
        # Setup: Wrong agent (researcher instead of report-writer)
        sample_session['phases']['synthesis']['agent'] = 'researcher'

        result = validate_quality_gate(sample_state, sample_session['id'], 'synthesis')

        assert result is False
        assert sample_session['qualityGates']['synthesis']['status'] == 'failed'
        assert sample_session['qualityGates']['synthesis']['actualAgent'] == 'researcher'

    def test_missing_session_returns_false(self, sample_state):
        """Returns False gracefully when session_id not found"""
        result = validate_quality_gate(sample_state, 'nonexistent_session', 'research')

        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# TESTS: set_current_skill()
# ═══════════════════════════════════════════════════════════════════════════

class TestSetCurrentSkill:
    """Test skill invocation tracking with re-invocation support"""

    def test_first_skill_invocation(self, temp_state_dir):
        """First skill invocation creates entry with invocationNumber=1"""
        start_time = datetime.now().isoformat()

        ended = set_current_skill('multi-agent-researcher', start_time)

        # Should return None (no skill to end)
        assert ended is None

        # Verify file written
        state_file = temp_state_dir / 'current.json'
        assert state_file.exists()

        # Verify contents
        with state_file.open() as f:
            state = json.load(f)

        assert state['currentSkill']['name'] == 'multi-agent-researcher'
        assert state['currentSkill']['startTime'] == start_time
        assert state['currentSkill']['endTime'] is None
        assert state['currentSkill']['invocationNumber'] == 1

    def test_same_skill_reinvocation(self, temp_state_dir):
        """Re-invoking same skill increments counter and ends previous"""
        start1 = datetime.now().isoformat()
        set_current_skill('multi-agent-researcher', start1)

        start2 = datetime.now().isoformat()
        ended = set_current_skill('multi-agent-researcher', start2)

        # Should return ended skill
        assert ended is not None
        assert ended['name'] == 'multi-agent-researcher'
        assert ended['endTime'] == start2  # Ended at moment new one starts
        assert ended['trigger'] == 'ReInvocation'
        assert ended['invocationNumber'] == 1

        # Verify new skill has invocationNumber=2
        state_file = temp_state_dir / 'current.json'
        with state_file.open() as f:
            state = json.load(f)

        assert state['currentSkill']['invocationNumber'] == 2

    def test_different_skill_switch(self, temp_state_dir):
        """Switching to different skill ends previous with trigger=NewSkill"""
        start1 = datetime.now().isoformat()
        set_current_skill('multi-agent-researcher', start1)

        start2 = datetime.now().isoformat()
        ended = set_current_skill('spec-workflow-orchestrator', start2)

        # Should return ended skill
        assert ended is not None
        assert ended['name'] == 'multi-agent-researcher'
        assert ended['trigger'] == 'NewSkill'

        # Verify new skill has invocationNumber=1 (reset)
        state_file = temp_state_dir / 'current.json'
        with state_file.open() as f:
            state = json.load(f)

        assert state['currentSkill']['name'] == 'spec-workflow-orchestrator'
        assert state['currentSkill']['invocationNumber'] == 1

    def test_file_persistence_on_missing_file(self, temp_state_dir):
        """Creates state file when missing (first run scenario)"""
        state_file = temp_state_dir / 'current.json'
        assert not state_file.exists()  # Verify missing

        start_time = datetime.now().isoformat()
        set_current_skill('multi-agent-researcher', start_time)

        assert state_file.exists()  # File created

        with state_file.open() as f:
            state = json.load(f)

        assert 'currentSkill' in state
        assert state['currentSkill']['name'] == 'multi-agent-researcher'

    def test_ended_skill_duration_calculated(self, temp_state_dir):
        """Ended skill has duration calculated"""
        start1 = "2025-12-16T10:00:00"
        set_current_skill('multi-agent-researcher', start1)

        start2 = "2025-12-16T10:05:30"  # 5 min 30 sec later
        ended = set_current_skill('spec-workflow-orchestrator', start2)

        assert ended is not None
        assert ended['duration'] is not None
        # Duration format: "5m 30s" or similar
        assert 'm' in ended['duration'] or 's' in ended['duration']
