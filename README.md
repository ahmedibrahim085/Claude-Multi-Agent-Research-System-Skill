# Claude Code Multi-Agent Research Skill

**Orchestrated multi-agent research with architectural enforcement, parallel execution, and comprehensive audit trails.**

[![Version](https://img.shields.io/badge/version-2.5.1-blue.svg)](https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎉 v2.5.1: Comprehensive Skill Tests + Quality Improvements

A **tri-skill platform** with smart routing, auto-indexing, and compound request detection:

| Skill | Purpose | Agents |
|-------|---------|--------|
| **multi-agent-researcher** | Comprehensive topic investigation | researcher, report-writer |
| **spec-workflow-orchestrator** | Planning from ideation to dev-ready specs | spec-analyst, spec-architect, spec-planner |
| **semantic-search** | RAG-powered semantic code search (finds code by meaning, not keywords) | semantic-search-reader, semantic-search-indexer |

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
- [Semantic-Search Workflow (RAG System)](#semantic-search-workflow-rag-system)
  - [What is RAG?](#what-is-rag)
  - [Trigger Keywords](#trigger-keywords)
  - [Agent Roles](#agent-roles)
  - [RAG Workflow Details](#rag-workflow-details)
  - [Features](#semantic-search-features)
  - [Benefits Over Traditional Search](#benefits-over-traditional-search)
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

The semantic-search skill implements **RAG (Retrieval-Augmented Generation)** - an AI technique that finds relevant code by understanding meaning rather than matching keywords. It converts code into vector embeddings and uses semantic similarity to retrieve contextually relevant chunks when you ask questions in natural language.

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

Choose one installation method based on your needs:

**📋 Quick Decision Guide**:
| Scenario | Installation Method |
|----------|---------------------|
| Add skills to **one existing project** | [Option 1: Project Skills](#option-1-project-skills-recommended) |
| Make skills available to **all projects** | [Option 2: Personal Skills](#option-2-personal-skills) |
| Explore this repository **standalone** | [Option 3: Standalone Usage](#option-3-standalone-usage) |

---

#### Option 1: Project Skills (Recommended)

**Use Case**: Add multi-agent research, planning, and semantic search to an existing Claude Code project.

**How It Works**: Claude Code auto-discovers skills in `.claude/skills/` directory. No manual configuration needed.

```bash
# Navigate to your existing project
cd ~/my-existing-project

# Clone into .claude/skills/ directory
mkdir -p .claude/skills
cd .claude/skills
git clone https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill.git
```

**Optional: Enable semantic-search skill**

> **Note:** The multi-agent-researcher and spec-workflow-orchestrator skills work immediately. Only install if you want semantic code search.

```bash
# Clone Python library to standard location (one-time, 30 seconds)
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local
```

**That's it!** Start Claude Code in your project:

```bash
cd ~/my-existing-project
claude
```

The SessionStart hook will automatically initialize all skills.

**Optional: Import Orchestration Rules**

If you want to use this project's orchestration rules (auto-skill-activation hooks) in your existing project:

```markdown
# Add to your project's .claude/CLAUDE.md
@import .claude/skills/Claude-Multi-Agent-Research-System-Skill/.claude/CLAUDE.md
```

This imports the trigger keyword system that auto-activates skills based on your requests (e.g., "research X" → multi-agent-researcher, "plan feature Y" → spec-workflow-orchestrator).

---

#### Option 2: Personal Skills

**Use Case**: Make skills available to **all** your Claude Code projects (system-wide installation).

**How It Works**: Claude Code auto-discovers skills in `~/.claude/skills/` and makes them available to every project.

```bash
# Clone into personal skills directory
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill.git

# Optional: Enable semantic-search
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local
```

**That's it!** Skills are now available in **every** Claude Code project:

```bash
cd ~/any-project
claude
# Skills automatically available
```

**Note**: Personal skills don't include project-specific hooks or CLAUDE.md rules. You'll need to manually invoke skills using the Skill tool or add @import statements to individual projects.

---

#### Option 3: Standalone Usage

**Use Case**: Explore this repository as a dedicated research/planning workspace.

```bash
git clone https://github.com/ahmedibrahim085/Claude-Multi-Agent-Research-System-Skill.git
cd Claude-Multi-Agent-Research-System-Skill

# Optional: Enable semantic-search
git clone https://github.com/FarhanAliRaza/claude-context-local.git ~/.local/share/claude-context-local

# Start Claude Code
claude
```

**Full Experience**: This option includes:
- All 3 skills (multi-agent-researcher, spec-workflow-orchestrator, semantic-search)
- Auto-activation hooks (trigger keywords automatically invoke skills)
- Pre-configured directory structure
- Session logging and state management
- 4 custom slash commands (`/research-topic`, `/plan-feature`, `/project-status`, `/verify-structure`)

---

#### Common Setup (All Options)

**Automatic Initialization**: The SessionStart hook runs on every `claude` command and:
- Auto-reindexes semantic search (smart change detection, 60-min cooldown)
- Creates required directories (`files/research_notes/`, `files/reports/`, `logs/`)
- Initializes session logging
- Checks prerequisites and displays setup status

**No Manual Configuration**: Hooks are pre-configured in `.claude/settings.json` and work out-of-the-box.

**First-Time Semantic Search**: The embedding model (~1.2GB) downloads automatically on first use (10-30 minutes). Subsequent uses are instant. Model cached at `~/.claude_code_search/models/`.

**Semantic Search Details**:
- Imports Python modules from claude-context-local via `sys.path.insert()`
- No virtual environment, no pip install, no `uv` needed
- Merkle tree change detection for smart reindexing
- Multi-language code chunking (15+ languages)
- Embedding generation (sentence-transformers, FAISS)

**License Note**: claude-context-local is GPL-3.0. Our project imports it via PYTHONPATH (dynamic linking), preserving our Apache 2.0 license. See `docs/architecture/MCP-DEPENDENCY-STRATEGY.md` for details.

**Important**: Do not duplicate hooks in `settings.local.json` to avoid duplicate hook executions.

### What Makes This Different?

**Quick Answer**: This project uses **orchestrated multi-agent research** instead of single-query web search.

**Direct Approach** (typing "tell me about quantum computing"):
```
You → Claude → 1-2 WebSearch calls → Summary
Time: 30-60 seconds
Depth: Limited to what fits in single response
Sources: 2-3 quick sources
```

**This Skill** (typing "research quantum computing"):
```
You → Orchestrator → Decomposes into 3-4 subtopics
                  → Spawns 4 researcher agents (parallel)
                  → Each does multi-source research
                  → Report-writer synthesizes findings
                  → Comprehensive cross-referenced report

Time: 5-8 minutes
Depth: Multi-source, peer-reviewed quality
Sources: 8-15 authoritative sources per topic
Audit Trail: Session logs + research notes + final report
```

**When to Use This Skill**:
| Scenario | Use This Skill | Use Direct Approach |
|----------|----------------|---------------------|
| In-depth research (2+ sources needed) | ✅ Yes | ❌ Too shallow |
| Comprehensive coverage important | ✅ Yes | ❌ Incomplete |
| Need audit trail for compliance | ✅ Yes | ❌ No logs |
| Quick factual question | ❌ Overkill | ✅ Yes |
| Simple documentation lookup | ❌ Too slow | ✅ Yes |

**Example Comparison**:

```
Direct: "What is quantum entanglement?"
→ 45 seconds
→ 1 paragraph summary
→ 2 sources

This Skill: "research quantum entanglement"
→ 6 minutes
→ 4 research notes (foundations, experiments, applications, implications)
→ 1 synthesis report cross-referencing all findings
→ 12 authoritative sources
→ Complete session logs
```

**Bottom Line**: Use this when you need comprehensive, well-researched, auditable findings. Use direct questions for quick factual lookups.

### Your First Research Query

Try this example:
```
research quantum computing fundamentals
```

**What Happens**:
1. **UserPromptSubmit hook** detects "research" keyword → activates multi-agent-researcher skill
2. **Orchestrator** decomposes topic into 3-4 focused subtopics
3. **Four researcher agents** spawn in parallel (each conducts web searches)
4. **Each researcher** writes findings to `files/research_notes/`
5. **Report-writer agent** synthesizes all findings into comprehensive report
6. **Orchestrator** delivers final summary to you

**Expected Timing**:

| Stage | First Run | Subsequent Runs |
|-------|-----------|-----------------|
| **Setup** (directory creation, session init) | ~2-3 seconds | ~1 second |
| **Research** (4 agents in parallel) | 3-5 minutes | 3-5 minutes |
| **Synthesis** (report-writer) | 1-2 minutes | 1-2 minutes |
| **Total** | **5-8 minutes** | **4-6 minutes** |

**First-Time Setup Messages**:

On your very first run, you'll see:
```
🔧 First-time setup detected
✅ Created settings.local.json from template
✅ Created directories: files/research_notes/, files/reports/, logs/
📝 Session logs initialized: logs/session_20251216_150000_*
```

**Expected Output**:
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

**Where to Find Results**:
- **Individual research notes**: `files/research_notes/{subtopic}_YYYYMMDD-HHMMSS.md`
- **Final synthesis**: `files/reports/{topic}_YYYYMMDD-HHMMSS.md`
- **Session logs**: `logs/session_YYYYMMDD_HHMMSS_{transcript.txt,tool_calls.jsonl,state.json}`

**What If Something Fails?**:

1. **Import errors on startup**:
   ```bash
   python3 setup.py --repair
   ```

2. **Research produces no results**:
   - Check API key: `echo $ANTHROPIC_API_KEY`
   - Review logs: `cat logs/session_*_transcript.txt | tail -50`
   - See [Troubleshooting](#troubleshooting) section

3. **Takes longer than expected**:
   - Normal: Research quality > speed
   - Can interrupt with `Ctrl+C` and use partial results
   - Check `files/research_notes/` for individual findings

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

## Semantic-Search Workflow (RAG System)

### What is RAG?

**RAG (Retrieval-Augmented Generation)** combines two AI capabilities to provide intelligent, context-aware responses:

1. **Retrieval**: Search a knowledge base for relevant information using semantic similarity
   - Converts code into vector embeddings (numerical representations)
   - Finds semantically similar content based on meaning, not just keywords
   - Uses FAISS (Facebook AI Similarity Search) for efficient vector search

2. **Augmentation**: Provides retrieved context to the language model for accurate responses
   - LLM receives: Your query + Retrieved code chunks
   - Result: Project-specific answers grounded in actual code
   - No hallucination - answers based on real codebase content

**Why RAG for Code Search?**

Traditional keyword search fails when code uses different terminology:

- Search `"authentication"` → Misses `signin()`, `verifyUser()`, `auth_middleware`
- Search `"database"` → Misses `Repository`, `ORM`, `queryBuilder`, `DataSource`
- Search `"error handling"` → Misses `try/catch`, `Result<T>`, `Exception`, `panic`

**RAG understands meaning**, not just words:

- Query: `"find authentication logic"`
- Retrieves: Login functions, auth middleware, token validation, session handling
- Even if they use different terminology like `signin`, `verify`, `authorize`

**Real Example**:

```
Traditional grep: "authentication"  → 12 matches, 8 false positives (documentation, comments)
Semantic RAG:     "auth logic"     → 15 semantically relevant code chunks, 0 false positives
```

### Trigger Keywords

Semantic-search is automatically activated when your prompt contains these patterns (37+ keywords):

**Search Operations** (18 keywords):
```
"search for", "find", "locate", "show me", "where is"
"look for", "get me", "retrieve", "fetch", "discover"
"search code", "code search", "find code"
"show implementation", "find implementation"
"what code", "which files"
```

**Code Discovery** (10 keywords):
```
"how does", "what does", "explain"
"similar to", "like this code", "resembles"
"examples of", "patterns for"
"find similar", "similar files"
```

**Index Operations** (9 keywords):
```
"reindex", "index", "rebuild index"
"update index", "incremental reindex"
"index status", "check index"
"what's indexed", "indexed projects"
```

**Examples**:
```bash
✅ "search for authentication logic"        → semantic-search-reader
✅ "find database query patterns"           → semantic-search-reader
✅ "reindex the project"                    → semantic-search-indexer
✅ "show me error handling code"            → semantic-search-reader
✅ "find similar implementations to auth.py" → semantic-search-reader
✅ "what's the index status?"               → semantic-search-indexer
✅ "how does the login system work"         → semantic-search-reader
```

**Note**: Full trigger list in `.claude/skills/skill-rules.json` (semantic-search section, 69 keywords + 27 patterns)

### Agent Roles

The semantic-search skill uses two specialized agents with distinct responsibilities:

| Agent | Operations | Triggers | Prerequisites | Output |
|-------|-----------|----------|---------------|--------|
| **semantic-search-indexer** | Build/update vector database | `index`, `reindex`, `status`, `incremental-reindex` | None (creates index if missing) | FAISS index, cache files, state tracking |
| **semantic-search-reader** | Search and retrieve code | `search`, `find-similar`, `list-projects` | Project must be indexed (auto-triggers indexer if needed) | Ranked code chunks with relevance scores |

**Indexer Operations**:
- **Full reindex**: Complete rebuild of vector database from scratch
- **Incremental reindex**: Smart updates using Merkle tree change detection (only re-embeds changed files)
- **Status**: Report index state, bloat percentage, last update timestamp

**Reader Operations**:
- **Search**: Natural language code search (`"find authentication logic"`)
- **Find-similar**: Find code similar to a specific file (`"similar to auth.py"`)
- **List-projects**: Show all indexed projects

**Auto-Triggering**:
- **Session start**: Indexer runs if changes detected since last session
- **File Write/Edit**: Indexer triggers after 5-minute cooldown
- **Search without index**: Reader auto-triggers indexer if project not indexed

### RAG Workflow Details

The RAG system operates in two main modes: **Index Building** (offline, happens once or on changes) and **Search & Retrieval** (online, happens on each query).

```
┌──────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC-SEARCH RAG WORKFLOW                       │
└──────────────────────────────────────────────────────────────────────┘

PHASE 1: INDEX BUILDING (Offline - Once per project, updates on changes)
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│ Code Files  │─────▶│  Chunking    │─────▶│  Embeddings   │
│ (.py, .js,  │      │ (functions,  │      │ (768-dim      │
│  .ts, etc)  │      │  classes,    │      │  vectors)     │
└─────────────┘      │  blocks)     │      └───────┬───────┘
                     └──────────────┘              │
                     15+ languages                 │
                                                    ▼
                                            ┌───────────────┐
                                            │ FAISS Index   │
                                            │ (IndexFlatIP) │
                                            │ + Cache       │
                                            └───────────────┘
                                            Merkle tree tracks
                                            changes for smart
                                            incremental updates

PHASE 2-4: SEARCH & RETRIEVAL (Online - Every query)
┌─────────────────┐      ┌──────────────┐      ┌────────────┐
│  User Query     │─────▶│ Query        │─────▶│  Vector    │
│  "find auth     │      │ Embedding    │      │  Search    │
│   logic"        │      │ (same model) │      │  (cosine   │
└─────────────────┘      └──────────────┘      │  similarity│
                                                └──────┬─────┘
                                                       │
                                                       ▼
┌─────────────────┐      ┌──────────────┐      ┌────────────┐
│  Claude +       │◀─────│  Retrieved   │◀─────│  Ranked    │
│  Context        │      │  Chunks      │      │  Results   │
│  (Augmented     │      │  (with file  │      │  (Top-k    │
│   Response)     │      │   paths)     │      │   similar) │
└─────────────────┘      └──────────────┘      └────────────┘
```

#### Phase 1: Index Building (Offline)

**When it runs**: First use, file changes (5-min cooldown), session start

**Process**:
1. **Code Chunking**: Splits code files into meaningful chunks
   - Language-aware parsing (15+ languages: Python, JavaScript, TypeScript, etc.)
   - Chunks: Functions, classes, methods, blocks
   - Preserves context: Includes docstrings, comments, signatures

2. **Embedding Generation**: Converts chunks into 768-dimensional vectors
   - Model: `google/embeddinggemma-300m` (1.2GB, one-time download)
   - Each chunk → 768 numbers representing semantic meaning
   - Similar code produces similar vectors

3. **Vector Storage**: Builds FAISS index for fast similarity search
   - IndexFlatIP: Simple, reliable, cross-platform
   - Stores vectors + metadata (file path, line numbers)
   - Enables sub-second search across thousands of files

4. **Smart Caching**: Merkle tree tracks file changes
   - Only re-embeds changed files (incremental reindex)
   - Embedding cache: 3.2x speedup on subsequent reindexes
   - State tracking: Last update timestamp, bloat percentage

**Output**: `~/.claude_code_search/projects/{project}/index.faiss` + metadata

#### Phase 2: Query Processing (Online)

**When it runs**: Every search query

**Process**:
1. **Trigger Detection**: Hook identifies semantic-search intent
   - User: `"find authentication logic"`
   - Hook: Detects "find" keyword → Activates semantic-search skill

2. **Agent Selection**: Routes to semantic-search-reader
   - Checks if project is indexed
   - If not indexed: Auto-triggers semantic-search-indexer first

3. **Query Embedding**: Converts natural language query to vector
   - Same model as index building (`embeddinggemma-300m`)
   - Query: `"find authentication logic"` → 768-dim vector
   - Vector represents semantic meaning of the query

#### Phase 3: Retrieval

**Process**:
1. **Vector Similarity Search**: Compares query vector with all code vectors
   - FAISS performs cosine similarity: `similarity = dot(query_vec, code_vec) / (||query_vec|| * ||code_vec||)`
   - Finds Top-k most similar chunks (default k=5, configurable)
   - Sub-second search even for large codebases (10,000+ files)

2. **Ranking**: Orders results by relevance score
   - Higher similarity = more relevant
   - Score range: 0.0 (unrelated) to 1.0 (identical)
   - Returns top-k results ranked by score

3. **Context Extraction**: Retrieves full chunk content with metadata
   - File path: `src/auth/login.py`
   - Line numbers: Lines 45-67
   - Code content: Full function/class with context
   - Relevance score: 0.87

**Output**: Ranked list of code chunks with file locations

#### Phase 4: Augmentation

**Process**:
1. **Context Assembly**: Combines query + retrieved chunks
   - Original query: `"find authentication logic"`
   - Retrieved: 15 code chunks from auth.py, middleware.ts, tokens.py
   - Format: File paths + code snippets + relevance scores

2. **LLM Augmentation**: Claude receives query + context
   - Claude sees: User question + Relevant code from codebase
   - No guessing: Answers grounded in actual project code
   - No hallucination: If code doesn't exist, Claude says so

3. **Response Generation**: Claude provides accurate, project-specific answer
   - Cites specific files and line numbers
   - Explains how the code works
   - Can suggest improvements or answer follow-up questions

**Example Output**:
```
Claude: I found your authentication logic across 3 files:

1. src/auth/login.py:45-67 - Main login function with JWT generation
2. src/middleware/auth.ts:12-34 - Express middleware for token validation
3. src/utils/tokens.py:78-95 - Token refresh and expiration handling

The login flow uses JWT tokens with 24-hour expiration...
```

### Semantic-Search Features

1. **Automatic Index Management**
   - **Auto-reindex on file changes**: Triggers after Write/Edit operations (5-minute cooldown)
   - **Auto-reindex on session start**: Smart change detection when Claude Code starts
   - **Incremental updates**: Only re-embeds changed files using Merkle tree tracking
   - **No manual intervention**: Index stays current automatically

2. **Smart Caching & Performance**
   - **Embedding cache**: Stores generated embeddings for 3.2x speedup on reindexes
   - **Sub-second search**: FAISS enables fast similarity search even for large codebases
   - **GPU acceleration**: Uses MPS (Metal Performance Shaders) on Apple Silicon for 2-3x faster embedding
   - **Efficient storage**: Typical index size 5-50MB per project

3. **Cross-Platform Compatibility**
   - **IndexFlatIP**: Simple, reliable FAISS index type that works everywhere
   - **Tested platforms**: macOS (Intel + Apple Silicon), Linux (x86_64, ARM64), Windows WSL
   - **No special dependencies**: Works with standard Python packages

4. **Multi-Language Support**
   - **15+ programming languages**: Python, JavaScript, TypeScript, Java, C++, Go, Rust, etc.
   - **Language-aware chunking**: Understands code structure (functions, classes, methods)
   - **Context preservation**: Includes docstrings, comments, type hints

5. **Large Codebase Support**
   - **Scalable**: Handles projects with 10,000+ files
   - **Memory efficient**: Doesn't load entire codebase into memory
   - **Chunked processing**: Processes files incrementally

6. **Comprehensive Decision Tracing**
   - **Reindex decisions**: Full visibility into skip reasons, timing, errors
   - **Status reporting**: Index state, bloat percentage, last update timestamp
   - **Debug information**: Detailed logs for troubleshooting

### Benefits Over Traditional Search

1. **Semantic Understanding (Not Just Keywords)**

   **Traditional grep**:
   ```bash
   $ grep -r "authentication" .
   # Finds: 12 matches
   # Misses: signin(), verifyUser(), auth_middleware, validateToken()
   # False positives: Comments, documentation, variable names
   ```

   **Semantic RAG**:
   ```bash
   You: "find authentication logic"
   # Finds: All auth-related code regardless of terminology
   # Includes: login(), signin(), authenticate(), verifyUser(),
   #          auth_middleware, validateToken(), checkSession()
   # Zero false positives: Only actual implementation code
   ```

2. **Massive Token Savings**
   - **Grep exploration**: 15+ attempts, 26 file reads, 5,000-10,000 tokens
   - **Semantic search**: 1 query, 2 file reads, 500-1,000 tokens
   - **Savings**: ~90% token reduction for code discovery tasks

3. **No False Positives**
   - Traditional search: `"error"` matches comments, strings, logs, tests
   - RAG search: `"error handling patterns"` retrieves only actual error handling code
   - Result: Higher signal-to-noise ratio, less time reviewing irrelevant results

4. **Natural Language Queries**
   - Don't need to know exact function/variable names
   - Ask questions: `"how does login work"`, `"where are API calls made"`
   - RAG understands intent and finds relevant code

5. **Context-Aware Results**
   - Results ranked by semantic relevance (not just keyword count)
   - Includes file paths and line numbers for easy navigation
   - Claude can explain, summarize, or suggest improvements based on retrieved code

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

Override configuration without editing `config.json`:

**Path Overrides**:
```bash
export RESEARCH_NOTES_DIR=/custom/path/notes    # Default: files/research_notes
export REPORTS_DIR=/custom/path/reports          # Default: files/reports
export LOGS_DIR=/custom/path/logs                # Default: logs
export STATE_DIR=/custom/path/state              # Default: logs/state
```

**Research Settings**:
```bash
export MAX_PARALLEL_RESEARCHERS=2                # Default: 4 (range: 1-10)
```

**Logging Settings**:
```bash
export LOGGING_ENABLED=false                     # Default: true
```

**Priority Order** (highest to lowest):
1. Environment variables (override everything)
2. `.claude/config.json` values
3. Hardcoded defaults

**Usage Example**:
```bash
# Customize paths for this session
export RESEARCH_NOTES_DIR=/tmp/research
export REPORTS_DIR=/tmp/reports
export MAX_PARALLEL_RESEARCHERS=2

# Start Claude Code with custom config
claude
```

**Verification**:
```bash
# Test that env vars are loaded
python3 -c "import sys; sys.path.insert(0, '.claude/utils'); \
from config_loader import load_config; \
import os; os.environ['RESEARCH_NOTES_DIR'] = '/test'; \
print(load_config()['paths']['research_notes'])"
# Should output: /test
```

Then restart Claude Code to apply changes.

### Semantic-Search Configuration

The semantic-search skill implements **RAG (Retrieval-Augmented Generation)** for intelligent code search. It converts code into vector embeddings to find semantically similar content based on meaning, not just keyword matching:

**Model Details**:
- **Model**: `google/embeddinggemma-300m` (768-dimensional embeddings)
- **Size**: ~1.2GB
- **Download**: Automatic on first use (10-30 minutes, depends on internet speed)
- **Cache Location**: `~/.claude_code_search/models/models--google--embeddinggemma-300m`
- **Reuse**: Downloaded once, shared across all projects

**First-Time Usage**:
```
You: "search for user authentication logic"

Claude: Starting semantic search...
[Downloads model: 10-30 minutes]
Indexing project files...
Search complete.
```

**Subsequent Usage**:
```
You: "search for database queries"

Claude: Starting semantic search...
[Uses cached model: ~2 seconds]
Search complete.
```

**Storage Requirements**:
- Model: ~1.2GB (`~/.claude_code_search/models/`)
- Index per project: ~5-50MB (`~/.claude_code_search/projects/{project}/`)
- Embedding cache: ~2-20MB per project (reused across reindexes)

**Manual Model Management**:
```bash
# Check if model is downloaded
ls -lh ~/.claude_code_search/models/models--google--embeddinggemma-300m/

# Check model size
du -sh ~/.claude_code_search/models/

# Remove model (will re-download on next use)
rm -rf ~/.claude_code_search/models/

# Remove all indexes (safe, will rebuild on demand)
rm -rf ~/.claude_code_search/projects/
```

**Performance Notes**:
- **Apple Silicon**: Uses MPS (Metal Performance Shaders) GPU acceleration
  - Model loads on `mps:0` device
  - ~2-3x faster than CPU
- **Other platforms**: Uses CPU (faiss-cpu)
  - Still fast, but no GPU acceleration

**Troubleshooting**:
- **Slow first-time download**: Normal, model is 1.2GB (10-30 min)
- **Disk space error**: Ensure 1.5GB+ free space in home directory
- **Model corruption**: Delete `~/.claude_code_search/models/` and retry

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

#### Settings Files Overview

Three settings files work together - understanding their roles prevents configuration errors:

| File | Purpose | Location | User Action | Committed to Git |
|------|---------|----------|-------------|------------------|
| `.claude/settings.json` | **Golden configuration** (hooks, permissions, tools) | Project root | **❌ DO NOT EDIT** | ✅ Yes |
| `.claude/settings.template.json` | **Template for first-time setup** | Project root | **❌ DO NOT EDIT** | ✅ Yes |
| `.claude/settings.local.json` | **User-specific overrides** (gitignored) | Project root | ✅ Safe to customize | ❌ No (gitignored) |

**How They Work Together**:

1. **On first `claude` run**: `session-start.py` hook copies `settings.template.json` → `settings.local.json`
2. **Claude Code loads**: Reads `settings.json` (hooks) + `settings.local.json` (overrides)
3. **Hooks execute**: Configured in `settings.json`, NOT `settings.local.json`

**⚠️ CRITICAL: Do NOT Duplicate Hooks**

If you create or edit `.claude/settings.local.json`, **REMOVE any `hooks` section**:

```json
{
  "// WRONG - This will break things": "",
  "hooks": {
    "UserPromptSubmit": ".../.claude/hooks/user-prompt-submit.py"
  }
}
```

**Why?** Hooks are already in `settings.json`. Duplicating them causes:
- ❌ Hooks run twice per event
- ❌ Duplicate session logs
- ❌ Race conditions in state management
- ❌ Confusing "which hooks are active" debugging

**Safe `settings.local.json` Example**:

```json
{
  "permissions": {
    "allowedDomains": ["example.com", "mycompany.com"]
  }
}
```

**When to Edit Each File**:
- **`settings.json`**: Never (managed by project maintainers)
- **`settings.template.json`**: Never (template only)
- **`settings.local.json`**: Customize paths/permissions (no hooks!)

---

## Troubleshooting

Common issues and solutions for first-time users:

### Hooks Not Executing / Import Errors

**Symptoms**:
- Error message: `ImportError: No module named 'state_manager'`
- Error message: `ImportError: No module named 'session_logger'`
- No session logs created in `logs/` directory
- No "Session logs initialized" message on startup

**Solution**:
```bash
python3 setup.py --repair
```

This validates and fixes:
- Python version compatibility (requires 3.8+)
- Utility module availability (.claude/utils/)
- Hook executability permissions
- Directory structure

**Manual Verification**:
```bash
# Check Python version
python3 --version  # Should show 3.8+

# Check utility modules exist
ls -la .claude/utils/*.py

# Check hooks are executable
ls -la .claude/hooks/*.py  # Should show -rwxr-xr-x

# Test session-start hook manually
python3 .claude/hooks/session-start.py
```

### Claude-Context-Local Not Found

**Symptom**: Error during semantic-search: "Failed to import dependencies" or "claude-context-local is not installed"

**Solution**: Clone the Python library:
```bash
git clone https://github.com/FarhanAliRaza/claude-context-local.git \
  ~/.local/share/claude-context-local

# Verify installation
ls -la ~/.local/share/claude-context-local/
```

**Important**: No venv, no pip install, no `uv` needed. Just clone!

### Embedding Model Download Issues

**Symptom 1**: Slow first semantic-search (10-30 minutes)

**Solution**: This is NORMAL - the 1.2GB embedding model downloads automatically on first use. Subsequent searches are instant (~2 seconds).

**Symptom 2**: Download fails or hangs

**Solutions**:
```bash
# Check disk space (needs 1.5GB+)
df -h ~

# Check internet connection
curl -I https://huggingface.co

# Remove corrupted download and retry
rm -rf ~/.claude_code_search/models/
# Then retry semantic-search
```

### Hooks Not Running / No Session Logs

**Symptoms**:
- No files in `logs/` directory
- No "Session logs initialized" message when starting Claude Code
- Research skill doesn't enforce delegation

**Solutions**:

1. **Check settings.json exists**:
   ```bash
   cat .claude/settings.json | head -20
   # Should show hooks configuration
   ```

2. **Check hooks are executable**:
   ```bash
   ls -la .claude/hooks/*.py
   # Should show -rwxr-xr-x (executable)
   ```

3. **Manually test hooks**:
   ```bash
   python3 .claude/hooks/session-start.py
   # Should create directories and show status
   ```

4. **Check for Python errors**:
   ```bash
   python3 -c "import sys; sys.path.insert(0, '.claude/utils'); import state_manager"
   # Should return no errors
   ```

### Research Produces No Results

**Symptoms**:
- Research completes but no files in `files/reports/`
- Empty or incomplete results
- Agents spawn but produce nothing

**Possible Causes & Solutions**:

1. **API quota exceeded**:
   ```bash
   # Check API key is set
   echo $ANTHROPIC_API_KEY  # Should not be empty
   ```

2. **Web search disabled**:
   ```bash
   # Check permissions in settings.json
   grep -A5 '"permissions"' .claude/settings.json
   # Should show WebSearch allowed
   ```

3. **Write permissions**:
   ```bash
   # Check directories are writable
   ls -ld files/research_notes/ files/reports/
   # Should show drwxr-xr-x (writable)
   ```

4. **Review session logs**:
   ```bash
   # Check latest session for errors
   cat logs/session_*_transcript.txt | tail -50
   # Look for "Error" or "⚠️" messages
   ```

### Performance Issues / Slow Research

**Symptom**: Research takes longer than expected (>10 minutes)

**Possible Causes**:
- Slow internet connection (affects web searches)
- Rate limited by search APIs
- Large topic requiring extensive research
- Multiple parallel agents competing for resources

**Not a Problem**: Research quality > speed. You can interrupt with `Ctrl+C` and use partial results from `files/research_notes/`.

**Optimization Tips**:
```bash
# Reduce parallel researchers in config.json
# Change from 4 to 2 for slower connections
"max_parallel_researchers": 2
```

### Session State Corruption

**Symptoms**:
- Weird behavior with workflow state
- "Skip research" when you didn't ask to
- Duplicate research sessions logged
- State conflicts between skills

**Solution - Clear state** (safe to delete):
```bash
# Remove all state files
rm -f logs/state/*.json logs/session_*

# Restart Claude Code - fresh state will be created
claude
```

**What gets reset**:
- Workflow state (current skill pointer)
- Session history
- Research session tracking

**What's preserved**:
- Configuration (config.json)
- Research outputs (files/research_notes/, files/reports/)
- Semantic search indexes

### Paths Resolved to Wrong Location

**Symptoms**:
- Files created in unexpected directories
- config.json paths not being respected
- "File not found" errors for existing files

**Solution - Start Claude Code from project root**:
```bash
# WRONG - Don't start from parent or subdirectory
cd ~/projects/
claude  # ❌ Wrong working directory

# RIGHT - Start from project root
cd ~/projects/Claude-Multi-Agent-Research-System-Skill/
claude  # ✅ Correct
```

**Why**: All paths in config.json are relative to project root. Hooks use `Path(__file__).parent.parent.parent` to find project root.

### Semantic-Search Not Working

**Symptom**: Semantic-search commands fail or produce no results

**Diagnostic Checklist**:

```bash
# 1. Check claude-context-local is installed
ls -la ~/.local/share/claude-context-local/
# Should show directories: merkle/, chunking/, embeddings/

# 2. Check embedding model is downloaded
ls -la ~/.claude_code_search/models/models--google--embeddinggemma-300m/
# Should show model files (1.2GB total)

# 3. Check project is indexed
ls -la ~/.claude_code_search/projects/*/
# Should show index files for your project

# 4. Test indexing manually
python3 .claude/skills/semantic-search/scripts/incremental-reindex $(pwd)
# Should show indexing progress

# 5. Test search manually
python3 .claude/skills/semantic-search/scripts/search $(pwd) "test query"
# Should return results
```

### Git Command Not Found (Semantic-Search)

**Symptom**: Semantic-search fails with git-related errors

**Solution**: Install git:
```bash
# macOS
brew install git

# Linux (Debian/Ubuntu)
sudo apt-get install git

# Linux (RHEL/CentOS)
sudo yum install git

# Verify
git --version
```

**Why needed**: Semantic-search uses `git rev-parse` to find project root.

### Still Having Issues?

1. **Enable detailed logging**:
   ```bash
   # Check config.json has logging enabled
   grep -A3 '"logging"' .claude/config.json
   ```

2. **Review session logs**:
   ```bash
   ls -lt logs/session_* | head -3
   # Check most recent session logs
   ```

3. **Run full diagnostic**:
   ```bash
   python3 setup.py --verify
   # Shows detailed system status
   ```

4. **Check prerequisites**:
   ```bash
   python3 --version  # 3.8+
   git --version      # Any version
   which bash         # /bin/bash or similar
   df -h ~            # >1.5GB free
   ```

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

### Semantic Search Infrastructure

- **[claude-context-local](https://github.com/FarhanAliRaza/claude-context-local)** by FarhanAliRaza<sup>[[12]](#ref-12)</sup>
  - Foundation for semantic-search skill (RAG system)
  - FAISS-based vector indexing (IndexFlatIP)
  - Multi-language code chunking (15+ languages)
  - Merkle tree change detection for smart reindexing
  - Embedding generation (sentence-transformers)
  - License: GPL-3.0 (imported via PYTHONPATH for license compatibility)

All projects are MIT, Apache-2.0, or GPL-3.0 licensed and used in compliance with their terms.

---

## Author & Acknowledgments

**Created by Ahmed Maged**
GitHub: [@ahmedibrahim085](https://github.com/ahmedibrahim085)

This project was conceived, architected, and guided at every step by Ahmed Maged. Implementation was assisted by Claude Code, but all architectural decisions, design choices, and strategic direction came from the author.

**Special Acknowledgments**:
- Anthropic team for the [claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent) inspiration
- FarhanAliRaza for [claude-context-local](https://github.com/FarhanAliRaza/claude-context-local), the foundation of our semantic-search skill
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

<a id="ref-12"></a>**[12]** FarhanAliRaza. "claude-context-local - Local Context for Claude." GitHub Repository. https://github.com/FarhanAliRaza/claude-context-local

---

**⭐ Star this repo** if you find it useful!
