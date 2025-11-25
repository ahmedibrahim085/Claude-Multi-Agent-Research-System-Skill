# Project Instructions for anthropic_research

## CRITICAL: Research Orchestration Rules

### ALWAYS Use multi-agent-researcher Skill When:

**Trigger Keywords in User Prompt**:
- **Search/Discovery**: "search", "find", "find out", "look up", "look into", "discover", "uncover"
- **Investigation**: "research", "investigate", "analyze", "study", "explore", "examine", "survey", "assess", "evaluate", "review", "inspect", "probe", "scrutinize"
- **Collection**: "gather", "collect", "compile"
- **Learning**: "learn about", "tell me about", "dig into", "delve into"
- **Contextual**: "what are the latest", "comprehensive", "deep dive", "thorough investigation", "in-depth", "detailed overview", "landscape of", "state of the art", "best practices"

**MANDATORY Workflow**:
1. **STOP** - Do NOT use WebSearch/WebFetch directly for research tasks
2. **INVOKE**: Use `/skill multi-agent-researcher` or let it auto-activate
3. **DECOMPOSE**: Break topic into 2-4 focused subtopics
4. **PARALLEL**: Spawn researcher agents simultaneously (NOT sequentially)
5. **SYNTHESIZE**: Aggregate findings into comprehensive report

### Direct Tool Use vs Skill Orchestration

**Use WebSearch/WebFetch directly ONLY for**:
- Single factual lookups (e.g., "What is the capital of France?")
- Quick documentation checks (e.g., "How to use Array.map in JavaScript?")
- Specific URL fetches (e.g., "Fetch this exact GitHub README")

**Use multi-agent-researcher Skill for**:
- Multi-source research (2+ sources)
- Comprehensive topic investigation
- Comparative analysis
- Literature reviews
- Market research
- Technology surveys
- ANY task requiring synthesis across multiple sources

### Example Violations to AVOID

❌ **WRONG**: User asks "investigate MCP servers for research"
   → I do 15 sequential WebSearch calls myself

✅ **CORRECT**: User asks "investigate MCP servers for research"
   → I invoke multi-agent-researcher skill
   → Skill spawns 3 parallel researchers
   → Each researcher investigates subtopic
   → I spawn report-writer agent for synthesis
   → Report-writer agent creates final report

### Self-Check Before Acting

**Before using WebSearch/WebFetch, ask yourself**:
1. Is this a research task requiring multiple sources? → Use Skill
2. Will I need to synthesize information? → Use Skill
3. Am I about to do >3 searches on related topics? → Use Skill
4. Did user say "research", "investigate", "analyze"? → Use Skill

## CRITICAL: Synthesis Phase Enforcement

### ⚠️ ARCHITECTURAL CONSTRAINT ACTIVE

When multi-agent-researcher skill is active, you **DO NOT HAVE WRITE TOOL ACCESS**. The skill's `allowed-tools` frontmatter EXCLUDES the Write tool to enforce proper workflow delegation.

### Synthesis Phase Requirements

**ABSOLUTE PROHIBITION**:
- ❌ Orchestrator writing synthesis reports directly
- ❌ Creating files in files/reports/ yourself
- ❌ Using "direct synthesis" approach
- ❌ Bypassing report-writer agent
- ❌ Attempting to write reports when skill is active

