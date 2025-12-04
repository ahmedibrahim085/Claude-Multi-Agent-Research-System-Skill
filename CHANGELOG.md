# Changelog

All notable changes to the Claude Multi-Agent Research System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] - 2025-12-04

### 🎉 Major Release: Production-Grade Auto-Reindex + Comprehensive Tracing

**96 commits across 7 development phases** (Nov 28 - Dec 4, 2025)

This major release transforms the semantic search skill from basic functionality to a production-grade system with comprehensive auto-indexing, decision tracing, and architectural refinements.

---

### ✨ Added

#### Auto-Reindex System
- **Post-file-modification auto-reindex** - Automatically reindex after Write/Edit operations
  - Triggers on file changes with smart filtering (include/exclude patterns)
  - 4-layer filtering: include patterns, exclude directories, exclude patterns, cooldown
  - Cooldown mechanism (default 300s, configurable per-project)
  - 42x faster incremental reindex vs full (5.29s vs 225s)
- **Session-start auto-reindex** - Smart change detection when Claude Code starts
  - Triggers: startup, resume (after context compaction)
  - Skips: clear, compact (no code changes)

#### Comprehensive Decision Tracing
- **Auto-reindex decision tracing** - Full visibility into every reindex decision (Commit: e446cba)
  - Logs all decisions to session transcript (skip or run)
  - 9 distinct skip reasons with detailed context:
    - `prerequisites_not_ready`, `not_indexable_pattern`, `excluded_directory`
    - `excluded_pattern`, `cooldown_active`, `index_not_found`
    - `concurrent_reindex`, `reindex_success`, `reindex_failed`, `exception`
  - Human-readable log format: `[HH:MM:SS] AUTO-REINDEX → DECISION: file - message`
  - Enables post-mortem debugging and error diagnosis

#### Architecture & Documentation
- **Architecture Decision Records (ADRs)**
  - ADR-001: Direct Script vs Agent for Auto-Reindex (Commit: c1fe85d)
    - Full analysis with benchmarks, cost projections, testing
    - 5x faster, $0 cost, offline support, predictable behavior
  - Quick reference guide for implementation patterns (Commit: 78f0c23)
- **Comprehensive development timeline**
  - 96 commits analyzed chronologically across 7 phases
  - Location: `docs/history/feature-branch-semantic-search-timeline.md`
- **Pre-merge checklist**
  - 39-item comprehensive checklist for production readiness
  - Location: `docs/release/pre-merge-checklist.md`

#### Semantic Search Infrastructure
- **Reindex manager centralization** (`reindex_manager.py`)
  - Unified reindex logic for all hooks
  - Configurable cooldown, file filtering, prerequisites
  - Clean separation of concerns
- **Session state management improvements**
  - Better handling of resumed sessions
  - State file integrity checks

---

### 🔧 Changed

#### Hook System Improvements
- **post-tool-use hook** refactored for auto-reindex
  - Added Write/Edit trigger support
  - Integrated with reindex_manager
  - Graceful error handling
  - **Now logs auto-reindex decisions** to session transcript
- **session-start hook** enhanced
  - Added auto-reindex on startup/resume
  - Skip logic for clear/compact events
  - Better user feedback

#### Configuration & Flexibility
- **Configurable reindex behavior** (`.claude/config.json`)
  - File include patterns (code, docs, config files)
  - File exclude directories (dist/, build/, node_modules/, etc.)
  - File exclude patterns (*_transcript.txt, *.log, etc.)
  - Cooldown seconds (default 300s)
- **Per-hook cooldown overrides**
  - Session-start can use different cooldown than post-tool-use
  - Fixes timing issues with rapid file modifications

#### CLAUDE.md Modernization
- **Progressive disclosure architecture** (Phase 4: 21 commits)
  - Core instructions remain concise (< 100 lines)
  - Detailed workflows imported via @import
  - Token-efficient design
- **Workflow documentation reorganization**
  - `docs/workflows/research-workflow.md` - 90+ trigger keywords
  - `docs/workflows/planning-workflow.md` - 37+ trigger keywords
  - `docs/workflows/semantic-search-hierarchy.md` - Search workflow
  - `docs/workflows/compound-request-handling.md` - Multi-skill detection

