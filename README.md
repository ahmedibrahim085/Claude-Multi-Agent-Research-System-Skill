# Claude Code Multi-Agent Research Skill

**A Claude Code Skill** that orchestrates multi-agent research workflows with architectural enforcement, comprehensive session logging, and agent tracking.

Inspired by [Anthropic's claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent), adapted for Claude Code's skill system with workflow patterns from DevFlow, Claude-Flow, and TDD-Guard.

---

## What This Is

A **Claude Code Skill** that provides multi-agent research orchestration with:

### Core Workflow
- **Decomposes** complex research questions into 2-4 focused subtopics
- **Spawns** specialized researcher agents in parallel (not sequential)
- **Enforces** proper synthesis workflow via architectural constraints (~95% reliability)
- **Validates** quality gates to ensure workflow compliance

### Logging & Tracking
- **Session logging** to `transcript.txt` (human-readable) and `tool_calls.jsonl` (structured)
- **Agent identification** via heuristic detection (file paths + tool usage patterns)
- **Tool call tracking** via PostToolUse hooks
- **Session restoration** for interrupted research workflows

### Configuration & Setup
- **Automatic first-time setup** via SessionStart hook
- **JSON configuration** with environment variable overrides
- **Interactive setup.py** for advanced customization

---

## Inspiration & Credits

This project adapts the multi-agent research pattern for Claude Code's skill system, combining patterns from multiple production-proven projects:

### Primary Inspiration
- **[claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent)** by Anthropic PBC
  - Multi-agent research orchestration concept
  - Decomposition → Research → Synthesis workflow
  - Session logging patterns
  - License: Apache-2.0

### Workflow Patterns
- **[DevFlow](https://github.com/mathewtaylor/devflow)** by Mathew Taylor
  - Architectural enforcement via `allowed-tools` constraint
  - State tracking with `state.json`
  - Quality gates for phase validation
  - License: MIT

- **[Claude-Flow](https://github.com/ruvnet/claude-flow)** by ruvnet
  - Session persistence patterns
  - Research session restoration
  - License: Apache-2.0

- **[TDD-Guard](https://github.com/nizos/tdd-guard)** by nizos
  - Agent tracking via tool usage patterns
  - Multi-context workflow enforcement
  - License: MIT

- **[claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase)** by diet103
  - Skill auto-activation patterns
  - `skill-rules.json` configuration
  - License: MIT

All projects are MIT or Apache-2.0 licensed and used in compliance with their terms.

---

## Key Differences from Reference Implementation

| Feature | Reference (Python SDK) | This Project (Claude Code) |
|---------|------------------------|----------------------------|
| **Platform** | Python Agent SDK (standalone) | **Claude Code Skill** (extension) |
| **Hooks** | Python SDK hooks (`HookMatcher`) | Shell-based hooks (Python scripts) |
| **Enforcement** | Behavioral (via prompts) | **Architectural** (via \`allowed-tools\` ~95% reliability) |
| **Logging** | SDK-managed with \`parent_tool_use_id\` | **Custom hooks with heuristic agent detection** |
| **Agent Identification** | SDK's \`parent_tool_use_id\` field | **File path + tool usage heuristics** |
| **Configuration** | Python code | **JSON config + environment variables** |
| **Deployment** | Standalone Python app | **Claude Code skill + hooks** |
| **Session Logs** | Nested directories | **Flat structure** (configurable) |
| **Path Configuration** | Hardcoded | **Fully configurable** via \`.claude/config.json\` |
| **Setup** | Manual installation | **Automatic first-time setup** |

---

## Why Use This vs Reference?

### Use Reference Implementation If:
- Building **standalone Python application**
- Need SDK's native hook system with \`parent_tool_use_id\`
- Want official Anthropic patterns without modification
- Deploying as independent service

### Use This Implementation If:
- Using **Claude Code as your primary environment**
- Need **workflow enforcement** (~95% reliability via architectural constraints)
- Require **audit logging** for compliance/debugging
- Want **configuration flexibility** (JSON + env vars)
- Prefer **flat log structure** for easier analysis
- Need **quality gates** to validate research workflow

---

## Installation

### Prerequisites
- Claude Code installed
- Python 3.8+
- Git

### Quick Start (Automatic Setup)

The system includes automatic first-time setup that runs when you start Claude Code:

1. **Clone repository**:
\`\`\`bash
git clone https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill.git
cd Claude-Multi-Agent-Research-System-Skill
\`\`\`

2. **Start Claude Code** in the project directory

The SessionStart hook will automatically:
- Create required directories (if missing)
- Initialize session logging
- Show setup status and any warnings

**Note**: Hooks are pre-configured in `.claude/settings.json` and work out-of-the-box. Do not duplicate hooks in `settings.local.json` to avoid duplicate hook executions.

### Advanced Setup (Optional Customization)

For custom paths or advanced configuration, run the interactive setup script:

\`\`\`bash
python3 setup.py           # Interactive setup with prompts
python3 setup.py --verify  # Check setup without changes
python3 setup.py --repair  # Auto-fix issues
\`\`\`

The setup script allows you to:
- Customize directory paths (research notes, reports, logs)
- Configure max parallel researchers
- Verify Python version and hooks
- Check for missing files or directories

### Manual Configuration

If you want to customize hooks or permissions:

1. **(Optional) Create local settings override**:
\`\`\`bash
cp .claude/settings.template.json .claude/settings.local.json
# Edit .claude/settings.local.json to customize
\`\`\`

   **⚠️ Important**: If you create `settings.local.json`, **remove the `hooks` section** from it. Hooks are already configured in `settings.json` and duplicating them will cause duplicate hook executions. Only add custom permissions or other user-specific settings to `settings.local.json`.

2. **Customize paths in \`.claude/config.json\`**:
\`\`\`json
{
  "paths": {
    "research_notes": "files/research_notes",
    "reports": "files/reports",
    "logs": "logs"
  }
}
\`\`\`

3. **(Optional) Use environment variables**:
\`\`\`bash
export RESEARCH_NOTES_DIR=/custom/path
export REPORTS_DIR=/custom/reports
export LOGS_DIR=/custom/logs
\`\`\`

4. **Restart Claude Code** to load hooks

### Verify Installation

Test with a research query:
\`\`\`
research quantum computing fundamentals
\`\`\`

Expected output:
\`\`\`
📝 Session logs initialized: logs/session_20251117_143022_{transcript.txt,tool_calls.jsonl}

[Orchestrator decomposes into 3 subtopics]
[Spawns 3 researcher agents in parallel]
[Waits for completion]
[Spawns report-writer agent for synthesis]
[Delivers comprehensive report]
\`\`\`

Check outputs:
- \`files/research_notes/\` - 3 research note files
- \`files/reports/\` - 1 synthesis report
- \`logs/\` - Session transcript and tool calls log

---

## Configuration

### File: \`.claude/config.json\`

\`\`\`json
{
  "paths": {
    "research_notes": "files/research_notes",
    "reports": "files/reports",
    "logs": "logs",
    "state": ".claude/state"
  },
  "logging": {
    "enabled": true,
    "format": "flat",
    "log_tool_calls": true
  },
  "research": {
    "max_parallel_researchers": 4,
    "require_synthesis_delegation": true,
    "quality_gates_enabled": true
  }
}
\`\`\`

### Environment Variable Overrides

\`\`\`bash
export RESEARCH_NOTES_DIR=/custom/path
export REPORTS_DIR=/custom/reports
export LOGS_DIR=/var/log/research
export MAX_PARALLEL_RESEARCHERS=6
export LOGGING_ENABLED=true
\`\`\`

Priority: \`Environment Variables\` > \`config.json\` > \`Defaults\`

---

## Session Logs

### Log Format: Flat Structure

\`\`\`
logs/
├── session_20251117_143022_transcript.txt
├── session_20251117_143022_tool_calls.jsonl
├── session_20251117_150113_transcript.txt
└── session_20251117_150113_tool_calls.jsonl
\`\`\`

### transcript.txt Example

\`\`\`
[14:30:22] ORCHESTRATOR → Task ✅
  Input: {"subagent_type": "researcher", ...}
  Output: Success (2.4 KB)
  Duration: 1250ms

[14:31:05] RESEARCHER-1 → WebSearch ✅
  Input: {"query": "agentic RAG architectures"}
  Output: Success (15.2 KB)
  Duration: 450ms
\`\`\`

---

## License

MIT License - See LICENSE file

---

## Acknowledgments

Inspired by [claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent) by Anthropic.

Key adaptations for Claude Code environment:
- Shell-based hooks instead of SDK hooks
- Architectural enforcement via \`allowed-tools\`
- Flat log structure for easier analysis
- JSON-based configuration system
- Environment variable overrides
