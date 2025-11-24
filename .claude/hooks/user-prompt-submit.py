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
import os
import re
import sys
from pathlib import Path

# =============================================================================
# DEBUG MODE (set COMPOUND_DETECTION_DEBUG=true to enable verbose logging)
# =============================================================================
DEBUG = os.environ.get('COMPOUND_DETECTION_DEBUG', 'false').lower() == 'true'

# =============================================================================
# NEGATION PATTERNS (Critical Fix #2)
# =============================================================================
# These patterns indicate user explicitly does NOT want a skill
# Check these BEFORE other pattern matching

NEGATION_PATTERNS = {
    'research': [
        r"(don't|do not|dont|skip|without|no need to|not going to|won't|will not|shouldn't|should not|avoid)\s+(the\s+)?(research|search|investigat|analyz|study|explor)",
        r"(research|search|investigation|analysis)\s+(is\s+)?(not\s+)?(needed|required|necessary)",
        r"(skip|bypass|ignore)\s+(the\s+)?(research|search|investigation|analysis)",
        r"(already\s+)?(researched|searched|investigated|analyzed|studied)",
    ],
    'planning': [
        r"(don't|do not|dont|skip|without|no need to|not going to|won't|will not|shouldn't|should not|avoid)\s+(the\s+)?(plan|build|design|creat|develop|implement|architect)",
        r"(planning|building|design|development|implementation)\s+(is\s+)?(not\s+)?(needed|required|necessary)",
        r"(skip|bypass|ignore)\s+(the\s+)?(planning|design|architecture|specs|specification)",
        r"(already\s+)?(planned|built|designed|created|developed|implemented)",
    ],
}

# =============================================================================
# COMPOUND NOUN PATTERNS (High Fix #4)
# =============================================================================
# These look like TRUE compounds but are actually single planning actions
# "Build a search and analysis tool" - compound noun, not two actions

COMPOUND_NOUN_PATTERNS = [
    r'(build|create|design|develop|implement)\s+(a|an|the)\s+\w{0,20}\s*(search|research|analysis|investigation)\s+and\s+(search|research|analysis|analytics|investigation|exploration|study)\s+(tool|system|feature|platform|dashboard|interface|engine|module|component|service|application|app)',
    r'(build|create|design|develop|implement)\s+(a|an|the)\s+\w{0,20}\s*(build|design|plan|development)\s+and\s+(build|design|plan|development|deploy|test)\s+(tool|system|pipeline|workflow|process|platform)',
    r'(build|create|design|develop|implement)\s+(a|an|the)\s+\w{0,20}\s*\w+-and-\w+\s+(tool|system|feature|component|module)',
    r'(build|create|design|develop|implement)\s+(a|an|the)?\s*(research\s+and\s+development|R&D|r&d)\s+(team|department|lab|facility|center|process|pipeline|workflow|system)',
]

# =============================================================================
# AGENT NOUN EXCLUSIONS (Critical Fix #1 - supplementary)
# =============================================================================
# Words that contain skill keywords but are agent nouns, not action verbs

AGENT_NOUN_EXCLUSIONS = [
    'researcher', 'researchers',
    'builder', 'builders',
    'designer', 'designers',
    'planner', 'planners',
    'developer', 'developers',
    'architect', 'architects',
    'analyst', 'analysts',
    'investigator', 'investigators',
    'explorer', 'explorers',
    'examiner', 'examiners',
]

# =============================================================================
# TRUE COMPOUND PATTERNS
# =============================================================================
# Both keywords are ACTION verbs (user wants BOTH workflows)

TRUE_COMPOUND_PATTERNS = [
    r'(search|research|investigate|analyze|find|explore|study|examine)\s+.{0,60}\s+(and|then|,\s*then|;\s*then|after that|followed by)\s+(build|plan|design|create|implement|develop|architect|make)',
    r'(build|plan|design|create|develop|implement)\s+.{0,60}\s+(and|then|after|;\s*then)\s+(research|search|investigate|analyze|study)',
    r'first\s+(research|search|investigate|explore|analyze).{0,60}(then|after|before).{0,30}(build|plan|design|create|implement)',
    r'(research|investigate|search|analyze|explore)\s+.{0,60}\s+and\s+(build|design|create|plan|implement)\s+(it|that|this|the\s+\w+)',
    r'(want to|need to|going to|let\'s|we should|I\'ll|i\'ll)\s+(research|search|investigate).{0,60}(and|then)\s+(build|plan|design|create)',
    r'(building|planning|designing|creating|developing|implementing)\s+.{0,60}\s+(after|before|while)\s+(researching|searching|investigating|analyzing|studying)',
    r'(researching|searching|investigating|analyzing|studying|exploring)\s+.{0,60}\s+(before|then|and)\s+(building|planning|designing|creating|implementing)',
    r'(research|investigate|search|analyze|explore|study)\s+\w+.{0,40},\s*(build|plan|design|create|implement|develop)\s+',
]

