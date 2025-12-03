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
    # Document types that contain research keywords but are planning artifacts
    r'(prepare|create|write|draft|develop|produce)\s+(a\s+|an\s+|the\s+)?(feasibility\s+study|research\s+proposal|study\s+plan|analysis\s+document|review\s+document)',
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


def check_semantic_search_prerequisites() -> bool:
    """
    Check if semantic-search skill prerequisites are ready.

    Reads SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY from state file.

    Returns:
        True if prerequisites are ready (enable semantic-search enforcement)
        False if prerequisites not ready (fallback to Grep/Glob/Read)

    Default behavior (backward compatible):
        - If state file doesn't exist: return True (lazy initialization)
        - If state file read fails: return True (graceful degradation)
        - If value is explicitly false: return False (prerequisites not met)
    """
    try:
        project_root = get_project_root()
        state_file = project_root / 'logs' / 'state' / 'semantic-search-prerequisites.json'

        # If state file doesn't exist, assume prerequisites ready (backward compat)
        if not state_file.exists():
            return True

        # Read state file
        with open(state_file, 'r') as f:
            state = json.load(f)

        # Get SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY value
        ready = state.get('SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY', True)

        if DEBUG:
            print(f"DEBUG: Semantic-search prerequisites: {ready}", file=sys.stderr)

        return ready

    except Exception as e:
        # On any error, default to True (graceful degradation)
        if DEBUG:
            print(f"DEBUG: Failed to check prerequisites, defaulting to True: {e}", file=sys.stderr)
        return True


# =============================================================================
# HELPER FUNCTIONS FOR COMPOUND DETECTION
# =============================================================================

def check_negation(prompt: str, skill_type: str) -> bool:
    """
    Check if the prompt contains negation for a specific skill.

    Args:
        prompt: User's input prompt
        skill_type: 'research' or 'planning'

    Returns:
        True if negation detected (skill should NOT be triggered)
    """
    patterns = NEGATION_PATTERNS.get(skill_type, [])
    for pattern in patterns:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                if DEBUG:
                    print(f"DEBUG: Negation detected for {skill_type}: {pattern}", file=sys.stderr)
                return True
        except re.error:
            continue
    return False


def check_compound_noun(prompt: str) -> bool:
    """
    Check if prompt contains a compound noun that looks like a TRUE compound.

    Example: "Build a search and analysis tool" - NOT a true compound

    Returns:
        True if compound noun detected (should NOT be treated as TRUE compound)
    """
    for pattern in COMPOUND_NOUN_PATTERNS:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                if DEBUG:
                    print(f"DEBUG: Compound noun detected: {pattern}", file=sys.stderr)
                return True
        except re.error:
            continue
    return False


def is_agent_noun_only(prompt: str, keyword: str) -> bool:
    """
    Check if a keyword appears only as part of an agent noun.

    Example: "researcher" contains "research" but is a noun, not action.

    Args:
        prompt: User's input prompt
        keyword: The keyword to check

    Returns:
        True if keyword only appears in agent noun context
    """
    prompt_lower = prompt.lower()
    keyword_lower = keyword.lower()

    # Check if keyword appears as standalone word (word boundary)
    standalone_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
    standalone_matches = re.findall(standalone_pattern, prompt_lower)

    # Check if keyword appears in agent nouns
    agent_noun_count = 0
    for agent_noun in AGENT_NOUN_EXCLUSIONS:
        if agent_noun.lower() in prompt_lower:
            # Check if this agent noun contains our keyword
            if keyword_lower in agent_noun.lower():
                agent_noun_count += prompt_lower.count(agent_noun.lower())

    # If all occurrences are within agent nouns, it's agent noun only
    return len(standalone_matches) <= agent_noun_count


# =============================================================================
# CORE COMPOUND DETECTION FUNCTIONS
# =============================================================================

