# Project Instructions for anthropic_research

---

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

The spec-workflow-orchestrator enforces quality standards for all deliverables:

**Scoring System**:
- **Total Points**: 100 per deliverable
- **Pass Threshold**: 85/100 (85%)
- **Max Iterations**: 3 attempts per agent (fail after 3rd attempt)

**4 Criteria (25 points each)**:
1. **Completeness** (25 pts): All required sections present, no gaps, comprehensive coverage
2. **Technical Depth** (25 pts): Detailed technical specifications, architectural decisions documented
3. **Actionability** (25 pts): Clear implementation steps, testable acceptance criteria
4. **Clarity** (25 pts): Well-structured, easy to understand, proper formatting

**3 Deliverables Validated**:
- **requirements.md** (spec-analyst): User stories, acceptance criteria, constraints (~800-1,500 lines)
- **architecture.md + ADRs** (spec-architect): System design, technology choices, decision records (~600-1,000 lines)
- **tasks.md** (spec-planner): Implementation tasks, priorities, dependencies (~500-800 lines)

**Validation Flow**:
1. Agent creates deliverable
2. Quality gate validates (4 criteria × 25 points = 100 total)
3. If score ≥85: PASS, proceed to next agent
4. If score <85: FAIL, agent revises (max 3 iterations)
5. After 3 failures: Workflow stops, user notified

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

## CRITICAL: Project Content Search Hierarchy (Token Savings)

### WHY This Matters: Token Economics

**Problem**: Traditional exploration wastes 5,000-10,000 tokens per task:
- Grep for "auth", "login", "verify", "authenticate" → 15+ searches
- Read 20+ files to find the right implementation
- Multiple failed attempts before finding correct code

**Solution**: Semantic search finds functionality in 1 search by understanding MEANING:
- Query: "user authentication logic" → Direct hit in 1 search
- **Token Savings**: ~90% reduction in exploration overhead
- **Speed**: Instant vs 5-10 minutes of trial-and-error

### ABSOLUTE SEARCH HIERARCHY

**BEFORE using Grep/Glob to find functionality or content, ask yourself:**

1. **Am I searching for WHAT content describes** (not exact keywords)? → Use semantic-search
2. **Do I know the exact function/variable name**? → Use Grep
3. **Do I know the exact file path**? → Use Read
4. **Am I searching for file name patterns**? → Use Glob

### ALWAYS Use semantic-search Skill When:

**Trigger Keywords - When I Need To**:
- **Search/Find**: "search", "find", "locate", "look for", "discover", "where is", "show me", "find in codebase", "search codebase", "find in code"
- **Understanding**: "how does this work", "how is X implemented", "where is Y handled", "explain the content about"
- **Similarity**: "find similar", "similar to", "like this", "related to", "find other implementations"
- **Patterns**: "discover patterns", "identify instances", "all occurrences of"
- **Cross-Reference**: "where else", "find related", "show all references", "used by"
- **Documentation/Config**: "find documentation", "search documentation", "find config", "search config", "locate guide", "deployment documentation"

**Total**: ~52 keywords + 14 intent patterns (see `.claude/skills/skill-rules.json` for complete list)

**ABSOLUTE PROHIBITION**:
- ❌ NEVER use Grep/Glob as first attempt for functionality/content searches
- ❌ NEVER search the project without trying semantic-search first
- ❌ NEVER run bash scripts directly - activate skill and let it orchestrate

**MANDATORY Workflow**:
1. **STOP** - Do NOT use Grep/Glob/Read for functionality searches
2. **INVOKE**: Activate semantic-search skill FIRST
3. **SKILL SPAWNS AGENT**:
   - Reader agent for searches (90% of cases - search, find-similar, list-projects)
   - Indexer agent for indexing (10% of cases - index, status)
4. **AGENT EXECUTES**: Bash scripts run in agent's separate token budget
5. **AGENT RETURNS**: Interpreted results in natural language (not raw JSON)
6. **TOKEN SAVINGS**: Agent context separate from yours = 2-3x longer conversations
7. **ONLY IF SKILL FAILS**: Then fallback to Grep/Glob

### Token Cost Examples (WHY This Saves Tokens)

#### ❌ BAD: Traditional Grep Exploration (~8,000 tokens wasted)

**User**: "Find where authentication is handled"

**My Wrong Approach**:
```
1. Grep for "auth" → 200 matches → Read 5 files → Wrong code
2. Grep for "login" → 150 matches → Read 7 files → Still wrong
3. Grep for "authenticate" → 80 matches → Read 4 files → Getting closer
4. Grep for "session" → 300 matches → Read 10 files → Found it!

Total: 26 file reads, 4 Grep searches, 5-10 minutes
Token cost: ~8,000 tokens (file reads + failed attempts)
```

#### ✅ GOOD: Semantic Search (~400 tokens saved)

**User**: "Find where authentication is handled"