#### Code Quality & Fixes
- **15 bug fixes** across reindex logic:
  - Cooldown parameter not respected (Fix #1, #5)
  - Directory exclusion complexity (Fix #2)
  - File filtering edge cases (Fix #3, #4)
  - Timezone-naive datetime comparison (Hybrid fix)
  - Future timestamp handling (Fix #14)
  - None vs False for concurrent reindex (Fix #15)
  - And 8 more documented in commits
- **State file integrity**
  - Better error handling for corrupted state
  - Graceful degradation when state unavailable

---

### 🗑️ Removed (YAGNI Principles Applied)

- **Notebook support removed** - Zero .ipynb files in project (Commit: 3de8b83)
  - Removed `*.ipynb` from file include patterns
  - Removed NotebookEdit trigger from post-tool-use hook
  - Deleted test files and limitation documentation
  - **Rationale:** No evidence of need, MCP backend doesn't support .ipynb parsing
- **Notebook limitation documentation removed**
  - Deleted `docs/testing/notebook-indexing-limitation.md`
  - Analysis showed YAGNI violation

---

### 🐛 Fixed

#### Auto-Reindex Bugs
- **Cooldown not respecting parameter override** (Fix #1, #5)
- **Directory exclusion complexity** (Fix #2)
- **File filtering edge cases** (Fix #3, #4)
- **Timezone-naive datetime comparison** (Hybrid fix)
- **Future timestamp handling** (Fix #14) - Treat future timestamps as stale
- **Concurrent reindex handling** (Fix #15) - Return None (not False)

#### State Management
- **State loading failures** breaking reindex (Issue #2 fix)
  - post-tool-use hook continues even if state load fails
- **Session ID not initialized** on logging failure - Prevents NameError

---

### ⚠️ Known Limitations

#### Platform Limitations
- **Hooks may not fire in resumed sessions** after context compaction
  - Claude Code platform limitation, not our code
  - Workaround: Manual incremental reindex (5-10 seconds)

#### MCP Server Limitations
- **15 file extensions supported**
  - Supported: .py, .js, .jsx, .ts, .tsx, .java, .go, .rs, .c, .cpp, .cc, .cxx, .c++, .cs, .svelte
  - Not supported: .ipynb (notebooks) - no parser in MCP backend

---

### 📊 Performance

#### Benchmarks
- **Incremental reindex:** 5.29s for single file modification
- **Full reindex:** 225s for 196 files, 5755 chunks
- **Performance improvement:** 42x faster incremental vs full
- **Token savings:** 90% using semantic search vs traditional Grep
  - Example: 1 search + 2 reads vs 15 Grep + 26 reads
  - Savings: 5,000-10,000 tokens per task

---

### 📈 Development Statistics

#### Commits & Phases
- **Total commits:** 96
- **Development period:** Nov 28 - Dec 4, 2025 (7 days)
- **Phase 1:** Skill Infrastructure (11 commits, 5 hours)
- **Phase 2:** Integration & Enforcement (11 commits, 3 days)
- **Phase 3:** Architecture Cleanup (13 commits, 1 hour)
- **Phase 4:** CLAUDE.md Modernization (21 commits, 3 hours)
- **Phase 5:** Auto-Reindex Feature (21 commits, 1.5 days)
- **Phase 6:** Architectural Decisions (4 commits, 3 minutes)
- **Phase 7:** Edit/NotebookEdit & YAGNI (15 commits, 1 day)

#### Code Metrics
- **Files added/modified:** 39 files
- **Lines of code:** ~7,700 lines
- **Documentation:** 1500+ lines in timeline, ADRs, guides
- **Trigger keywords:** 200+ across 3 skills

---

### 📋 Migration Guide

#### From v2.3.0 to v3.0.0

**No breaking changes** - This is a feature release with backward compatibility.

**What's New:**
1. Auto-reindex now triggers on Write/Edit operations (automatic)
2. Decision tracing logs to session transcript (automatic)
3. Improved file filtering configuration (optional customization)

**Action Required:** None - all new features work out-of-the-box

**Optional Configuration:**
- Tune cooldown in `.claude/config.json` (`semantic_search.reindex.cooldown_seconds`)
- Customize file patterns if needed (`file_include_patterns`, `file_exclude_patterns`)

---

### 📚 References

- **Full Development Timeline:** `docs/history/feature-branch-semantic-search-timeline.md`
- **Architecture Decisions:** `docs/architecture/ADR-001-direct-script-vs-agent-for-auto-reindex.md`
- **Pre-Merge Checklist:** `docs/release/pre-merge-checklist.md`
- **Configuration Guide:** `docs/configuration/configuration-guide.md`
- **Workflows:** `docs/workflows/` (research, planning, semantic-search, compound)

---

## [2.3.0] - 2025-11-25

### ✨ Added

#### Skill Orchestrator Logging & Tracking

Session-aware tracking for the dual-skill platform.

**New State Architecture:**
- `logs/state/current.json` - Active skill pointer (~100 bytes, never grows)
- `logs/session_*_state.json` - Per-session skill invocations history

**Why Split?** Claude Code's Read tool has 25K token limit. Single file would fail at ~359 skill invocations.

**Tracked Data:**
- `currentSkill`: Which skill is active (multi-agent-researcher or spec-workflow-orchestrator)
- `skillInvocations[]`: All skill activations per session (both skills)
- Start/end times, duration, trigger source

**Enables:**
- Skill routing (prevent concurrent conflicting skills)
- Session restoration (resume interrupted workflows)
- Audit trail (track all skill usage)

### 🔧 Changed

- Moved state directory from `.claude/state/` to `logs/state/` (Claude Code best practices)
- Updated hooks to write skill history to per-session state files
- Enhanced README with dual-skill state architecture documentation

### 🐛 Fixed

- Python 3.9 compatibility: `timezone.utc` instead of `datetime.UTC`

---

## [2.2.0] - 2025-11-23

### 🎉 New Feature: Spec-Workflow-Orchestrator Skill

This release introduces a complete **Planning Orchestration System** alongside the existing research capabilities, transforming the project into a dual-skill orchestration platform.

---

### ✨ Added

#### New Skill: spec-workflow-orchestrator

A comprehensive planning workflow that takes projects from ideation to development-ready specifications.

**Workflow Phases:**
1. **spec-analyst** - Requirements gathering and user story creation
2. **spec-architect** - System design, component architecture, and ADRs
3. **spec-planner** - Task breakdown with dependencies and implementation order

**Key Features:**
- **Quality Gates**: 85% threshold with up to 3 iteration attempts per agent
- **Per-Project Structure**: Each project gets its own `docs/projects/{slug}/` directory
- **Interactive Decision System**: Detects existing projects and offers New/Refine/Archive options
- **Archive System**: Timestamped backups with integrity verification and rollback
- **State Management**: JSON-based workflow state persistence across sessions
- **Version Detection**: Automatic next version detection (v2, v3...v99)

**New Agents (3):**
- `.claude/agents/spec-analyst.md` - Requirements elicitation specialist
- `.claude/agents/spec-architect.md` - System design and ADR creation
- `.claude/agents/spec-planner.md` - Task breakdown and dependency mapping

**New Utilities (5 scripts, 420+ lines):**
- `.claude/utils/archive_project.sh` - Create timestamped project archives
- `.claude/utils/restore_archive.sh` - Restore from specific archive timestamp
- `.claude/utils/list_archives.sh` - List all archives for a project
- `.claude/utils/workflow_state.sh` - JSON state management (set/get/show/clear)
- `.claude/utils/detect_next_version.sh` - Find next available version number

#### Universal Skill Activation Hook

**File:** `.claude/hooks/user-prompt-submit.py`

Intercepts ALL user prompts and enforces proper skill activation:
- Detects 37+ research trigger keywords → enforces multi-agent-researcher
- Detects 90+ planning trigger keywords → enforces spec-workflow-orchestrator
- Regex pattern matching for intent detection
- Priority-based enforcement (research=critical, planning=high)

#### Skill Rules Configuration

**File:** `.claude/skills/skill-rules.json`

Centralized trigger configuration:
- `promptTriggers.keywords` - Word-level detection
- `promptTriggers.intentPatterns` - Regex patterns for contextual matching
- `fileTriggers.pathPatterns` - File-based skill activation
- `validation.qualityGates` - Per-skill quality thresholds

#### New Slash Commands (4)

- `/plan-feature` - Invoke spec-workflow-orchestrator for feature planning
- `/project-status` - Show current project implementation status
- `/research-topic` - Invoke multi-agent-researcher for topic research
- `/verify-structure` - Verify project structure alignment

#### Documentation

- `PRODUCTION_READY_SUMMARY.md` - Comprehensive implementation status
- `HONEST_REVIEW.md` - Candid assessment of system capabilities
- `PROJECT_STRUCTURE.md` - Canonical file organization reference
- `.claude/STRUCTURE_ALIGNMENT.md` - Official vs custom file documentation

#### Test Suites (2)

- `tests/spec-workflow/test_interactive_decision.sh` - 8 tests for interactive decision feature
- `tests/common/test_production_implementation.sh` - 10 tests covering all production features

---

### 🔧 Changed

#### multi-agent-researcher Skill

- **Refactored to Option B Architecture**: Skill orchestrator in dedicated directory
- **Added Reference Documentation**: `reference.md` with implementation details
- **Added Examples**: `examples.md` with comprehensive usage patterns
- **Moved Agents**: Agents now in `.claude/agents/` for proper discovery

#### CLAUDE.md Instructions

- Added comprehensive planning orchestration rules
- Added synthesis phase enforcement (Write tool restriction)
- Added custom configuration file documentation
- Clarified official vs custom Claude Code files

#### .gitignore

- Added `docs/projects/*`, `docs/examples/*`, `docs/testing/*` (user outputs)
- Added `docs/plans/*`, `docs/analysis/*`, `docs/adrs/*` (user-generated)
- Added `.claude/utils/logs/` (runtime logs)
- Preserved directory structure via `.gitkeep` files

---

### 🗂️ Directory Structure Changes

```
.claude/
├── agents/                    # Official agent location (moved from skills/)
│   ├── spec-analyst.md        # NEW
│   ├── spec-architect.md      # NEW
│   ├── spec-planner.md        # NEW
│   ├── researcher.md          # Existing
│   └── report-writer.md       # Existing
├── commands/                  # NEW: Slash commands
│   ├── plan-feature.md
│   ├── project-status.md
│   ├── research-topic.md
│   └── verify-structure.md
├── hooks/
│   ├── user-prompt-submit.py  # NEW: Universal enforcement hook
│   └── HOOKS_SETUP.md         # Updated documentation
├── skills/
│   ├── multi-agent-researcher/
│   │   ├── SKILL.md           # Existing orchestrator
│   │   ├── examples.md        # NEW
│   │   └── reference.md       # NEW
│   ├── spec-workflow-orchestrator/  # NEW: Complete skill
│   │   ├── SKILL.md           # Main orchestrator (1,771 lines)
│   │   ├── examples.md
│   │   ├── reference.md
│   │   └── docs/reference/
│   └── skill-rules.json       # NEW: Trigger configuration
└── utils/                     # NEW: Production utilities
    ├── archive_project.sh
    ├── restore_archive.sh
    ├── list_archives.sh
    ├── workflow_state.sh
    └── detect_next_version.sh

docs/
├── projects/.gitkeep          # User project outputs (gitignored)
├── examples/.gitkeep          # User examples (gitignored)
├── testing/.gitkeep           # User test outputs (gitignored)
├── plans/.gitkeep             # Implementation plans (gitignored)
├── analysis/.gitkeep          # Analysis documents (gitignored)
└── adrs/.gitkeep              # ADRs (gitignored)
```

---

### 📊 Statistics

| Metric | Value |
|--------|-------|
| New Files | 39 |
| Lines Added | ~7,700 |
| New Agents | 3 |
| New Utilities | 5 |
| New Commands | 4 |
| Test Coverage | 18 tests (100% pass) |
| Planning Keywords | 90+ |
| Research Keywords | 37+ |
| Intent Patterns | 35+ |

---

### 🔮 Planned (Not Implemented)

**Compound Request Detection** - Smart handling when user triggers BOTH skills:
- Signal strength analysis (action vs subject detection)
- TRUE/FALSE compound pattern matching
- User clarification via AskUserQuestion
- Implementation plan saved to `docs/plans/compound-detection-implementation-plan.md`

---

### 🐛 Fixed

- Agent discovery issue (moved from `skills/*/agents/` to `.claude/agents/`)
- Frontmatter formatting in spec-analyst.md
- Missing planning keywords in skill-rules.json
- User-generated files incorrectly committed to git

---

### ⚠️ Breaking Changes

None. This release is additive - existing multi-agent-researcher functionality remains unchanged.

---

### 📋 Migration Guide

**From v2.1.x:**
1. Pull latest changes
2. No configuration changes required
3. New skills auto-activate based on prompt keywords
4. Use `/plan-feature` or `/research-topic` for explicit invocation

---

### 🙏 Acknowledgments

- Claude Code team for the extensibility architecture
- Anthropic research on multi-agent orchestration patterns
- Community feedback on planning workflow design

---

## [2.1.3] - 2025-11-18

### Changed
- Clean up redundant text from SKILL.md

---

## [2.1.2] - 2025-11-17

### Fixed
- Minor documentation improvements

---

## [2.1.1] - 2025-11-17

### Fixed
- Hook configuration updates

---

## [2.1-hybrid-setup] - 2025-11-17

### Added
- Initial hybrid setup with research orchestration
- multi-agent-researcher skill implementation
- researcher and report-writer agents

---

## Links

- [Full Commit History](../../commits/main)
- [Production Ready Summary](PRODUCTION_READY_SUMMARY.md)
- [Honest Review](HONEST_REVIEW.md)
- [Project Structure](PROJECT_STRUCTURE.md)