def get_signal_strength(prompt: str, skill_config: dict, skill_type: str = None) -> dict:
    """
    Analyze signal strength for a skill based on keyword vs pattern matching.

    KEY INSIGHT:
    - Intent pattern match = keyword is used as ACTION verb = STRONG signal
    - Keyword only match = keyword might be SUBJECT noun = WEAK signal

    CRITICAL FIX #1: Uses word boundary matching to avoid substring false positives
    CRITICAL FIX #2: Checks negation patterns to exclude negated skills

    Args:
        prompt: User's input prompt
        skill_config: Skill configuration from skill-rules.json
        skill_type: 'research' or 'planning' (for negation checking)

    Returns:
        {
            'strength': 'strong' | 'medium' | 'weak' | 'none',
            'keywords': list of matched keywords,
            'patterns': list of matched patterns,
            'is_action': bool - Is keyword used as action verb?,
            'negated': bool - Was this skill negated?
        }
    """
    prompt_triggers = skill_config.get('promptTriggers', {})
    keywords = prompt_triggers.get('keywords', [])
    patterns = prompt_triggers.get('intentPatterns', [])

    # CRITICAL FIX #2: Check negation first
    if skill_type and check_negation(prompt, skill_type):
        return {
            'strength': 'none',
            'keywords': [],
            'patterns': [],
            'is_action': False,
            'negated': True
        }

    # CRITICAL FIX #1: Check keyword matches with WORD BOUNDARY (not substring)
    prompt_lower = prompt.lower()
    matched_keywords = []
    for k in keywords:
        keyword_lower = k.lower()
        # Use word boundary regex instead of simple 'in' check
        word_boundary_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        if re.search(word_boundary_pattern, prompt_lower):
            # Additional check: is this only appearing as agent noun?
            if not is_agent_noun_only(prompt, k):
                matched_keywords.append(k)

    # Check pattern matches
    matched_patterns = []
    for pattern in patterns:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                matched_patterns.append(pattern)
        except re.error:
            continue

    # Determine strength based on match type
    if matched_patterns:
        return {
            'strength': 'strong',
            'keywords': matched_keywords,
            'patterns': matched_patterns,
            'is_action': True,
            'negated': False
        }
    elif len(matched_keywords) >= 3:
        return {
            'strength': 'medium',
            'keywords': matched_keywords,
            'patterns': [],
            'is_action': False,
            'negated': False
        }
    elif matched_keywords:
        return {
            'strength': 'weak',
            'keywords': matched_keywords,
            'patterns': [],
            'is_action': False,
            'negated': False
        }
    else:
        return {
            'strength': 'none',
            'keywords': [],
            'patterns': [],
            'is_action': False,
            'negated': False
        }


def check_compound_patterns(prompt: str) -> dict:
    """
    Check if prompt matches known compound patterns.

    HIGH FIX #4: Checks COMPOUND_NOUN_PATTERNS first to avoid misdetection.

    Returns:
        {
            'type': 'true_compound' | 'false_compound' | 'compound_noun' | 'unclear',
            'primary_skill': 'research' | 'planning' | None
        }
    """
    # HIGH FIX #4: Check compound nouns FIRST
    if check_compound_noun(prompt):
        if DEBUG:
            print(f"DEBUG: Compound noun detected, routing to planning", file=sys.stderr)
        return {'type': 'compound_noun', 'primary_skill': 'planning'}

    # Check TRUE compound patterns
    for pattern in TRUE_COMPOUND_PATTERNS:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                if DEBUG:
                    print(f"DEBUG: TRUE compound match: {pattern}", file=sys.stderr)
                return {'type': 'true_compound', 'primary_skill': None}
        except re.error:
            continue

    # Check FALSE compound patterns - Planning is ACTION
    for pattern in FALSE_COMPOUND_PLANNING_ACTION:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                if DEBUG:
                    print(f"DEBUG: FALSE compound (planning action): {pattern}", file=sys.stderr)
                return {'type': 'false_compound', 'primary_skill': 'planning'}
        except re.error:
            continue

    # Check FALSE compound patterns - Research is ACTION
    for pattern in FALSE_COMPOUND_RESEARCH_ACTION:
        try:
            if re.search(pattern, prompt, re.IGNORECASE):
                if DEBUG:
                    print(f"DEBUG: FALSE compound (research action): {pattern}", file=sys.stderr)
                return {'type': 'false_compound', 'primary_skill': 'research'}
        except re.error:
            continue

    return {'type': 'unclear', 'primary_skill': None}