**My Correct Approach**:
```
1. Invoke semantic-search skill
2. Query: "user authentication and credential verification"
3. Get ranked results with exact file:line locations
4. Read 1-2 most relevant files → Found it!

Total: 1 semantic search, 2 file reads, 30 seconds
Token cost: ~600 tokens (search overhead + targeted reads)
SAVINGS: 7,400 tokens (92% reduction)
```

### Direct Tool Use vs Semantic Search

**Use semantic-search Skill for** (TOKEN SAVINGS):
- Finding content by describing WHAT it does (not exact keywords)
- Searching for "authentication logic" (could be named anything)
- Discovering patterns like "retry mechanisms" across project
- Finding similar implementations or documentation
- Understanding unfamiliar projects
- Cross-language/format searches (same concept, different syntax)
- **ANY exploratory task where you'd try multiple Grep searches**

**Use Grep ONLY for** (Known Targets):
- Exact string matching (e.g., `"import React"`)
- Known variable/function names (e.g., `"getUserById"`)
- Regex patterns (e.g., `"function.*export"`)
- File content search with known keywords
- **When you KNOW exactly what string to match**

**Use Glob ONLY for** (File Navigation):
- Finding files by name pattern (e.g., `"**/*.test.js"`)
- Locating configuration files (e.g., `"**/config.yml"`)
- File system navigation (e.g., `"src/components/**/*.tsx"`)

**Use Read ONLY for** (Known Files):
- Reading specific known files
- Examining files after semantic-search narrows results

### Example Violations to AVOID

❌ **WRONG #1** (~8,000 tokens wasted): User asks "how does authentication work?"
   → I run 20 Grep searches: `"login"`, `"auth"`, `"authenticate"`, `"verify"`
   → I read 26 files trying to find the right code
   → VIOLATION: Wasted 8,000 tokens on exploration instead of 400 tokens with semantic-search

❌ **WRONG #2** (Tool misuse): User asks "find the orchestrator pattern"
   → I run: `~/.claude/skills/semantic-search/scripts/search --query "..."`
   → VIOLATION: Ran bash scripts directly - skill should orchestrate this

❌ **WRONG #3** (Skipped hierarchy): I need to find error handling code
   → I use Grep without trying semantic-search first
   → VIOLATION: Didn't follow search hierarchy

✅ **CORRECT** (~400 tokens, saved 7,600): User asks "how does authentication work?"
   → I activate semantic-search skill
   → Skill executes: `scripts/search --query "user authentication logic" --k 10`
   → Get ranked results with exact locations
   → Read 2 most relevant files
   → Deliver answer
   → **Token savings: 95%**

✅ **ALSO CORRECT** (Proper fallback): I need to find authentication code
   → I activate semantic-search skill first
   → If index missing or search fails, THEN use Grep/Glob
   → Always try semantic-search before manual exploration

### Self-Check Before Acting

**Before searching/finding ANYTHING in this project, ask yourself**:
1. Did I try semantic-search skill? → NO? STOP and use skill first
2. Did the skill fail? → NO? Then don't do it yourself
3. Am I about to run Grep/Glob/bash? → YES? STOP and use skill first
4. Do I need to search/find/locate anything? → YES? Use semantic-search skill first

### Prerequisites

**Required**:
- Global installation: `~/.local/share/claude-context-local` (macOS/Linux) or `%LOCALAPPDATA%\claude-context-local` (Windows)
- Index created using `scripts/index` command

**If index missing**:
- Use `scripts/index /path/to/project --full` to create index
- Or inform user to create index first
- Fallback to Grep/Glob for keyword-based search

### Usage Examples

**Create/Update Index**:
```bash
~/.claude/skills/semantic-search/scripts/index /path/to/project --full
```

**List Indexed Projects**:
```bash
~/.claude/skills/semantic-search/scripts/list-projects
```

**Check Index Status**:
```bash
~/.claude/skills/semantic-search/scripts/status --project /path/to/project
```

**Basic Search**:
```bash
~/.claude/skills/semantic-search/scripts/search --query "user authentication logic" --k 10 --project /path/to/project
```

**Find Similar Content**:
```bash
# After getting chunk_id from search results
~/.claude/skills/semantic-search/scripts/find-similar --chunk-id "src/auth.py:45-67:function:authenticate" --k 5 --project /path/to/project
```

### Performance Guidelines

- **Default k=5**: Fast, usually sufficient
- **k=10-20**: Thorough search, moderate speed
- **k>50**: Slow, use only when comprehensive coverage needed
- **Index on SSD**: 5-10x faster than HDD

### When NOT to Use

**Do NOT use semantic search when**:
- You know the exact file name (use Read)
- You know the exact function/variable name (use Grep)
- You want file patterns (use Glob)
- Index doesn't exist and you need immediate results (use Grep/Glob)
- Searching for exact strings like import statements (use Grep)

---

## Available Skills

- **multi-agent-researcher**: Orchestrates 2-4 parallel researchers for comprehensive topic investigation, then synthesizes findings via mandatory report-writer agent delegation (architectural constraint: orchestrator lacks Write tool when skill active)
- **spec-workflow-orchestrator**: Orchestrates 3 sequential planning agents for development-ready specifications
- **semantic-search**: Semantic search using natural language queries to find any text content by meaning (code, documentation, markdown, configs). Uses 2-agent architecture (semantic-search-reader for searches, semantic-search-indexer for index management). Orchestrates claude-context-local via bash scripts. Saves 5,000-10,000 tokens vs traditional Grep exploration.

