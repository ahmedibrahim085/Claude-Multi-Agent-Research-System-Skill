#!/usr/bin/env python3
"""
User Prompt Submit Hook: Universal Skill Activation

This hook intercepts user prompts BEFORE they reach Claude and checks against
skill-rules.json triggers for both multi-agent-researcher and spec-workflow-orchestrator.

When triggers match, it injects enforcement reminders to ensure proper skill activation.

Pattern Source: claude-agent-sdk-demos + Claude-Flow
Enhancement: Multi-skill detection, regex pattern matching, comprehensive enforcement
"""

import json
import re
import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'utils'))


def get_project_root() -> Path:
    """Get project root directory"""
    # From .claude/hooks/ go up two levels
    return Path(__file__).parent.parent.parent


def load_skill_rules() -> dict:
    """Load skill-rules.json"""
    project_root = get_project_root()
    rules_path = project_root / '.claude' / 'skills' / 'skill-rules.json'

    try:
        with open(rules_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load skill-rules.json: {e}", file=sys.stderr)
        return {}


def check_keywords(prompt: str, keywords: list) -> list:
    """Check if any keywords are present in the prompt (case-insensitive)"""
    prompt_lower = prompt.lower()
    matched = []

    for keyword in keywords:
        if keyword.lower() in prompt_lower:
            matched.append(keyword)

    return matched


def check_patterns(prompt: str, patterns: list) -> list:
    """Check if any regex patterns match the prompt (case-insensitive)"""
    matched = []

    for pattern in patterns:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                matched.append(pattern)
        except re.error:
            # Skip invalid regex patterns
            continue

    return matched


def detect_skill_triggers(prompt: str, skill_rules: dict) -> dict:
    """
    Detect which skills should be triggered based on the prompt

    Returns: {
        'multi-agent-researcher': {'keywords': [...], 'patterns': [...]},
        'spec-workflow-orchestrator': {'keywords': [...], 'patterns': [...]}
    }
    """
    triggers = {}

    for skill_name, skill_config in skill_rules.get('skills', {}).items():
        prompt_triggers = skill_config.get('promptTriggers', {})
        keywords = prompt_triggers.get('keywords', [])
        patterns = prompt_triggers.get('intentPatterns', [])

        matched_keywords = check_keywords(prompt, keywords)
        matched_patterns = check_patterns(prompt, patterns)

        if matched_keywords or matched_patterns:
            triggers[skill_name] = {
                'keywords': matched_keywords,
                'patterns': matched_patterns,
                'enforcement': skill_config.get('enforcement', 'recommend'),
                'priority': skill_config.get('priority', 'medium')
            }

    return triggers


def build_research_enforcement_message(triggers: dict) -> str:
    """Build enforcement message for multi-agent-researcher skill"""
    matched_keywords = triggers.get('keywords', [])
    matched_patterns = triggers.get('patterns', [])

    keywords_str = ', '.join(f'"{k}"' for k in matched_keywords[:5])
    if len(matched_keywords) > 5:
        keywords_str += f' (+{len(matched_keywords) - 5} more)'

    patterns_str = f'{len(matched_patterns)} intent pattern(s)' if matched_patterns else 'none'

    return f"""
🔒 RESEARCH WORKFLOW ENFORCEMENT ACTIVATED

**Detected**: Research task keywords in your prompt
**Matched Keywords**: {keywords_str}
**Matched Patterns**: {patterns_str}

**Required Skill**: multi-agent-researcher

**CRITICAL REMINDER**:
❌ DO NOT use WebSearch/WebFetch directly for multi-source research
✅ MUST invoke multi-agent-researcher skill

**Mandatory Workflow**:
1. STOP - Don't use WebSearch/WebFetch yourself
2. INVOKE - Use `/skill multi-agent-researcher` or let auto-activate
3. DECOMPOSE - Break topic into 2-4 focused subtopics
4. PARALLEL - Spawn researcher agents simultaneously (NOT sequentially)
5. SYNTHESIZE - Spawn report-writer agent for final report

**Self-Check**:
- Is this multi-source research? → Use Skill
- Will I need synthesis? → Use Skill
- Am I about to do >3 searches? → Use Skill

**Enforcement Level**: CRITICAL (guardrail - blocks direct tool use)

---
""".strip()


def build_planning_enforcement_message(triggers: dict) -> str:
    """Build enforcement message for spec-workflow-orchestrator skill"""
    matched_keywords = triggers.get('keywords', [])
    matched_patterns = triggers.get('patterns', [])

    keywords_str = ', '.join(f'"{k}"' for k in matched_keywords[:5])
    if len(matched_keywords) > 5:
        keywords_str += f' (+{len(matched_keywords) - 5} more)'

    patterns_str = f'{len(matched_patterns)} intent pattern(s)' if matched_patterns else 'none'

    return f"""
🔒 PLANNING WORKFLOW ENFORCEMENT ACTIVATED

**Detected**: Planning task keywords in your prompt
**Matched Keywords**: {keywords_str}
**Matched Patterns**: {patterns_str}

**Required Skill**: spec-workflow-orchestrator

**CRITICAL REMINDER**:
❌ DO NOT start manual planning with TodoWrite or direct file creation
✅ MUST invoke spec-workflow-orchestrator skill

**Mandatory Workflow**:
1. STOP - Don't start planning manually
2. INVOKE - Use `/skill spec-workflow-orchestrator` or let auto-activate
3. ANALYZE - Spawn spec-analyst for requirements gathering
4. ARCHITECT - Spawn spec-architect for system design + ADRs
5. PLAN - Spawn spec-planner for task breakdown
6. VALIDATE - Quality gate (85% threshold) with iteration if needed

**Self-Check**:
- Am I about to plan/design/architect a new feature/system? → Use Skill
- Did user ask for specs/requirements/features? → Use Skill
- Is this more than trivial planning? → Use Skill

**Enforcement Level**: HIGH (recommended - helps ensure comprehensive planning)

---
""".strip()


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    user_prompt = input_data.get('user_prompt', '')

    if not user_prompt or len(user_prompt.strip()) < 5:
        sys.exit(0)

    # Load skill rules
    skill_rules = load_skill_rules()
    if not skill_rules:
        sys.exit(0)

    # Detect which skills should be triggered
    triggers = detect_skill_triggers(user_prompt, skill_rules)

    if not triggers:
        # No skill triggers detected
        sys.exit(0)

    # Build enforcement messages
    messages = []

    # Priority order: research (critical) > planning (high)
    if 'multi-agent-researcher' in triggers:
        messages.append(build_research_enforcement_message(triggers['multi-agent-researcher']))

    if 'spec-workflow-orchestrator' in triggers:
        messages.append(build_planning_enforcement_message(triggers['spec-workflow-orchestrator']))

    # Output enforcement messages
    if messages:
        combined_message = '\n\n'.join(messages)
        output = {
            'systemMessage': combined_message
        }
        print(json.dumps(output))

    # Exit successfully
    sys.exit(0)


if __name__ == '__main__':
    main()