def analyze_request(prompt: str, skill_rules: dict) -> dict:
    """
    Complete analysis of request for compound detection.

    Decision matrix:
    | Research Signal | Planning Signal | Action          |
    |-----------------|-----------------|-----------------|
    | Strong          | Strong          | ASK USER        |
    | Strong          | Weak/Medium     | Research only   |
    | Weak/Medium     | Strong          | Planning only   |
    | Weak            | Weak            | ASK USER (safe) |
    | None            | Any             | That skill only |
    | Any             | None            | That skill only |

    Returns:
        {
            'action': 'ask_user' | 'research_only' | 'planning_only' | 'none',
            'confidence': 'high' | 'medium' | 'low',
            'research_signal': signal strength dict,
            'planning_signal': signal strength dict,
            'compound_type': 'true_compound' | 'false_compound' | 'compound_noun' | 'unclear'
        }
    """
    skills = skill_rules.get('skills', {})

    # Get signal strength for each skill
    research_signal = get_signal_strength(
        prompt,
        skills.get('multi-agent-researcher', {}),
        skill_type='research'
    )
    planning_signal = get_signal_strength(
        prompt,
        skills.get('spec-workflow-orchestrator', {}),
        skill_type='planning'
    )

    result = {
        'action': 'none',
        'confidence': 'low',
        'research_signal': research_signal,
        'planning_signal': planning_signal,
        'compound_type': 'unclear'
    }

    if DEBUG:
        print(f"DEBUG: Research signal: {research_signal}", file=sys.stderr)
        print(f"DEBUG: Planning signal: {planning_signal}", file=sys.stderr)

    # Case 1: Only one skill has signal
    if research_signal['strength'] == 'none' and planning_signal['strength'] != 'none':
        result['action'] = 'planning_only'
        result['confidence'] = 'high' if planning_signal['strength'] == 'strong' else 'medium'
        return result

    if planning_signal['strength'] == 'none' and research_signal['strength'] != 'none':
        result['action'] = 'research_only'
        result['confidence'] = 'high' if research_signal['strength'] == 'strong' else 'medium'
        return result

    if research_signal['strength'] == 'none' and planning_signal['strength'] == 'none':
        result['action'] = 'none'
        return result

    # Case 2: Both skills have signals - check compound patterns
    compound_result = check_compound_patterns(prompt)
    result['compound_type'] = compound_result['type']

    if DEBUG:
        print(f"DEBUG: Compound pattern result: {compound_result}", file=sys.stderr)

    if compound_result['type'] == 'true_compound':
        result['action'] = 'ask_user'
        result['confidence'] = 'high'
        return result

    if compound_result['type'] == 'compound_noun':
        result['action'] = 'planning_only'
        result['confidence'] = 'high'
        return result

    if compound_result['type'] == 'false_compound':
        if compound_result['primary_skill'] == 'planning':
            result['action'] = 'planning_only'
            result['confidence'] = 'high'
        elif compound_result['primary_skill'] == 'research':
            result['action'] = 'research_only'
            result['confidence'] = 'high'
        return result

    # Case 3: Unclear - use signal strength matrix
    rs = research_signal['strength']
    ps = planning_signal['strength']

    if rs == 'strong' and ps == 'strong':
        result['action'] = 'ask_user'
        result['confidence'] = 'medium'
    elif rs == 'strong' and ps in ['medium', 'weak']:
        result['action'] = 'research_only'
        result['confidence'] = 'medium'
    elif ps == 'strong' and rs in ['medium', 'weak']:
        result['action'] = 'planning_only'
        result['confidence'] = 'medium'
    else:
        result['action'] = 'ask_user'
        result['confidence'] = 'low'

    return result