## Available Agents

### Research Agents:
- **researcher**: Web research agent. Tools: WebSearch, Write, Read. DO NOT invoke directly, use via skill
- **report-writer**: Synthesis agent. Tools: Read, Glob, Write.

### Planning Agents:
- **spec-analyst**: Requirements gathering agent. Tools: Read, Write, Glob, Grep, WebFetch, TodoWrite. DO NOT invoke directly, use via skill
- **spec-architect**: System design agent. Tools: Read, Write, Glob, Grep, WebFetch, TodoWrite, mcp__sequential-thinking__sequentialthinking. DO NOT invoke directly, use via skill
- **spec-planner**: Task breakdown agent. Tools: Read, Write, Glob, Grep, TodoWrite, mcp__sequential-thinking__sequentialthinking. DO NOT invoke directly, use via skill

### Semantic-Search Agents:
- **semantic-search-reader**: Executes semantic content search operations (search, find-similar, list-projects). Searches across all text content (code, documentation, markdown, configs). Tools: Bash, Read, Grep, Glob. DO NOT invoke directly, use via skill
- **semantic-search-indexer**: Executes semantic index management operations (index, status). Creates and updates semantic content indices for all text content. Tools: Bash, Read, Grep, Glob. DO NOT invoke directly, use via skill

## Available Slash Commands

Project-specific commands for common workflows:

- **`/project-status`**: Show current project implementation status (reads docs/status/, logs/, PROJECT_STRUCTURE.md)
- **`/plan-feature`**: Plan a new feature using spec-workflow-orchestrator skill (interactive feature specification)
- **`/research-topic`**: Research a topic using multi-agent-researcher skill (spawns 2-4 parallel researchers)
- **`/verify-structure`**: Verify project structure aligns with official Claude Code standards (runs structural validation)

**Usage**: Type `/command-name` in chat. Commands expand to prompts that activate relevant skills/agents.

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

---

## Hooks System

This project uses **5 hooks** for workflow automation. Hooks run automatically - users don't interact with them directly.

### User-Facing Hooks:
- **user-prompt-submit.py** (777 lines): Universal skill activation engine. Detects trigger keywords for all 3 skills, handles compound request detection (research + planning), applies negation patterns, injects enforcement reminders. Achieves 95% reliability (vs 70% with instructions only).
- **session-start.py**: Auto-setup, session logging initialization, research session restoration, skill crash recovery.

### Internal Tracking Hooks:
- **post-tool-use-track-research.py**: Research workflow phase tracking, quality gate validation (85% threshold), session logging, skill invocation tracking.
- **stop.py**: Skill completion detection, duration tracking, end-of-turn validation.
- **session-end.py**: Cleanup on session termination, finalize session state, close log files.

### How Hooks Work:
1. **user-prompt-submit** runs first - analyzes user prompt, detects skills, injects reminders
2. **post-tool-use** tracks each tool call during skill execution
3. **stop** detects when skill completes
4. **session-start/end** handle session lifecycle

### Debugging Hooks:
```bash
# Enable compound detection debug mode
export COMPOUND_DETECTION_DEBUG=true

# Check hook execution logs
tail -f logs/session_YYYYMMDD_HHMMSS_transcript.txt
```

**Note**: Hooks are configured in `.claude/settings.json`. Trigger rules defined in `.claude/skills/skill-rules.json`.

---

## MCP Servers

### claude-context-local
**Purpose**: Semantic search backend for the semantic-search skill. Enables natural language queries across all project content (code, documentation, markdown, configs).

**Technology**:
- FAISS IndexFlatIP (inner product similarity)
- google/embeddinggemma-300m embeddings (768 dimensions)
- Supports ~10,000 files per index, ~4,686 chunks for this project

**Installation**:
```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash

# Windows
# Use Windows installer from repository
```

**Location**:
- macOS/Linux: `~/.local/share/claude-context-local`
- Windows: `%LOCALAPPDATA%\claude-context-local`

**Used by**: semantic-search skill orchestrates claude-context-local via bash scripts in `.claude/skills/semantic-search/scripts/`

**Index Management**:
```bash
# Create/update index
~/.claude/skills/semantic-search/scripts/index /path/to/project --full

# Check status
~/.claude/skills/semantic-search/scripts/status --project /path/to/project

# List indexed projects
~/.claude/skills/semantic-search/scripts/list-projects
```

**Note**: This is the ONLY external dependency. All other features use built-in Claude Code capabilities.

---

## Commit Standards

When committing research work:
- Separate commits for: infrastructure, individual research notes, synthesis reports
- Include key statistics in commit messages
- Tag with source counts and confidence levels
- Co-author attribution to Claude

---

**REMEMBER**: You built the orchestrator - USE IT! Don't play all the instruments yourself when you have an orchestra.