**MANDATORY WORKFLOW**:
- ✅ Spawn report-writer agent via Task tool
- ✅ Agent reads ALL files/research_notes/*.md files
- ✅ Agent synthesizes findings into comprehensive report
- ✅ Agent writes to files/reports/{topic}_{timestamp}.md
- ✅ Orchestrator reads final report and delivers to user

### Self-Check Before Synthesis

**Before attempting synthesis, ask yourself**:
1. Am I the orchestrator with multi-agent-researcher skill active? → MUST use report-writer agent
2. Do I have Write tool access? → If NO, spawn report-writer agent
3. Have all research notes been completed? → Verify with Glob before synthesis
4. Am I about to write to files/reports/? → STOP, delegate to report-writer agent

### Why This Enforcement Exists

**Problem Identified**: Orchestrator was doing synthesis directly, bypassing the report-writer agent's specialized synthesis capabilities.

**Solution**: Architectural constraint - orchestrator lacks Write tool when skill is active, making it physically impossible to write reports. This forces proper delegation.

**Reliability**: ~95% enforcement (cannot be bypassed through prompt injection)

### Example Violation and Correction

❌ **WRONG**: After researchers complete
   → I read the research notes
   → I write synthesis report myself
   → Result: Tool permission error (Write not in allowed-tools)

✅ **CORRECT**: After researchers complete
   → I verify all notes exist with Glob
   → I spawn report-writer agent via Task tool
   → Agent reads notes and writes comprehensive report
   → I read final report and deliver to user

---

## CRITICAL: Planning Orchestration Rules

### ALWAYS Use spec-workflow-orchestrator Skill When:

**Trigger Keywords in User Prompt**:
- **Planning Actions**: "plan", "design", "architect", "blueprint", "outline", "draft", "sketch", "map out", "structure", "organize", "prototype", "model", "define", "specify", "scaffold", "frame", "conceptualize"
- **Build/Create**: "build", "create", "develop", "implement", "construct", "craft", "engineer", "make", "set up", "establish"
- **Specifications**: "specs", "specifications", "requirements", "functional requirements", "non-functional requirements", "acceptance criteria", "user stories", "use cases", "scenarios", "test cases"
- **Architecture**: "architecture", "system design", "technical design", "infrastructure", "framework", "schema", "data model", "API design", "component design"
- **Requirements**: "analyze requirements", "gather requirements", "define requirements", "requirement analysis", "feasibility study", "needs assessment", "scope definition"
- **Documentation**: "PRD", "product requirements document", "technical spec", "design doc", "architecture document", "ADR", "architecture decision record", "RFC", "proposal"
- **Features**: "features", "feature list", "capabilities", "functionality", "feature set", "feature spec", "MVP", "minimum viable product"
- **Planning Phases**: "roadmap", "project plan", "implementation plan", "development plan", "rollout plan", "migration plan", "deployment plan"
- **Conversational**: "what should we build", "how should we structure", "what's the best approach", "help me plan", "need to design", "want to architect", "thinking about building", "considering implementing", "what are the requirements for", "what features should", "how do we implement", "what's the architecture", "need specs for", "create a plan for", "design a system for", "outline the approach", "ready for development", "before we start coding", "what do we need", "how should this work"

**MANDATORY Workflow**:
1. **STOP** - Do NOT start manual planning with TodoWrite or direct file creation
2. **INVOKE**: Use `/skill spec-workflow-orchestrator` or let it auto-activate
3. **ANALYZE**: Spawn spec-analyst agent for requirements gathering
4. **ARCHITECT**: Spawn spec-architect agent for system design + ADRs
5. **PLAN**: Spawn spec-planner agent for task breakdown
6. **VALIDATE**: Quality gate (85% threshold) with iteration if needed

### Direct Planning vs Skill Orchestration

**Do Manual Planning ONLY for**:
- Trivial tasks (single-file changes, simple fixes)
- Tasks with 1-2 steps that don't need formal specs
- Quick experiments or prototypes explicitly marked as throwaway

**Use spec-workflow-orchestrator Skill for**:
- New features or systems (any non-trivial addition)
- Architecture changes (refactoring, new patterns)
- Multi-component work (3+ files or modules)
- Requirements gathering (when user asks "what should we build?")
- ANY task requiring formal specifications
- Projects needing ADRs or technical design docs

### Example Violations to AVOID

❌ **WRONG**: User asks "build a local web interface for session logs"
   → I create TodoWrite list and start planning manually
   → I analyze requirements myself
   → I write specs directly

✅ **CORRECT**: User asks "build a local web interface for session logs"
   → I invoke spec-workflow-orchestrator skill
   → Skill spawns spec-analyst for requirements (outputs: docs/planning/requirements.md)
   → Skill spawns spec-architect for design (outputs: docs/planning/architecture.md + docs/adrs/*.md)
   → Skill spawns spec-planner for tasks (outputs: docs/planning/tasks.md)
   → Quality gate validates all deliverables (85% threshold)

### Self-Check Before Acting

**Before starting planning work, ask yourself**:
1. Is this a new feature/system/architecture? → Use Skill
2. Did user ask for specs/requirements/features? → Use Skill
3. Will this require >3 files or multi-component work? → Use Skill
4. Did user say "plan", "design", "build", "architect"? → Use Skill
5. Is this more than a trivial 1-2 step task? → Use Skill

### Quality Gates

The spec-workflow-orchestrator enforces quality standards:
- **Threshold**: 85% (100 points total, 4 criteria per deliverable)
- **Max Iterations**: 3 attempts per agent
- **Criteria**: Completeness, Technical Depth, Actionability, Clarity
- **Outputs**: requirements.md (~800-1,500 lines), architecture.md + ADRs, tasks.md (~500-800 lines)

---

## CRITICAL: Compound Request Handling

### What is a Compound Request?

A user request that triggers MULTIPLE skills simultaneously because it contains action verbs for both research AND planning.

**Example**: "Search for notification systems and build it"
- "Search" triggers: multi-agent-researcher (research action)
- "build" triggers: spec-workflow-orchestrator (planning action)
- Result: COMPOUND REQUEST → needs user clarification

### How Detection Works

The `user-prompt-submit` hook analyzes requests using two methods:

#### 1. Signal Strength Analysis
Determines if a keyword is used as an ACTION (verb) or SUBJECT (noun):

| Signal Type | Criteria | Interpretation |
|-------------|----------|----------------|
| **Strong** | Intent pattern matched | Keyword is ACTION verb |
| **Medium** | 3+ keywords, no pattern | Uncertain |
| **Weak** | 1-2 keywords, no pattern | Keyword is likely SUBJECT |
| **None** | No matches | Skill not triggered |

#### 2. Compound Pattern Matching
Checks against known TRUE and FALSE compound patterns:

- **TRUE Compound**: `"research X AND build Y"` - both are actions
- **FALSE Compound**: `"build a search feature"` - search is subject

### Decision Matrix

| Research Signal | Planning Signal | Compound Type | Result |
|-----------------|-----------------|---------------|--------|
| Strong | Strong | TRUE compound | **ASK USER** |
| Strong | Strong | FALSE compound | Primary skill (from pattern) |
| Strong | Weak/Medium | Any | Research only |
| Weak/Medium | Strong | Any | Planning only |
| Weak | Weak | Any | **ASK USER** (safe default) |

### Examples

| Prompt | Research | Planning | Result |
|--------|----------|----------|--------|
| "Search for notification systems and build it" | STRONG | STRONG | **ASK USER** |
| "Build a search feature" | WEAK | STRONG | Planning only |
| "Research build tools" | STRONG | WEAK | Research only |
| "Hire a researcher" | NONE | NONE | No skill |
| "Don't research, just build it" | NONE (negated) | STRONG | Planning only |
| "Build a search and analysis tool" | WEAK | STRONG | Planning only (compound noun) |

### When You See "COMPOUND REQUEST DETECTED"

This system message means BOTH keywords are detected as ACTION verbs.

**YOU MUST:**
1. Use AskUserQuestion tool with the standard options
2. Wait for user response
3. Execute ONLY the chosen skill(s)

**YOU MUST NOT:**
- Invoke any skill before user responds
- Assume you know what user wants
- Skip the clarification step

### AskUserQuestion Template

```json
{
  "questions": [{
    "question": "This request involves both research and planning. How would you like to proceed?",
    "header": "Workflow",
    "multiSelect": false,
    "options": [
      {"label": "Research → Plan", "description": "Research first, then I'll ask you to proceed with planning"},
      {"label": "Research only", "description": "Just investigate and report findings"},
      {"label": "Plan only", "description": "Create specifications using existing knowledge"},
      {"label": "Both sequentially", "description": "Research first, then plan (separate workflows, no data sharing)"}
    ]
  }]
}
```

### Actions After User Responds

| User Choice | Claude Action |
|-------------|---------------|
| **Research → Plan** | Invoke research skill, wait for completion, tell user "Reply 'proceed with planning' when ready", wait for user, then invoke planning skill |
| **Research only** | Invoke research skill, deliver report, done |
| **Plan only** | Invoke planning skill, deliver specs, done |
| **Both sequentially** | Invoke research skill, deliver report, immediately invoke planning skill (no wait), deliver specs |

### IMPORTANT: "Research → Plan" Limitation

When user selects "Research → Plan", Claude Code **cannot automatically chain** the skills.

**What actually happens:**
1. Research skill completes and produces report
2. User must **manually request** planning in a follow-up message
3. Planning skill then runs using research outputs as context

**Claude should inform user:**
> "I'll start with the research phase. Once complete, please ask me to proceed with planning, and I'll use the research findings to inform the specifications."

---

## Available Skills

- **multi-agent-researcher**: Orchestrates 2-4 parallel researchers for comprehensive topic investigation
- **spec-workflow-orchestrator**: Orchestrates 3 sequential planning agents for development-ready specifications

## Available Agents

### Research Agents:
- **researcher**: Web research agent (WebSearch, Write, Read) - DO NOT invoke directly, use via skill
- **report-writer**: Synthesis agent (Read, Glob, Write)

### Planning Agents:
- **spec-analyst**: Requirements gathering agent (Read, Write) - DO NOT invoke directly, use via skill
- **spec-architect**: System design agent (Read, Write) - DO NOT invoke directly, use via skill
- **spec-planner**: Task breakdown agent (Read, Write) - DO NOT invoke directly, use via skill

## File Organization

- `files/research_notes/`: Individual researcher outputs (one file per subtopic)
- `files/reports/`: Comprehensive synthesis reports (timestamped)
- Name format: `topic-slug_YYYYMMDD-HHMMSS.md`
- `docs/planning/`: Active planning documents (requirements, architecture, tasks)
- `docs/adrs/`: Architecture Decision Records (numbered format)

## Custom Configuration Files

This project uses several **custom** files that are NOT part of official Claude Code:

### .claude/config.json
**Purpose**: Custom project paths configuration
**Content**: Defines paths for logs, reports, research notes
**Example**:
```json
{
  "paths": {
    "logs": "logs",
    "reports": "files/reports",
    "research_notes": "files/research_notes"
  }
}
```

### logs/state/
**Purpose**: Runtime state management directory (gitignored)
**Content**: Session state, workflow progress tracking
**Files**:
- `research-workflow-state.json`: Tracks active research sessions
- `spec-workflow-state.json`: Tracks active planning sessions
**Note**: Moved from `.claude/state/` to follow Claude Code best practices

### .claude/utils/
**Purpose**: Python utility modules for hooks and validation
**Files**:
- `config_loader.py`: Load and parse config.json
- `session_logger.py`: Session logging utilities
- `state_manager.py`: State persistence helpers

### .claude/validation/
**Purpose**: Quality gate validation logic for planning skill
**Usage**: spec-workflow-orchestrator uses these modules to score deliverables
**Note**: Custom implementation, not standard Claude Code feature

### .claude/workflows/
**Purpose**: Workflow definition files
**Usage**: Define multi-step workflows for complex operations
**Note**: Custom organizational structure

### .claude/skills/skill-rules.json
**Purpose**: Custom skill activation rules (NOT official Claude Code)
**Content**: Trigger keywords and patterns for both skills
**Usage**: Loaded by hooks to detect when to suggest/activate skills
**Format**:
```json
{
  "skills": {
    "multi-agent-researcher": {
      "promptTriggers": {
        "keywords": ["research", "investigate", "analyze", ...],
        "intentPatterns": ["(research|investigate) .* for .*", ...]
      }
    },
    "spec-workflow-orchestrator": {
      "promptTriggers": {
        "keywords": ["plan", "design", "architect", "build", ...],
        "intentPatterns": ["(plan|design) .* (application|app|system)", ...]
      }
    }
  }
}
```

### Official vs Custom Files

**Official Claude Code files** (from documentation):
- ✅ `.claude/CLAUDE.md` - Project instructions
- ✅ `.claude/settings.json` - Claude Code settings
- ✅ `.claude/settings.local.json` - Local user overrides
- ✅ `.claude/agents/*.md` - Agent definitions
- ✅ `.claude/skills/*/SKILL.md` - Skill orchestrators
- ✅ `.claude/commands/*.md` - Slash commands
- ✅ `.claude/hooks/*.py` - Hook scripts

**Custom project files** (project-specific):
- 🔧 `.claude/config.json` - Custom paths configuration
- 🔧 `.claude/utils/` - Python utility modules
- 🔧 `.claude/validation/` - Quality gate logic
- 🔧 `.claude/workflows/` - Workflow definitions
- 🔧 `.claude/skills/skill-rules.json` - Custom trigger rules
- 🔧 `logs/state/` - Runtime state directory (following best practices)

**Note**: Custom files enable advanced features but are not required for basic Claude Code usage.

## Commit Standards

When committing research work:
- Separate commits for: infrastructure, individual research notes, synthesis reports
- Include key statistics in commit messages
- Tag with source counts and confidence levels
- Co-author attribution to Claude

---

**REMEMBER**: You built the orchestrator - USE IT! Don't play all the instruments yourself when you have an orchestra.