def build_compound_clarification_message(analysis: dict) -> str:
    """
    Build system message for compound requests requiring user clarification.
    """
    confidence = analysis['confidence'].upper()
    research = analysis['research_signal']
    planning = analysis['planning_signal']

    # Format matched triggers with "(none)" fallback
    if research['keywords']:
        research_kw = ', '.join(f'"{k}"' for k in research['keywords'][:3])
        if len(research['keywords']) > 3:
            research_kw += f' (+{len(research["keywords"]) - 3} more)'
    else:
        research_kw = "(none)"

    if planning['keywords']:
        planning_kw = ', '.join(f'"{k}"' for k in planning['keywords'][:3])
        if len(planning['keywords']) > 3:
            planning_kw += f' (+{len(planning["keywords"]) - 3} more)'
    else:
        planning_kw = "(none)"

    research_action = "Yes (verb)" if research['is_action'] else "Maybe (subject?)"
    planning_action = "Yes (verb)" if planning['is_action'] else "Maybe (subject?)"

    return f"""
<system-reminder>
⚠️ COMPOUND REQUEST DETECTED - CLARIFICATION REQUIRED

Detection Confidence: {confidence}

Your request triggers MULTIPLE skill workflows:

RESEARCH SKILL (multi-agent-researcher)
  Signal Strength: {research['strength'].upper()}
  Matched Triggers: {research_kw}
  Used as Action: {research_action}

PLANNING SKILL (spec-workflow-orchestrator)
  Signal Strength: {planning['strength'].upper()}
  Matched Triggers: {planning_kw}
  Used as Action: {planning_action}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛑 MANDATORY: Use AskUserQuestion BEFORE invoking any skill
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST present these options to the user:

1. "Research → Plan" - Research first, then I'll ask you to proceed with planning
2. "Research only" - Just investigate and report findings
3. "Plan only" - Create specifications using existing knowledge
4. "Both sequentially" - Research first, then plan (separate workflows, no data sharing)

DO NOT invoke ANY skill until user responds.
</system-reminder>
""".strip()


# =============================================================================
# ENFORCEMENT MESSAGE BUILDERS
# =============================================================================

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

📖 **Detailed workflow**: docs/workflows/research-workflow.md

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

📖 **Detailed workflow**: docs/workflows/planning-workflow.md

---
""".strip()


def detect_semantic_search_operation(matched_keywords: list, matched_patterns: list) -> str:
    """Detect if this is a SEARCH or INDEX operation based on matched keywords/patterns

    Returns:
        'index' for index management operations (index, reindex, check index, etc.)
        'search' for content search operations (find, search, where is, etc.)
    """
    # Index-related keywords - if any of these match, it's an INDEX operation
    index_keywords = {
        'index', 'reindex', 're-index', 'update index', 'refresh index',
        'rebuild index', 'recreate index', 'create index', 'build index',
        'incremental index', 'incremental reindex', 'full index', 'full reindex',
        'check index', 'index status', 'verify index', 'list projects',
        'indexed projects', 'what projects', 'show projects'
    }

    # Check if any matched keywords are index-related
    for keyword in matched_keywords:
        if keyword.lower() in index_keywords:
            return 'index'

    # Check if patterns contain index-related terms
    index_pattern_terms = ['index', 'reindex', 'projects']
    for pattern in matched_patterns:
        pattern_lower = pattern.lower() if isinstance(pattern, str) else str(pattern).lower()
        if any(term in pattern_lower for term in index_pattern_terms):
            return 'index'

    # Default to search operation
    return 'search'


def build_search_enforcement_message(matched_keywords: list, matched_patterns: list) -> str:
    """Build enforcement message for semantic-search SEARCH operations"""
    keywords_str = ', '.join(f'"{k}"' for k in matched_keywords[:5])
    if len(matched_keywords) > 5:
        keywords_str += f' (+{len(matched_keywords) - 5} more)'

    patterns_str = f'{len(matched_patterns)} intent pattern(s)' if matched_patterns else 'none'

    return f"""
🔍 PROJECT CONTENT SEARCH ENFORCEMENT ACTIVATED (Token Savings)

**Detected**: Content search keywords in your prompt
**Matched Keywords**: {keywords_str}
**Matched Patterns**: {patterns_str}

**Required Skill**: semantic-search

**CRITICAL REMINDER - TOKEN SAVINGS**:
❌ DO NOT use Grep/Glob as first attempt for functionality/content searches
✅ MUST activate semantic-search skill FIRST

**Why This Saves Tokens**:
- Traditional Grep exploration: ~8,000 tokens (20+ Grep searches, 26 file reads)
- Semantic search: ~600 tokens (1 search, 2 targeted reads)
- **Token savings: 92-95% reduction in exploration overhead**