# =============================================================================
# FALSE COMPOUND: Planning is ACTION, research keyword is SUBJECT
# =============================================================================
# Route to: PLANNING skill

FALSE_COMPOUND_PLANNING_ACTION = [
    r'(build|create|design|plan|develop|architect|implement|make|construct)\s+(a|an|the)\s+\w{0,30}\s*(search|research|analytics?|investigation|analysis|exploration|study|survey|review|assessment|evaluation|finder|explorer)\s*(feature|tool|system|platform|module|component|interface|dashboard|service|API|endpoint|functionality|capability|engine|mechanism|solution|application|app|page|widget|bar)?',
    r'(design|plan|create|build|develop|architect)\s+(a\s+|an\s+|the\s+)?(research|search|analysis|investigation|exploration|study)\s+(method|methodology|approach|strategy|plan|workflow|process|pipeline|system|framework|architecture|tool|platform|solution|technique|procedure)',
    r'(create|build|design|develop|implement|establish)\s+(research|search|analysis|investigation)\s+(infrastructure|tooling|capabilities|capacity|resources|team|department|lab|center|facility)',
    r'(building|creating|designing|planning|developing|implementing|constructing)\s+(a|an|the)\s+\w{0,25}\s*(search|research|analytics?|analysis|investigation)\s*(feature|tool|system|interface|component|module|page|widget)?',
]

# =============================================================================
# FALSE COMPOUND: Research is ACTION, planning keyword is SUBJECT
# =============================================================================
# Route to: RESEARCH skill

FALSE_COMPOUND_RESEARCH_ACTION = [
    r'(research|search|find|look|investigate|analyze|study|explore|examine|review|assess|evaluate)\s+(for\s+)?(the\s+)?(best\s+|good\s+|top\s+|recommended\s+|popular\s+|common\s+|modern\s+)?\w{0,20}\s*(build|design|architecture|architectural|planning|implementation|development|deployment|infrastructure|construction)\s*(tool|tools|pattern|patterns|practice|practices|method|methods|approach|approaches|framework|frameworks|system|systems|process|processes|solution|solutions|technique|techniques|strategy|strategies|software|platform|platforms|failure|failures|error|errors|issue|issues|problem|problems|performance|speed|time|output|results|configuration|settings|options|dependencies|requirement|requirements|pipeline|pipelines|workflow|workflows|automation|script|scripts|guide|guides|tutorial|tutorials|documentation|docs|example|examples|template|templates)',
    r'(search|find|look|grep|scan|check)\s+(for\s+|in\s+|through\s+)?(the\s+)?\w{0,15}\s*(build|design|plan|implementation|deployment|architecture|development|test|testing)\s*(log|logs|file|files|doc|docs|document|documents|output|outputs|error|errors|issue|issues|record|records|history|artifact|artifacts|report|reports|result|results|failure|failures|warning|warnings|message|messages|trace|traces|dump|dumps|metric|metrics|stat|stats|status)',
    r'(research|analyze|study|examine|investigate|review|assess|evaluate|audit|inspect|explore|understand|learn about)\s+(the\s+)?(existing\s+|current\s+|legacy\s+|old\s+|previous\s+|original\s+|proposed\s+|new\s+|updated\s+)?(design|architecture|architectural|plan|planning|implementation|build|system|infrastructure|codebase|code|structure|schema|model|spec|specification|blueprint|diagram|flow|workflow)',
    r'(research|search|find|investigate|study|explore|analyze|examine|review)\s+(design|architectural|build|implementation|development|deployment|coding|programming|software|system)\s+(pattern|patterns|principle|principles|practice|practices|standard|standards|convention|conventions|guideline|guidelines|approach|approaches|anti-pattern|anti-patterns|smell|smells|idiom|idioms)',
    r'(researching|searching|finding|investigating|studying|exploring|analyzing|examining|reviewing|learning about|looking into|checking)\s+(design|architectural|build|implementation|development|planning|deployment|infrastructure|system)\s+(pattern|patterns|tool|tools|practice|practices|method|methods|approach|approaches|failure|failures|error|errors|issue|issues|option|options|alternative|alternatives|solution|solutions)',
    r'(research|search|find|investigate|study|explore|learn|understand)\s+(how\s+to\s+|ways\s+to\s+|methods\s+to\s+|approaches\s+to\s+)(build|design|plan|implement|develop|architect|create|deploy)',
    r'(research|search|find|investigate|study|explore|analyze)\s+.{3,40}\s+(for|to help with|to support|to enable|to improve)\s+(building|designing|planning|implementing|developing|creating|deploying)',
]

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
