# Configuration Guide
## Claude Multi-Agent Research System

This guide documents all skills, agents, slash commands, file organization conventions, and custom configuration files used in this project.

---

## Available Skills

- **multi-agent-researcher**: Orchestrates 2-4 parallel researchers for comprehensive topic investigation, then synthesizes findings via mandatory report-writer agent delegation (architectural constraint: orchestrator lacks Write tool when skill active)
- **spec-workflow-orchestrator**: Orchestrates 3 sequential planning agents for development-ready specifications
- **semantic-search**: Semantic search using natural language queries to find any text content by meaning (code, documentation, markdown, configs). Uses 2-agent architecture (semantic-search-reader for searches, semantic-search-indexer for index management). Orchestrates claude-context-local via bash scripts. Saves 5,000-10,000 tokens vs traditional Grep exploration.

---

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

---

## Available Slash Commands

Project-specific commands for common workflows:

- **`/project-status`**: Show current project implementation status (reads docs/status/, logs/, PROJECT_STRUCTURE.md)
- **`/plan-feature`**: Plan a new feature using spec-workflow-orchestrator skill (interactive feature specification)
- **`/research-topic`**: Research a topic using multi-agent-researcher skill (spawns 2-4 parallel researchers)
- **`/verify-structure`**: Verify project structure aligns with official Claude Code standards (runs structural validation)

**Usage**: Type `/command-name` in chat. Commands expand to prompts that activate relevant skills/agents.

---

## File Organization

- `files/research_notes/`: Individual researcher outputs (one file per subtopic)
- `files/reports/`: Comprehensive synthesis reports (timestamped)
- Name format: `topic-slug_YYYYMMDD-HHMMSS.md`
- `docs/planning/`: Active planning documents (requirements, architecture, tasks)
- `docs/adrs/`: Architecture Decision Records (numbered format)

---

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

## Commit Standards

When committing research work:
- Separate commits for: infrastructure, individual research notes, synthesis reports
- Include key statistics in commit messages
- Tag with source counts and confidence levels
- Co-author attribution to Claude