**What Semantic-Search Finds**:
- Code (functions, classes, logic patterns)
- Documentation (markdown, guides, ADRs)
- Configurations (YAML, JSON, env files)
- Cross-format content (auth in code + docs + configs)

**Mandatory Search Hierarchy**:
1. **Am I searching for WHAT content describes?** → Use semantic-search
2. **Do I know exact function/variable name?** → Use Grep
3. **Do I know exact file path?** → Use Read
4. **Am I searching for file name patterns?** → Use Glob

**Correct Workflow**:
1. STOP - Don't use Grep/Glob/Read for functionality/content searches
2. INVOKE - Activate semantic-search skill FIRST
3. SKILL RUNS - Bash scripts executed within skill context
4. ONLY IF SKILL FAILS - Then fallback to Grep/Glob

**Examples**:
❌ WRONG: Grep for "auth", "login", "verify" → 26 file reads → 8,000 tokens
✅ CORRECT: semantic-search "user authentication logic" → 2 file reads → 600 tokens
✅ CORRECT: semantic-search "deployment documentation" → finds docs, configs, README

**Enforcement Level**: HIGH (recommended - saves 5,000-10,000 tokens per task)

📖 **Detailed workflow**: docs/workflows/semantic-search-hierarchy.md

---
""".strip()


def build_index_enforcement_message(matched_keywords: list, matched_patterns: list) -> str:
    """Build enforcement message for semantic-search INDEX operations"""
    keywords_str = ', '.join(f'"{k}"' for k in matched_keywords[:5])
    if len(matched_keywords) > 5:
        keywords_str += f' (+{len(matched_keywords) - 5} more)'

    patterns_str = f'{len(matched_patterns)} intent pattern(s)' if matched_patterns else 'none'

    return f"""
🔧 SEMANTIC INDEX MANAGEMENT ENFORCEMENT ACTIVATED (Performance)

**Detected**: Index management keywords in your prompt
**Matched Keywords**: {keywords_str}
**Matched Patterns**: {patterns_str}

**Required Skill**: semantic-search (indexer agent)

**CRITICAL REMINDER - INCREMENTAL INDEXING**:
❌ DO NOT use full reindex unless necessary (wastes time re-processing unchanged files)
✅ MUST use incremental-reindex FIRST (smart Merkle tree change detection)

**Why Incremental-Reindex is Better**:
- Traditional full reindex: ~186 seconds (re-embeds all files)
- Incremental reindex: ~3 seconds (only changed files, 59x faster)
- **Performance: 59x speedup for typical updates**
- **Proper vector removal**: IndexIDMap2 wrapper (fixes "list index out of range" bug)
- **Smart detection**: Merkle tree identifies new/modified/deleted files automatically

**When to Use Which**:
1. **incremental-reindex (RECOMMENDED - Default)**:
   - Regular updates after code changes
   - Detects and processes only changed files
   - Fast (sub-5 second updates for <100 changed files)
   - Proper vector removal via IndexIDMap2

2. **Full reindex (ONLY IF)**:
   - First-time indexing (no existing index)
   - Major refactoring (100+ files changed)
   - Index corruption/debugging

**Correct Workflow**:
1. INVOKE - Activate semantic-search skill
2. AGENT - semantic-search-indexer spawned automatically
3. OPERATION - incremental-reindex (recommended), or index --full if needed
4. RESULT - Fast update with change statistics

**Examples**:
✅ CORRECT: "update the semantic index" → incremental-reindex → 3s, 68 changed files
✅ CORRECT: "reindex after my changes" → incremental-reindex → detects modified files
❌ WRONG: "full reindex" for 10 changed files → wastes 180+ seconds

**Agent Decision Logic**:
- User says "update"/"reindex"/"refresh" → incremental-reindex (smart)
- User says "full"/"rebuild"/"from scratch" → index --full (as requested)
- User says "check"/"status"/"verify" → status operation

**Enforcement Level**: MEDIUM (recommend incremental, respect user preference for full)

