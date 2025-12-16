# Claude Code Multi-Agent Research Skill

**Orchestrated multi-agent research with architectural enforcement, parallel execution, and comprehensive audit trails.**

[![Version](https://img.shields.io/badge/version-2.4.1-blue.svg)](https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎉 v2.4.0: Production-Grade Auto-Reindex + Tracing

A **tri-skill platform** with smart routing, auto-indexing, and compound request detection:

| Skill | Purpose | Agents |
|-------|---------|--------|
| **multi-agent-researcher** | Comprehensive topic investigation | researcher, report-writer |
| **spec-workflow-orchestrator** | Planning from ideation to dev-ready specs | spec-analyst, spec-architect, spec-planner |
| **semantic-search** | Natural language content search (code, docs, configs) | semantic-search-reader, semantic-search-indexer |

**Key Features**:
- **Auto-Reindex on File Changes** - Triggers on Write/Edit with 5-min cooldown (IndexFlatIP auto-fallback (full reindex only))
- **Auto-Reindex on Session Start** - Smart change detection when Claude Code starts
- **Comprehensive Decision Tracing** - Full visibility into reindex decisions (skip reasons, timing, errors)
- **Smart Compound Detection** - When prompts trigger multiple skills, asks for clarification
- **200+ Trigger Keywords** - Automatic skill routing via hook (3 skills)
- **Quality Gates** - 85% threshold with max 3 iterations
- **Token Savings** - Semantic search saves 5,000-10,000 tokens per task (~90% reduction)

**Quick Examples**:
```
research quantum computing fundamentals     → multi-agent-researcher
plan a task management PWA with offline     → spec-workflow-orchestrator
find authentication logic in the codebase   → semantic-search
research auth methods and build login page  → asks which skill to use
```

See [Planning Workflow](#planning-workflow-new-in-v220) and [CHANGELOG.md](CHANGELOG.md) for details.

---

## Table of Contents

- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Your First Research Query](#your-first-research-query)
- [Why This Approach?](#why-this-approach)
  - [vs. Direct Tools (WebSearch/WebFetch)](#vs-direct-tools-websearchwebfetch)
  - [vs. MCP Servers](#vs-mcp-servers)
  - [vs. Sequential Research](#vs-sequential-research)
  - [Architectural Benefits](#architectural-benefits)
  - [When NOT to Use](#when-not-to-use)
- [How It Works](#how-it-works)
  - [Phase 1: Decomposition](#phase-1-decomposition)
  - [Phase 2: Parallel Research](#phase-2-parallel-research)
  - [Phase 3: Synthesis](#phase-3-synthesis)
  - [Phase 4: Delivery](#phase-4-delivery)
- [Planning Workflow (New in v2.2.0)](#planning-workflow-new-in-v220)
- [Testing](#testing)
- [Configuration](#configuration)
  - [File Structure](#file-structure)
  - [File & Directory Reference](#file--directory-reference)
  - [Environment Variables](#environment-variables)
  - [Advanced Setup](#advanced-setup)
- [Architecture Deep Dive](#architecture-deep-dive)
  - [Comparison to Reference SDK](#comparison-to-reference-sdk)
  - [Enforcement Mechanisms](#enforcement-mechanisms)
  - [Hooks Architecture](#hooks-architecture)
  - [Session Logging](#session-logging)
- [Inspiration & Credits](#inspiration--credits)
- [Author & Acknowledgments](#author--acknowledgments)
- [License](#license)
- [References](#references)

---

## Quick Start

### Prerequisites

**Required for All Features**:
- **Claude Code** installed ([Pro, Max, Team, or Enterprise tier](https://www.anthropic.com/news/skills))<sup>[[1]](#ref-1)</sup>
- **Python 3.8+** with `python3` command available in PATH
  - Verify: `python3 --version` (should show 3.8 or higher)
- **Git** installed and available in PATH
- **Bash shell** (for hooks and scripts)
  - macOS/Linux: built-in
  - Windows: Use WSL2 (Windows Subsystem for Linux)

**Additional for Semantic-Search Skill** (optional):
- **~1.5GB disk space** for embedding model download
  - Model: `google/embeddinggemma-300m` (768 dimensions)
  - Downloads automatically on first use (10-30 minutes)
  - Cached at: `~/.claude_code_search/models/`
  - One-time download, reused across all projects

### Platform Support

✅ **Fully Supported**:
- **macOS** (Intel + Apple Silicon)
  - **Apple Silicon**: Tested on M1/M2/M3 chips - semantic search works perfectly with MPS (Metal Performance Shaders) GPU acceleration
  - Model loads on `mps:0` device for optimal performance
- **Linux** (x86_64, ARM64)
- **Windows** (via WSL)

**Index Type**: Uses IndexFlatIP (FAISS) - simple, reliable, cross-platform compatible

### Installation

**Step 1: Clone the repository**
```bash
git clone https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill.git
cd Claude-Multi-Agent-Research-System-Skill
```

**Step 2: (Optional) Enable semantic-search skill**

> **Note:** The multi-agent-researcher skill works immediately without this step. Only install if you want semantic code search.

The semantic-search skill imports Python modules from claude-context-local for:
- Merkle tree change detection (smart reindexing)
- Multi-language code chunking (15+ languages)
- Embedding generation (sentence-transformers, FAISS)

```bash
# Clone Python library to standard location (30 seconds)
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local
```

**That's it!** No virtual environment, no pip install, no `uv` needed. The skill imports modules directly via `sys.path.insert()`.

**First-time usage**: The embedding model (~1.2GB) downloads automatically on first semantic-search (10-30 minutes). Subsequent uses are instant.

**License note:** claude-context-local is GPL-3.0. Our project imports it via PYTHONPATH (dynamic linking), which preserves our Apache 2.0 license. See `docs/architecture/MCP-DEPENDENCY-STRATEGY.md` for details.

**Step 3: Start Claude Code**
```bash
claude
```

The SessionStart hook will automatically:
- **Auto-reindex semantic search** (smart change detection, 60-min cooldown)
- Create required directories (`files/research_notes/`, `files/reports/`, `logs/`)
- Initialize session logging
- Check prerequisites and enable conditional enforcement
- Display setup status

**Note**: Hooks are pre-configured in `.claude/settings.json` and work out-of-the-box. **Do not duplicate hooks in `settings.local.json`** to avoid duplicate hook executions.

### Your First Research Query

Try this example:
```
research quantum computing fundamentals
```

**Expected output**:
```
📝 Session logs initialized: logs/session_YYYYMMDD_HHMMSS_{transcript.txt,tool_calls.jsonl,state.json}

# Research Complete: Quantum Computing Fundamentals

Comprehensive research completed with 3 specialized researchers.

## Key Findings
1. [Finding from researcher 1]
2. [Finding from researcher 2]
3. [Finding from researcher 3]

## Files Generated
**Research Notes**: `files/research_notes/`
- quantum-computing-fundamentals-basics_YYYYMMDD-HHMMSS.md
- quantum-computing-fundamentals-hardware_YYYYMMDD-HHMMSS.md
- quantum-computing-fundamentals-algorithms_YYYYMMDD-HHMMSS.md

**Final Report**: `files/reports/quantum-computing-fundamentals_YYYYMMDD-HHMMSS.md`
```

---

## Why This Approach?

### vs. Direct Tools (WebSearch/WebFetch)

**Direct approach**:
```
User: "Tell me about quantum computing"
→ Claude does 1-2 WebSearch calls
→ Returns summary from top results
→ Limited depth, single perspective
```

**This orchestrated approach**:
```
User: "Research quantum computing"
→ Decomposes into 3-4 subtopics (basics, hardware, algorithms, applications)
→ Spawns 3-4 researcher agents in parallel
→ Each agent conducts focused, multi-source research
→ Report-writer synthesizes comprehensive findings
→ Cross-referenced, authoritative sources
```

**When direct tools are sufficient**: Single factual questions ("What is X?"), quick documentation lookups, specific URL fetches.

### vs. MCP Servers

The **Model Context Protocol (MCP)**<sup>[[2]](#ref-2)</sup> is Anthropic's open standard for connecting AI systems to data sources through servers.

**MCP Approach** (agent as MCP server):
- Each agent is an **MCP server** providing tools
- Claude Code calls MCP tools to interact with agents
- ❌ **No enforced workflow** - Claude can skip decomposition or synthesis
- ❌ **No architectural constraints** - relies entirely on prompts
- ❌ **Agents don't coordinate** - just isolated tool calls
- ❌ **No guaranteed synthesis phase**

**This Orchestrated Approach**:
- Agents are **Task subprocesses**<sup>[[3]](#ref-3)</sup> with defined roles (researcher, report-writer)
- Orchestrator **enforces workflow phases** via `allowed-tools` constraint<sup>[[4]](#ref-4)</sup>
- ✅ **Architectural enforcement** (~95% reliability)
- ✅ **Parallel execution** - spawn all researchers simultaneously
- ✅ **Mandatory synthesis** - orchestrator physically cannot write reports (lacks Write tool)
- ✅ **Quality gates** - verify all phases complete before delivery

**Example**:
```
MCP Approach:
User: "research quantum computing"
→ Claude calls researcher-mcp-tool (maybe)
→ Claude writes synthesis itself (no delegation enforcement)
→ May skip decomposition or parallel execution
→ Workflow depends on prompt compliance

This Approach:
User: "research quantum computing"
→ Orchestrator MUST decompose (Phase 1)
→ Orchestrator MUST spawn researchers in parallel (Phase 2)
→ Orchestrator CANNOT write synthesis - lacks Write tool (architectural constraint)
→ Orchestrator MUST delegate to report-writer agent (Phase 3)
→ Workflow enforced by architecture, not prompts
```

### vs. Sequential Research

**Sequential Approach** (original SDK pattern<sup>[[5]](#ref-5)</sup>):
- Research subtopics one-by-one
- Total time: N × (research time per subtopic)
- Example: 3 subtopics × 10 min each = **30 minutes**

**Parallel Orchestration** (this project):
- Research all subtopics simultaneously (Claude Code supports up to 10 parallel tasks<sup>[[6]](#ref-6)</sup>)
- Total time: max(research times) + synthesis time
- Example: max(10, 12, 8 min) + 3 min = **15 minutes**
- **~30-50% faster** for typical 3-4 subtopic research<sup>[[7]](#ref-7)</sup>

**Additional benefits**:
- **Reliability**: If one researcher fails, others complete; orchestrator can retry failed subtopics
- **Isolation**: Independent researchers can't block each other
- **Scalability**: Performance scales with subtopic count

### Architectural Benefits

#### 1. Reliability Through Constraints

```yaml
# From SKILL.md frontmatter:
allowed-tools: Task, Read, Glob, TodoWrite
# Note: Write is deliberately excluded
```

- Orchestrator **physically cannot** bypass report-writer agent
- Prompts can be ignored; architecture cannot
- ~95% enforcement reliability (vs. ~20-50% for prompt-based approaches)<sup>[[4]](#ref-4)</sup>

#### 2. Audit Trail & Compliance

Every tool call is logged to:
- `transcript.txt` - human-readable session log
- `tool_calls.jsonl` - structured JSON for analysis

**Enables**:
- Verify workflow compliance after-the-fact
- Debug agent behavior
- Compliance requirements (audit who did what, when)

#### 3. Quality Gates

Before synthesis:
- ✅ Verify all research notes exist
- ✅ Detect violations (e.g., orchestrator writing reports)
- ✅ Fail-fast on incomplete research

#### 4. Scalability

- Parallel execution scales with subtopic count
- Independent researchers reduce single points of failure
- Synthesis happens once after all research completes

### When NOT to Use

This architecture is **overkill** for:

- ❌ Single factual questions ("What is the capital of France?")
- ❌ Quick lookups ("Latest version of Python?")
- ❌ Code-related tasks ("Debug this function", "Write a script")
- ❌ Decision evaluation ("Should I use React or Vue?")

**Use direct tools** (WebSearch, WebFetch) for these instead.

**Use this architecture when**:

- ✅ Multi-source research needed (2+ authoritative sources)
- ✅ Synthesis across perspectives required
- ✅ Comprehensive coverage important
- ✅ Audit trail needed for compliance
- ✅ Quality gates required

---

## How It Works

The orchestrated multi-agent workflow has four enforced phases:

### Phase 1: Decomposition

**Orchestrator**:
1. Analyzes user's research question
2. Breaks topic into 2-4 focused subtopics that are:
   - Mutually exclusive (minimal overlap)
   - Collectively exhaustive (cover whole topic)
   - Independently researchable

**Example**:
```
Query: "Research quantum computing"
→ Subtopics:
  1. Theoretical foundations (qubits, superposition, entanglement)
  2. Hardware implementations (superconducting, ion trap, topological)
  3. Algorithms & applications (Shor's, Grover's, VQE, QAOA)
```

### Phase 2: Parallel Research

**Orchestrator spawns all researchers simultaneously**:

```python
# Conceptual (actual implementation uses Task tool)
spawn_parallel([
    researcher(topic="Theoretical foundations", context="quantum computing"),
    researcher(topic="Hardware implementations", context="quantum computing"),
    researcher(topic="Algorithms & applications", context="quantum computing")
])
```

Each researcher:
- Conducts web research (WebSearch tool)
- Gathers authoritative sources
- Extracts key findings
- Saves results to `files/research_notes/{subtopic-slug}.md`

**Parallelism**: Claude Code supports up to 10 concurrent tasks<sup>[[6]](#ref-6)</sup>; excess tasks are queued.

### Phase 3: Synthesis

**⚠️ Architectural Enforcement Active**

The orchestrator **does not have Write tool access** (see `allowed-tools` in SKILL.md). This architectural constraint **physically prevents** the orchestrator from writing synthesis reports.

**Enforced workflow**:
1. Orchestrator verifies all research notes exist (Glob tool)
2. Orchestrator **MUST** spawn report-writer agent (Task tool)
3. Report-writer reads ALL research notes (Read tool)
4. Report-writer synthesizes findings into comprehensive report
5. Report-writer writes to `files/reports/{topic}_{timestamp}.md` (Write tool)

**Cannot be bypassed**: Attempting to write reports from orchestrator results in tool permission error.

### Phase 4: Delivery

Orchestrator:
1. Reads final report
2. Creates user-facing summary with:
   - Key findings (3-5 bullet points)
   - Research scope (subtopics investigated)
   - File paths (research notes + final report)
3. Delivers to user

---

## Planning Workflow (New in v2.2.0)

The **spec-workflow-orchestrator** skill provides comprehensive project planning from ideation to development-ready specifications.

### Trigger Keywords (90+)

- "plan", "design", "architect", "build", "create", "implement"
- "specs", "requirements", "features", "PRD", "ADR"
- "what should we build", "how should we structure"

### Workflow

```
User: "build a task tracker app"
    ↓
1. ANALYZE → spec-analyst gathers requirements
    → User stories with acceptance criteria
    → Functional/non-functional requirements
    ↓
2. ARCHITECT → spec-architect designs system
    → Component architecture
    → Technology recommendations
    → Architecture Decision Records (ADRs)
    ↓
3. PLAN → spec-planner breaks down tasks
    → Implementation tasks with dependencies
    → Complexity estimates
    → Suggested implementation order
    ↓
4. VALIDATE → Quality gate (85% threshold)
```

### Features

- **Per-Project Structure**: `docs/projects/{project-slug}/`
- **Interactive Decision**: Detects existing projects → New/Refine/Archive options
- **Archive System**: Timestamped backups with integrity verification
- **Quality Gates**: 85% threshold with up to 3 iterations
- **State Management**: JSON-based workflow persistence

### Outputs

| File | Content |
|------|---------|
| `docs/projects/{slug}/requirements.md` | User stories, acceptance criteria |
| `docs/projects/{slug}/architecture.md` | System design, components |
| `docs/projects/{slug}/tasks.md` | Implementation tasks with dependencies |
| `docs/adrs/*.md` | Architecture Decision Records |

### Production Utilities

```bash
# Archive a project
.claude/utils/archive_project.sh task-tracker-pwa

# List archives
.claude/utils/list_archives.sh task-tracker-pwa

# Restore from archive
.claude/utils/restore_archive.sh task-tracker-pwa 20251120-103602

# Manage workflow state
.claude/utils/workflow_state.sh set "task-tracker-pwa" "refinement" "Add offline"
.claude/utils/workflow_state.sh get "mode"
.claude/utils/workflow_state.sh show
.claude/utils/workflow_state.sh clear
```

See [PRODUCTION_READY_SUMMARY.md](PRODUCTION_READY_SUMMARY.md) for detailed implementation status.

---

## Testing

The project includes a comprehensive test suite following a 3-layer architecture for AI agent systems:

| Layer | Tests | Purpose |
|-------|-------|---------|
| Infrastructure | 158 | Hook behavior (148), utilities (10) |
| Behavior | 22 | Agent structure, file validation |
| Integration | Manual | Deliverable format, ADR compliance (require skill output) |
| Quality | Manual | Human evaluation of content quality |

### Running Tests

```bash
# Layer 1: Infrastructure tests (tests/common/)
python3 tests/common/e2e_hook_test.py
./tests/common/test_production_implementation.sh

# Layer 2: Structural validation
./tests/common/test_agent_structure.sh
./tests/spec-workflow/test_deliverable_structure.sh integration-test-hello-world
python3 tests/spec-workflow/test_adr_format.py integration-test-hello-world

# Integration: API-based E2E (requires ANTHROPIC_API_KEY)
python3 tests/spec-workflow/test_skill_integration.py --dry-run   # Without API
python3 tests/spec-workflow/test_skill_integration.py --quick     # With API
```

### Test Architecture

See [tests/TEST_ARCHITECTURE.md](tests/TEST_ARCHITECTURE.md) for detailed documentation on:
- Why AI agents require different testing approaches
- What can vs cannot be automated
- Manual test evidence documentation

**Total: 180 automated tests** (run without user input)

---

## Configuration

### File Structure

```
.
├── .claude/
│   ├── agents/                    # Agent definitions
│   │   ├── researcher.md          # Research skill
│   │   ├── report-writer.md       # Research skill
│   │   ├── spec-analyst.md        # Planning skill (v2.2.0)
│   │   ├── spec-architect.md      # Planning skill (v2.2.0)
│   │   └── spec-planner.md        # Planning skill (v2.2.0)
│   ├── commands/                  # Slash commands (v2.2.0)
│   │   ├── plan-feature.md
│   │   ├── project-status.md
│   │   ├── research-topic.md
│   │   └── verify-structure.md
│   ├── hooks/                     # Python hook scripts
│   │   ├── user-prompt-submit.py  # Universal skill activation (v2.2.0)
│   │   ├── session-start.py
│   │   └── post-tool-use-track-research.py
│   ├── skills/
│   │   ├── multi-agent-researcher/
│   │   │   └── SKILL.md
│   │   ├── spec-workflow-orchestrator/  # (v2.2.0)
│   │   │   └── SKILL.md
│   │   └── skill-rules.json       # Trigger configuration
│   ├── utils/                     # Production utilities (v2.2.0)
│   │   ├── archive_project.sh
│   │   ├── restore_archive.sh
│   │   ├── list_archives.sh
│   │   ├── workflow_state.sh
│   │   └── detect_next_version.sh
│   ├── settings.json              # Hooks configuration (committed)
│   ├── settings.local.json        # User overrides (gitignored)
│   └── config.json                # Path & research configuration
├── files/
│   ├── research_notes/            # Individual researcher outputs
│   └── reports/                   # Synthesis reports
├── docs/
│   ├── projects/                  # Planning outputs (v2.2.0)
│   └── adrs/                      # Architecture Decision Records (v2.2.0)
├── logs/                          # Session logs + state
│   ├── session_*_{transcript,tool_calls,state}.*
│   └── state/current.json         # Active skill pointer
└── setup.py                       # Interactive setup script
```

### File & Directory Reference

Complete reference of all files and their roles:

| File/Directory | Purpose | Type | User Action |
|----------------|---------|------|-------------|
| **Core Skill Files** | | | |
| `.claude/skills/multi-agent-researcher/SKILL.md` | Skill definition with `allowed-tools` constraint that enforces workflow | Skill Definition | View/Customize |
| `.claude/skills/spec-workflow-orchestrator/SKILL.md` | Planning orchestrator (v2.2.0) | Skill Definition | View/Customize |
| `.claude/agents/researcher.md` | Instructions for researcher agents (web research, note-taking) | Agent Definition | View/Customize |
| `.claude/agents/report-writer.md` | Instructions for report-writer agent (synthesis, cross-referencing) | Agent Definition | View/Customize |
| `.claude/agents/spec-analyst.md` | Requirements gathering (v2.2.0) | Agent Definition | View/Customize |
| `.claude/agents/spec-architect.md` | System design (v2.2.0) | Agent Definition | View/Customize |
| `.claude/agents/spec-planner.md` | Task breakdown (v2.2.0) | Agent Definition | View/Customize |
| **Hook System (Enforcement & Tracking)** | | | |
| `.claude/hooks/user-prompt-submit.py` | Universal skill activation (v2.2.0) | Hook Script | Advanced Only |
| `.claude/hooks/post-tool-use-track-research.py` | Logs every tool call, identifies agents, enforces quality gates | Hook Script | Advanced Only |
| `.claude/hooks/session-start.py` | Auto-creates directories, restores sessions, displays status | Hook Script | Advanced Only |
| `.claude/settings.json` | Registers hooks with Claude Code (committed to repo) | Settings | Caution |
| `.claude/settings.local.json` | User-specific overrides (gitignored, optional) | Settings | Optional |
| **Configuration & State** | | | |
| `.claude/config.json` | Paths, logging settings, research parameters | Config | Customize |
| `logs/state/current.json` | Active skill pointer for dual-skill routing (~100 bytes) | State | Auto-Generated |
| `logs/session_*_state.json` | Per-session history: skill invocations (both skills) | State | Auto-Generated |
| `.claude/skills/skill-rules.json` | Trigger patterns for skill activation | Config | View |
| **Data Outputs** | | | |
| `files/research_notes/*.md` | Individual researcher findings (one file per subtopic) | Research Data | Auto-Generated |
| `files/reports/*.md` | Comprehensive synthesis reports (timestamped) | Final Reports | Auto-Generated |
| `docs/projects/{slug}/*.md` | Planning deliverables (v2.2.0) | Planning Data | Auto-Generated |
| `docs/adrs/*.md` | Architecture Decision Records (v2.2.0) | Planning Data | Auto-Generated |
| **Logs & Audit Trail** | | | |
| `logs/session_*_transcript.txt` | Human-readable session log with agent identification | Log | Auto-Generated |
| `logs/session_*_tool_calls.jsonl` | Structured JSON log for programmatic analysis | Log | Auto-Generated |
| `logs/session_*_state.json` | Session skill invocations and research sessions | Log | Auto-Generated |
| **Utilities** | | | |
| `setup.py` | Interactive configuration wizard for advanced customization | Setup Script | Run When Needed |
| `.claude/utils/*.sh` | Production utilities for planning (v2.2.0) | Scripts | Run When Needed |

**Key**:
- **View**: Read to understand how system works
- **Customize**: Safe to edit for your needs
- **Advanced Only**: Don't edit unless you understand hook system deeply
- **Caution**: Edit carefully; incorrect changes can break functionality
- **Auto-Generated**: Created/updated by system; don't edit manually
- **Optional**: Only create if you need user-specific overrides

### Default Paths

Configured in `.claude/config.json`:

```json
{
  "paths": {
    "research_notes": "files/research_notes",
    "reports": "files/reports",
    "logs": "logs",
    "state": "logs/state"
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
```

### Environment Variables

Override paths without editing config:

```bash
export RESEARCH_NOTES_DIR=/custom/path/notes
export REPORTS_DIR=/custom/path/reports
export LOGS_DIR=/custom/path/logs
```

Then restart Claude Code.

### Advanced Setup

For custom configuration:

```bash
python3 setup.py           # Interactive setup with prompts
python3 setup.py --verify  # Check setup without changes
python3 setup.py --repair  # Auto-fix issues
```

The setup script allows you to:
- Customize directory paths
- Configure max parallel researchers (1-10)
- Verify Python version and hooks
- Check for missing files or directories

**⚠️ Important**: If you create `settings.local.json`, **remove the `hooks` section** from it. Hooks are already configured in `settings.json` and duplicating them will cause duplicate hook executions.

---

## Architecture Deep Dive

### Architecture Decision Records (ADRs)

**ADR-001: Direct Script vs Agent for Auto-Reindex** ([Full ADR](docs/architecture/ADR-001-direct-script-vs-agent-for-auto-reindex.md) | [Quick Reference](docs/architecture/auto-reindex-design-quick-reference.md))

**Decision**: Use direct bash scripts for automatic reindex operations (session start, post-write hooks)

**Key Metrics**:
- **Performance**: 5x faster (2.7s vs 14.6s)
- **Cost**: $0 vs $144/year per 10 developers
- **Reliability**: Deterministic, works offline
- **Hook Safety**: 9s buffer vs risky timeout

**Agent Use**: Reserved for manual operations where intelligence and rich output add value (user explicitly invokes reindex, troubleshooting, diagnostics)

---

### Comparison to Reference SDK

This project adapts the multi-agent research pattern from [Anthropic's research-agent demo](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent)<sup>[[5]](#ref-5)</sup> for Claude Code's skill system.

| Feature | Reference (Python SDK) | This Project (Claude Code) |
|---------|------------------------|----------------------------|
| **Platform** | Python Agent SDK (standalone) | **Claude Code Skill** (integrated) |
| **Hooks** | Python SDK hooks (`HookMatcher`) | Shell-based hooks (Python scripts) |
| **Enforcement** | Behavioral (via prompts) | **Architectural** (via `allowed-tools` ~95% reliability)<sup>[[4]](#ref-4)</sup> |
| **Logging** | SDK-managed with `parent_tool_use_id` | **Custom hooks with heuristic agent detection** |
| **Agent Identification** | SDK's `parent_tool_use_id` field | **File path + tool usage heuristics** |
| **Configuration** | Python code | **JSON config + environment variables** |
| **Deployment** | Standalone Python app | **Claude Code skill + hooks** |
| **Session Logs** | Nested directories | **Flat structure** (configurable) |
| **Setup** | Manual installation | **Automatic first-time setup** |

**Use Reference Implementation If**:
- Building standalone Python application
- Need SDK's native hook system
- Want official Anthropic patterns without modification

**Use This Implementation If**:
- Using Claude Code as primary environment
- Need workflow enforcement via architecture
- Require audit logging for compliance
- Want configuration flexibility (JSON + env vars)

### Enforcement Mechanisms

#### 1. `allowed-tools` Constraint

From `.claude/skills/multi-agent-researcher/SKILL.md`:

```yaml
---
name: multi-agent-researcher
allowed-tools: Task, Read, Glob, TodoWrite
---
```

When this skill is active, Claude can **only** use the listed tools<sup>[[4]](#ref-4)</sup>. The Write tool is deliberately excluded, making it **architecturally impossible** for the orchestrator to write synthesis reports.

**Reliability**: ~95% (cannot be bypassed through prompt injection).

From `.claude/skills/spec-workflow-orchestrator/SKILL.md`:

```yaml
---
name: spec-workflow-orchestrator
allowed-tools: Task, Read, Glob, TodoWrite, Write, Edit
---
```

Spec skill **has Write access** - enforcement is via quality gates (85% threshold), not tool restriction. Orchestrator delegates to spec-analyst → spec-architect → spec-planner sequentially, validating each deliverable before proceeding.

#### 2. Quality Gates

**Research Skill** - Implemented in hooks:

```python
# Detect orchestrator bypassing report-writer
if synthesis_phase and tool == "Write" and agent == "orchestrator":
    violation = "Orchestrator attempted to write synthesis report"
    log_violation(violation)
```

**Spec Skill** - 85% threshold scoring (100 points total):

| Criteria | Points | Applies To |
|----------|--------|------------|
| Completeness | 25 | All deliverables |
| Technical Depth | 25 | Architecture, ADRs |
| Actionability | 25 | Tasks, requirements |
| Clarity | 25 | All deliverables |

Max 3 iterations per agent. Below threshold → feedback loop → retry.

#### 3. Session State Tracking

Tracks active skill and workflow progression for the **dual-skill platform**.

**Current State** (`logs/state/current.json` ~100 bytes):
- `currentSkill`: Which skill is active (multi-agent-researcher **or** spec-workflow-orchestrator)
- `currentResearch`: Active research session details (if research skill)

**Session History** (`logs/session_*_state.json`):
- `skillInvocations[]`: All skill activations this session (both skills)
- `researchSessions[]`: Completed research sessions

**Enables**:
- **Routing**: Hooks check `currentSkill` before activating another skill
- **Restoration**: Resume interrupted workflows (either skill)
- **Audit**: Track all skill usage across sessions

**Why Split Architecture?** Claude Code's Read tool has 25K token limit. A single persistent file would fail at ~359 skill invocations. Split keeps `current.json` tiny (~100 bytes) while session files are bounded per-session.

### Hooks Architecture

The hook system is the **foundation of enforcement and tracking**. Without hooks, this system wouldn't work—`allowed-tools` constraints prevent unauthorized actions, but hooks provide logging, quality gates, and session management.

#### How Hooks Work

Claude Code fires hooks at specific lifecycle events:
- **UserPromptSubmit**: Before processing user prompt (v2.2.0)
- **PostToolUse**: After every tool call (Read, Write, Task, WebSearch, etc.)
- **SessionStart**: When Claude Code session begins

Our hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-submit.py\""
      }]
    }],
    "PostToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-track-research.py\""
      }]
    }],
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.py\""
      }]
    }]
  }
}
```

#### UserPromptSubmit Hook (v2.2.0)

**Runs BEFORE every user prompt is processed** to enforce skill activation.

**Responsibilities**:
1. Detects research triggers (37+ keywords, 15 patterns)
2. Detects planning triggers (90+ keywords, 23 patterns)
3. Injects enforcement reminders into Claude's context

#### PostToolUse Hook (`post-tool-use-track-research.py`)

**Runs after EVERY tool call** to provide comprehensive tracking and enforcement.

**Responsibilities**:

1. **Agent Identification**
   ```python
   # Heuristics to identify which agent made the call
   if tool == "Task" and "subagent_type" in input:
       agent = "orchestrator"
   elif file_path.startswith("files/research_notes/"):
       agent = "researcher"
   elif file_path.startswith("files/reports/"):
       agent = "report-writer"
   ```

2. **Logging**
   - Appends to `transcript.txt` with human-readable format
   - Appends to `tool_calls.jsonl` with structured JSON
   - Includes: timestamp, agent, tool, input, output, duration

3. **Quality Gate Enforcement**
   ```python
   # Detect workflow violations
   if synthesis_phase and tool == "Write" and agent == "orchestrator":
       violation = "Orchestrator attempted synthesis (should use report-writer)"
       log_violation(violation)
   ```

4. **Skill & Phase Tracking**
   - Updates `logs/state/current.json` with active skill
   - Writes completed skills to `logs/session_*_state.json`
   - **Research**: decomposition → parallel research → synthesis → delivery
   - **Planning**: analyze → architect → plan → validate (quality gate)

**Example log entry**:
```
[10:57:22] ORCHESTRATOR → Task ✅
  Input: {"subagent_type": "researcher", "description": "Research quantum computing"}
  Output: Success (2.4 KB)
  Duration: 1250ms
```

#### SessionStart Hook (`session-start.py`)

**Runs once when Claude Code session begins**.

**Responsibilities**:

1. **Auto-Setup**
   ```python
   # Create directories if missing
   create_directory("files/research_notes/")
   create_directory("files/reports/")
   create_directory("logs/")
   create_directory("logs/state/")
   ```

2. **Session Initialization**
   - Generates unique session ID (e.g., `session_20251118_105714`)
   - Creates log files (`transcript.txt`, `tool_calls.jsonl`, `state.json`)
   - Displays setup status to user

3. **Session Restoration** (if previous session was interrupted)
   - Reads `logs/state/current.json` for active skill
   - Detects incomplete research **or** planning workflows
   - Offers to resume or start fresh

**Example output**:
```
📝 Session logs initialized: logs/session_20251118_105714_{transcript.txt,tool_calls.jsonl,state.json}
✅ All directories exist
✅ Hooks configured correctly
```

#### Hook + Constraint Synergy

The **combination** of hooks and `allowed-tools` creates robust enforcement:

| Component | Role | Reliability |
|-----------|------|-------------|
| `allowed-tools: Task, Read, Glob, TodoWrite` | **Prevents** orchestrator from writing reports | ~95% (architectural) |
| PostToolUse quality gates | **Detects** if violation somehow occurs | ~100% (catches everything) |
| Session state tracking | **Verifies** all workflow phases complete | ~100% (checks existence) |

**Together**: ~99%+ enforcement reliability with full audit trail.

#### Hook Execution Flow

```
User: "research quantum computing"
    ↓
UserPromptSubmit hook fires (v2.2.0)
    → Detects research trigger
    → Injects skill enforcement reminder
    ↓
SessionStart hook fires
    → Creates directories
    → Initializes session logs
    → Displays status
    ↓
Orchestrator decomposes query
    ↓
Orchestrator spawns researchers (Task tool)
    ↓ PostToolUse hook fires
        → Identifies agent: orchestrator
        → Logs: Task call
        → Updates phase: research (in progress)
    ↓
Each researcher conducts research (WebSearch, Write tools)
    ↓ PostToolUse hook fires (multiple times)
        → Identifies agent: researcher (via file path heuristic)
        → Logs: WebSearch + Write calls
        → Tracks: research note paths
    ↓
All researchers complete
    ↓
Orchestrator spawns report-writer (Task tool)
    ↓ PostToolUse hook fires
        → Identifies agent: orchestrator
        → Logs: Task call
        → Updates phase: synthesis (in progress)
    ↓
Report-writer synthesizes (Read, Write tools)
    ↓ PostToolUse hook fires (multiple times)
        → Identifies agent: report-writer (via file path heuristic)
        → Logs: Read + Write calls
        → Updates phase: synthesis (complete)
    ↓
Session ends
    ↓
All tool calls logged ✅
All phases tracked ✅
Audit trail complete ✅
```

**Same pattern for Planning Skill**: Replace "research X" → "plan X", researchers → spec-analyst/architect/planner, report-writer → quality gate validation. State tracks `currentSkill: spec-workflow-orchestrator`.

**Without hooks**: `allowed-tools` would prevent violations, but you'd have no logs, no tracking, no session management, no quality gate verification.

**With hooks**: Complete observability + enforcement + automation.

### Session Logging

#### Log Format: Flat Structure

```
logs/
├── session_20251118_105714_transcript.txt      # Human-readable
├── session_20251118_105714_tool_calls.jsonl    # Structured JSON
├── session_20251118_105714_state.json          # Session skill/research history
└── state/
    └── current.json                            # Active skill pointer (~100 bytes)
```

**Benefits of flat structure**:
- Easier navigation (no nested directories)
- Simpler programmatic analysis (`grep`, `jq`)
- Compatible with log aggregation tools

#### transcript.txt Example

```
Research Agent Session Log
Session ID: session_20251118_105714
Started: 2025-11-18T10:57:14.369265
================================================================================

[10:57:22] ORCHESTRATOR → Task ✅
  Input: {"subagent_type": "researcher", "description": "Research theoretical foundations", ...}
  Output: Success (2.4 KB)
  Duration: 1250ms

[10:58:45] RESEARCHER → WebSearch ✅
  Input: {"query": "quantum computing qubits superposition"}
  Output: Found 10 results
  Duration: 850ms

[11:02:10] ORCHESTRATOR → Task ✅
  Input: {"subagent_type": "report-writer", ...}
  Output: Success (15.2 KB)
  Duration: 3400ms
```

#### Agent Identification Heuristics

Since Claude Code doesn't provide `parent_tool_use_id` (SDK feature), agents are identified via:

1. **File paths**: Writing to `files/research_notes/` → researcher; `files/reports/` → report-writer
2. **Tool usage**: Task tool with `subagent_type` → orchestrator
3. **Session phase**: During synthesis + WebSearch → researcher

**Accuracy**: ~90% (trade-off for not requiring SDK).

---

## Inspiration & Credits

This project adapts the multi-agent research pattern for Claude Code's skill system, combining patterns from multiple production-proven projects:

### Primary Inspiration

- **[claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent)** by Anthropic PBC<sup>[[5]](#ref-5)</sup>
  - Multi-agent research orchestration concept
  - Decomposition → Research → Synthesis workflow
  - Session logging patterns
  - License: Apache-2.0

### Workflow Patterns

- **[DevFlow](https://github.com/mathewtaylor/devflow)** by Mathew Taylor<sup>[[8]](#ref-8)</sup>
  - Architectural enforcement via `allowed-tools` constraint
  - State tracking with `state.json`
  - Quality gates for phase validation
  - License: MIT

- **[Claude-Flow](https://github.com/ruvnet/claude-flow)** by ruvnet<sup>[[9]](#ref-9)</sup>
  - Session persistence patterns
  - Research session restoration
  - License: MIT

- **[TDD-Guard](https://github.com/nizos/tdd-guard)** by nizos<sup>[[10]](#ref-10)</sup>
  - Agent tracking via tool usage patterns
  - Multi-context workflow enforcement
  - License: MIT

- **[claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase)** by diet103<sup>[[11]](#ref-11)</sup>
  - Skill auto-activation patterns
  - `skill-rules.json` configuration
  - License: MIT

All projects are MIT or Apache-2.0 licensed and used in compliance with their terms.

---

## Author & Acknowledgments

**Created by Ahmed Maged**
GitHub: [@ahmedibrahim085](https://github.com/ahmedibrahim085)

This project was conceived, architected, and guided at every step by Ahmed Maged. Implementation was assisted by Claude Code, but all architectural decisions, design choices, and strategic direction came from the author.

**Special Acknowledgments**:
- Anthropic team for the [claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent) inspiration
- Authors of DevFlow, Claude-Flow, TDD-Guard, and Infrastructure Showcase for proven workflow patterns
- Claude Code community for feature requests and feedback

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## References

<a id="ref-1"></a>**[1]** Anthropic. "Introducing Agent Skills." Anthropic News, October 16, 2025. https://www.anthropic.com/news/skills

<a id="ref-2"></a>**[2]** Anthropic. "Introducing the Model Context Protocol." Anthropic News, November 2024. https://www.anthropic.com/news/model-context-protocol

<a id="ref-3"></a>**[3]** Anthropic. "Agent Skills - Claude Code Docs." Accessed November 2025. https://code.claude.com/docs/en/skills

<a id="ref-4"></a>**[4]** Willison, Simon. "Claude Skills are awesome, maybe a bigger deal than MCP." Simon Willison's Weblog, October 16, 2025. https://simonwillison.net/2025/Oct/16/claude-skills/

<a id="ref-5"></a>**[5]** Anthropic. "How we built our multi-agent research system." Anthropic Engineering Blog, 2025. https://www.anthropic.com/engineering/multi-agent-research-system

<a id="ref-6"></a>**[6]** "Multi-Agent Orchestration: Running 10+ Claude Instances in Parallel (Part 3)." DEV Community, 2025. https://dev.to/bredmond1019/multi-agent-orchestration-running-10-claude-instances-in-parallel-part-3-29da

<a id="ref-7"></a>**[7]** Greyling, Cobus. "Orchestrating Parallel AI Agents." Medium, 2025. https://cobusgreyling.medium.com/orchestrating-parallel-ai-agents-dab96e5f2e61

<a id="ref-8"></a>**[8]** Taylor, Mathew. "DevFlow - Agentic Feature Management." GitHub Repository. https://github.com/mathewtaylor/devflow

<a id="ref-9"></a>**[9]** ruvnet. "Claude-Flow - Agent Orchestration Platform." GitHub Repository. https://github.com/ruvnet/claude-flow

<a id="ref-10"></a>**[10]** nizos. "TDD-Guard - TDD Enforcement for Claude Code." GitHub Repository. https://github.com/nizos/tdd-guard

<a id="ref-11"></a>**[11]** diet103. "Claude Code Infrastructure Showcase." GitHub Repository. https://github.com/diet103/claude-code-infrastructure-showcase

---

**⭐ Star this repo** if you find it useful!
