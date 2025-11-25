#!/usr/bin/env python3
"""
Post Tool Use Hook: Research Agent Tracking & Logging

Tracks which agent performs each phase of research workflow, updates state.json,
validates quality gates, and logs all tool calls to transcript.txt and tool_calls.jsonl.

Pattern Source: claude-agent-sdk-demos/research-agent + TDD-Guard
Enhancement: Research-specific phase tracking, quality gate validation, session logging

Usage: Configured in settings.json under PostToolUse hooks (all tools)
"""

import json
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))

try:
    import state_manager
    import session_logger
    import config_loader
except ImportError as e:
    print(f"Failed to import utilities: {e}", file=sys.stderr)
    sys.exit(0)


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)

    tool_name = input_data.get('tool_name')
    tool_input = input_data.get('tool_input', {})
    tool_output = input_data.get('tool_output')

    if not tool_name:
        sys.exit(0)

    # Load current state
    try:
        state = state_manager.load_state()
    except Exception as e:
        print(f"Failed to load state: {e}", file=sys.stderr)
        sys.exit(0)

    # Log ALL tool calls to session logs (transcript.txt and tool_calls.jsonl)
    try:
        session_id = session_logger.get_session_id()
        session_logger.log_tool_call(
            session_id,
            tool_name,
            tool_input,
            tool_output,
            state
        )
    except Exception as e:
        print(f"Failed to log tool call: {e}", file=sys.stderr)
        # Continue execution even if logging fails

    # ═══════════════════════════════════════════════════════════════════════════
    # SKILL INVOCATION TRACKING (Non-Destructive Extension)
    # ═══════════════════════════════════════════════════════════════════════════
    if tool_name == 'Skill':
        skill_name = tool_input.get('skill')
        if skill_name:
            try:
                from datetime import timezone
                timestamp = session_logger.datetime.now(timezone.utc).isoformat()
                current_skill = state_manager.get_current_skill()

                # Check if re-invocation
                if current_skill and current_skill.get('name') == skill_name and not current_skill.get('endTime'):
                    invocation_num = current_skill.get('invocationNumber', 1) + 1
                    print(f"🔄 SKILL RE-INVOKED: {skill_name} (invocation #{invocation_num})", flush=True)
                else:
                    print(f"🎯 SKILL START: {skill_name} (invocation #1)", flush=True)

                # Set current skill (returns ended skill if one was active)
                ended_skill = state_manager.set_current_skill(skill_name, timestamp)

                # Write ended skill to session state file (historical data)
                if ended_skill:
                    session_logger.append_skill_invocation(session_id, ended_skill)
            except Exception as e:
                print(f"Failed to track skill invocation: {e}", file=sys.stderr)

    # Early exit for non-Write operations (rest of hook is Write-specific tracking)
    if tool_name != 'Write':
        sys.exit(0)

    file_path = tool_input.get('file_path')
    if not file_path:
        sys.exit(0)

    # Skip if no active research session
    if not state.get('currentResearch'):
        sys.exit(0)

    sessions = state.get('sessions', [])
    session = next((s for s in sessions if s['id'] == state['currentResearch']), None)

    if not session:
        sys.exit(0)

    # Determine current agent context
    current_agent = identify_current_agent(file_path, state)

    # Track research note creation (use configured path)
    research_notes_dir = config_loader.get_path('research_notes')
    if file_path.startswith(research_notes_dir + '/'):
        outputs = session['phases']['research'].get('outputs', [])

        # Add to outputs if not already present
        if file_path not in outputs:
            outputs.append(file_path)
            session['phases']['research']['outputs'] = outputs

        # Check if all research completed
        expected_count = session['phases']['research'].get('parallelInstances', 0)
        if len(outputs) >= expected_count and len(outputs) > 0:
            session['phases']['research']['status'] = 'completed'
            session['phases']['research']['completedAt'] = session_logger.datetime.now().isoformat()

            # Validate research quality gate
            try:
                research_passed = state_manager.validate_quality_gate(state['currentResearch'], 'research', state)
                if research_passed:
                    message = {
                        'systemMessage': f"✅ Research phase completed: {len(outputs)}/{expected_count} notes created. Research quality gate PASSED."
                    }
                    print(json.dumps(message))
            except Exception:
                pass

        state_manager.save_state(state)
        sys.exit(0)

    # Track synthesis report creation (use configured path)
    reports_dir = config_loader.get_path('reports')
    if file_path.startswith(reports_dir + '/'):
        # Determine agent that wrote the report
        synthesis_agent = current_agent

        # Update synthesis phase
        session['phases']['synthesis']['status'] = 'completed'
        session['phases']['synthesis']['agent'] = synthesis_agent
        session['phases']['synthesis']['output'] = file_path
        session['phases']['synthesis']['completedAt'] = session_logger.datetime.now().isoformat()

        state_manager.save_state(state)

        # Validate synthesis quality gate
        try:
            synthesis_passed = state_manager.validate_quality_gate(state['currentResearch'], 'synthesis', state)
            synthesis_result = session['qualityGates']['synthesis']

            if not synthesis_passed:
                # Quality gate FAILED - emit violation warning
                expected_agent = 'report-writer'
                actual_agent = synthesis_agent

                if actual_agent != expected_agent:
                    violation = f"""
⚠️ WORKFLOW VIOLATION DETECTED ⚠️

**Quality Gate**: Synthesis Enforcement
**Status**: FAILED
**Issue**: Wrong agent performed synthesis

**Expected**: {expected_agent} agent
**Actual**: {actual_agent}

**Impact**:
This violates the established workflow where synthesis must be performed by
the specialized report-writer agent, not the orchestrator.

**Why This Matters**:
- Report-writer agent has specialized synthesis capabilities
- Orchestrator should coordinate, not execute
- Architectural separation prevents "plan dissolution"

**How This Happened**:
- Orchestrator had Write tool access when it shouldn't
- Skill's allowed-tools constraint may have been bypassed
- Agent detection heuristic may be incorrect

**Remediation**:
1. Verify multi-agent-researcher skill v2.0.0+ is active
2. Confirm allowed-tools excludes Write tool
3. Check logs/state/research-workflow-state.json for details
4. Review quality gate validation in state.qualityGates.synthesis

**Audit Trail**:
All details logged to: logs/state/research-workflow-state.json
Session ID: {session['id']}
Violation timestamp: {session_logger.datetime.now().isoformat()}

**Next Steps**:
Despite the violation, the research is complete. The quality gate failure
is logged for analysis and process improvement.
"""

                    message = {'systemMessage': violation.strip()}
                    print(json.dumps(message))
            else:
                # Quality gate PASSED
                message = {
                    'systemMessage': f"✅ Synthesis phase completed by {synthesis_agent}. Synthesis quality gate PASSED."
                }
                print(json.dumps(message))
        except Exception as e:
            print(f"Quality gate validation failed: {e}", file=sys.stderr)

        # Mark delivery phase as in progress (orchestrator will complete it)
        session['phases']['delivery']['status'] = 'in_progress'
        session['phases']['delivery']['startedAt'] = session_logger.datetime.now().isoformat()

        state_manager.save_state(state)
        sys.exit(0)

    # Exit successfully
    sys.exit(0)


def identify_current_agent(file_path: str, state: dict) -> str:
    """Identify which agent is performing the current operation"""
    import os

    # Priority: environment variable > heuristic detection
    if os.environ.get('CLAUDE_AGENT_TYPE'):
        return os.environ['CLAUDE_AGENT_TYPE']

    # Heuristic detection (use configured paths)
    research_notes_dir = config_loader.get_path('research_notes')
    reports_dir = config_loader.get_path('reports')

    if file_path.startswith(research_notes_dir + '/'):
        return 'researcher'
    elif file_path.startswith(reports_dir + '/'):
        return 'report-writer'

    return 'orchestrator'


if __name__ == '__main__':
    main()