📖 **Implementation details**: docs/status/INCREMENTAL-REINDEX-COMPLETE.md
📖 **Test validation**: docs/testing/incremental-reindex-agent-test.md

---
""".strip()


def build_semantic_search_enforcement_message(triggers: dict) -> str:
    """Build enforcement message for semantic-search skill - routes to SEARCH or INDEX message"""
    matched_keywords = triggers.get('keywords', [])
    matched_patterns = triggers.get('patterns', [])

    # Detect operation type
    operation = detect_semantic_search_operation(matched_keywords, matched_patterns)

    # Route to appropriate message builder
    if operation == 'index':
        return build_index_enforcement_message(matched_keywords, matched_patterns)
    else:
        return build_search_enforcement_message(matched_keywords, matched_patterns)


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

    # Check semantic-search prerequisites BEFORE processing triggers
    # If prerequisites not ready, skip semantic-search enforcement (fallback to Grep/Glob)
    semantic_prerequisites_ready = check_semantic_search_prerequisites()

    if DEBUG:
        print(f"DEBUG: Semantic-search prerequisites ready: {semantic_prerequisites_ready}", file=sys.stderr)

    # NEW: Use analyze_request for smart compound detection
    analysis = analyze_request(user_prompt, skill_rules)

    if DEBUG:
        print(f"DEBUG: Analysis result: {analysis}", file=sys.stderr)

    # Handle based on action
    action = analysis['action']

    # Check semantic-search independently (orthogonal to research/planning)
    # Must check BEFORE early exit to allow semantic-only prompts
    # CONDITIONAL: Only check if prerequisites are ready, otherwise skip enforcement
    if semantic_prerequisites_ready:
        semantic_signal = get_signal_strength(
            user_prompt,
            skill_rules['skills'].get('semantic-search', {}),
            skill_type=None
        )
    else:
        # Prerequisites not ready - skip enforcement, allow Claude to use Grep/Glob/Read
        # Set to "none" strength so all enforcement messages are skipped
        semantic_signal = {
            'strength': 'none',
            'keywords': [],
            'patterns': [],
            'is_action': False,
            'negated': False
        }
        if DEBUG:
            print("DEBUG: Skipping semantic-search enforcement (prerequisites not ready)", file=sys.stderr)

    # EARLY EXIT PROTECTION: If no skills matched, exit immediately (performance)
    if action == 'none' and semantic_signal['strength'] == 'none':
        # No skill triggers detected at all - don't waste CPU
        sys.exit(0)

    if action == 'ask_user':
        # Compound request - need user clarification
        message = build_compound_clarification_message(analysis)
        # Append semantic-search if it also matched (already computed above)
        if semantic_signal['strength'] != 'none':
            semantic_message = build_semantic_search_enforcement_message(semantic_signal)
            message = message + '\n\n' + semantic_message
        output = {'systemMessage': message}
        print(json.dumps(output))
        sys.exit(0)

    # Single skill action
    if action == 'research_only':
        message = build_research_enforcement_message(analysis['research_signal'])
        # Append semantic-search if it also matched (already computed above)
        if semantic_signal['strength'] != 'none':
            semantic_message = build_semantic_search_enforcement_message(semantic_signal)
            message = message + '\n\n' + semantic_message
        output = {'systemMessage': message}
        print(json.dumps(output))
        sys.exit(0)

    if action == 'planning_only':
        message = build_planning_enforcement_message(analysis['planning_signal'])
        # Append semantic-search if it also matched (already computed above)
        if semantic_signal['strength'] != 'none':
            semantic_message = build_semantic_search_enforcement_message(semantic_signal)
            message = message + '\n\n' + semantic_message
        output = {'systemMessage': message}
        print(json.dumps(output))
        sys.exit(0)

    # If action is 'none' but semantic_signal matched, show semantic-search only
    # (This case is possible because semantic is orthogonal to research/planning)
    if action == 'none' and semantic_signal['strength'] != 'none':
        message = build_semantic_search_enforcement_message(semantic_signal)
        output = {'systemMessage': message}
        print(json.dumps(output))
        sys.exit(0)

    # Should never reach here due to early exit protection above
    # But include failsafe
    sys.exit(0)


if __name__ == '__main__':
    main()
