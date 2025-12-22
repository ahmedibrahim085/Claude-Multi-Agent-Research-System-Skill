# Changelog

All notable changes to the Claude Multi-Agent Research System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.5.4] - 2025-12-22

### 🐛 Bug Fix: Fresh Clone Crashes

**P0 fix** for fresh clone crashes when storage directory doesn't exist.

**Problem:**
- Fresh clones crashed in `_acquire_reindex_lock()` when `~/.claude_code_search/projects/` didn't exist
- Exception silently swallowed, no debug output

**Solution:**
1. Added `storage_dir.mkdir(parents=True, exist_ok=True)` before lock file creation
2. Added traceback logging to stderr for debugging
3. Added `state_dir.mkdir()` safety check in first-prompt hook

### ♻️ Refactor: Semantic-Search Trigger Reduction (YAGNI)

**Reduced trigger keywords** to eliminate overlap with multi-agent-researcher.

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Keywords | 70 | 49 | 30% |
| Intent Patterns | 28 | 17 | 39% |

**Removed:** Generic questions (how does, where is, what is), explanations, similarity searches
**Kept:** Indexing operations, explicit codebase references, documentation search

**Files Modified:**
- `.claude/utils/reindex_manager.py`
- `.claude/hooks/first-prompt-reindex.py`
- `.claude/skills/skill-rules.json`

**Full Release Notes:** `docs/release/RELEASE_NOTES_v2.5.4.md`

---

## [2.5.3] - 2025-12-22

### 🐛 Bug Fix: Hook Output Buffering

**Fixed stdout buffering issues** that prevented hook output from appearing during fresh clone setup.

**Problem:**
- Hook output wasn't appearing, making it seem like the process was hanging
- Background process could potentially block on stdin inheritance

**Solution:**
1. Added `flush=True` to all print statements in hooks
2. Added `sys.stdout.flush()` before exit
3. Added `stdin=subprocess.DEVNULL` to background process spawn

### ✨ New Feature: CLAUDE.md Automation

**Automated skill discovery** for installations in other projects.

**New Functions:**
- `setup_claude_md()` - Creates or updates `.claude/CLAUDE.md` with skill documentation
- `verify_claude_md()` - Checks if skill instructions are present

**Usage:**
```bash
python3 setup.py --repair  # Creates/updates CLAUDE.md
python3 setup.py --verify  # Checks CLAUDE.md status
```

**Files Modified:**
- `.claude/hooks/first-prompt-reindex.py`
- `.claude/utils/reindex_manager.py`
- `setup.py`
- `README.md`

**Full Release Notes:** `docs/release/RELEASE_NOTES_v2.5.3.md`

---

## [2.5.2] - 2025-12-22

### 🐛 Bug Fix: Fresh Clone Auto-Detection

**Critical fix** for fresh clone experience when global prerequisites already exist.

**Problem:**
- Fresh clones failed to auto-detect global semantic-search prerequisites
- Required 30+ minutes of manual troubleshooting
- Incorrect diagnostics misled users

**Root Cause:**
- `check-prerequisites` script had inverted priority logic (deprecated script marked FAIL, modern script marked WARN)
- No auto-recovery mechanism for stale/failed state files

**Solution:**
1. Fixed `check-prerequisites` priority: `incremental-reindex` (required) vs `index` (deprecated)
2. Added auto-detection to `first-prompt-reindex.py` hook

**New Features:**
- `verify-setup` diagnostic script for quick troubleshooting (5 checks, <1 second)
- Fresh Clone Quick Start documentation in README
- Troubleshooting section for fresh clone issues

**Files Modified:**
- `.claude/skills/semantic-search/scripts/check-prerequisites`
- `.claude/hooks/first-prompt-reindex.py`
- `.claude/skills/semantic-search/scripts/verify-setup` (new)
- `README.md`

**Full Release Notes:** `docs/release/RELEASE_NOTES_v2.5.2.md`

---

## [2.5.1] - 2025-12-17

### 🧪 Testing Infrastructure + Quality Improvements

**Major leap in testing infrastructure** with 65 new skill tests and 100% pass rate.

**Key Highlights:**
- 65 new skill tests covering all 3 specialized skills
- Zero pytest warnings - eliminated all collection and return warnings
- 100% pass rate (154/154 tests in 3.15s)
- Professional cleanup - archived 50 log files, updated .gitignore

**Full Release Notes:** `docs/release/RELEASE_NOTES_v2.5.1.md`

---

## [Unreleased] - 2025-12-09

### ⚡ Performance: Simple Reindex Optimizations

**Simple optimizations** to improve full reindex UX and performance without architectural changes.

**Changes:**

1. **Progress Indicators (UX Improvement)**
   - Added progress messages at each reindex stage
   - Shows file counts, chunk counts, operation names
   - Progress every 50 files during chunking
   - Users now see what's happening during 3-4 minute reindex
   - No more "frozen" appearance

2. **Increased Embedding Batch Size (Performance)**
   - Changed from batch_size=32 (MCP default) to batch_size=64
   - Better GPU utilization for embeddinggemma-300m model
   - Expected speedup: ~15-20% for embedding phase
   - Safe: Uses MCP's existing batch_size parameter

**Impact:**
- Better UX: Users see progress, understand what's happening
- Faster: ~15-20% reduction in embedding time (largest bottleneck)
- Simple: No new dependencies, no architectural changes
- Safe: Falls back to existing behavior if issues

**Rationale:**
- Aligns with "SIMPLICITY IS THE KEY" principle
- Uses MCP's existing capabilities (batch_size parameter)
- No complex infrastructure (no parallel processing, no external databases)
- Works with pip-installable dependencies only

**Files Modified:**
- `.claude/skills/semantic-search/scripts/incremental_reindex.py`:
  - Lines 546-615: Added progress print statements
  - Lines 579-583: Increased batch_size from 32 to 64

---

## [2.4.1] - 2025-12-04

---
**⚠️ HISTORICAL CONTEXT - IndexIDMap2 Era (Superseded Dec 7, 2025)**

This changelog entry describes the **Dec 4, 2025 bug fix** that temporarily used IndexIDMap2. **Three days later (Dec 7)**, we deliberately switched TO IndexFlatIP for Apple Silicon compatibility.

**Current Implementation** (Dec 7+): IndexFlatIP with auto-fallback (full reindex only)
- IndexIDMap2 caused segfaults on Apple Silicon (exit 139)
- IndexFlatIP works perfectly on all platforms including Apple Silicon
- No incremental updates (IndexFlatIP limitation - full reindex only)

**This entry is preserved for historical accuracy - it describes what happened on Dec 4, not current implementation.**

See: Commit `84a92d7` (Dec 7, 2025) - "FIX: Switch from IndexIDMap2 to IndexFlatIP"

---

### 🐛 Bug Fix: IndexFlatIP Confusion + Auto-Reindex Corruption

**Critical fix** for auto-reindex failures caused by MCP native script confusion.

**Problem:**
- MCP native `scripts/index` created unwrapped IndexFlatIP indexes (no IndexIDMap2 wrapper)
- This caused "add_with_ids not implemented" errors during all incremental updates
- All 18+ auto-reindex attempts failed throughout Dec 4 morning
- Post-tool-use hook was firing correctly but reindex operations corrupted

**Root Cause:**
- Fixed `incremental-reindex` script existed (commit 197bcc2) with IndexIDMap2 wrapper ✅
- But old MCP wrapper `scripts/index` was still accessible
- Confusion led to using wrong script for full reindex
- Created unwrapped IndexFlatIP index → all subsequent incremental operations failed

**Solution:**
1. **Deprecated MCP native script:**
   - Renamed: `scripts/index` → `scripts/index.mcp-native.DEPRECATED`
   - Added prominent warning (exits immediately with helpful error)
   - Preserved original code for reference

2. **Updated 22 documentation references:**
   - Changed all `scripts/index` → `scripts/incremental-reindex`
   - Files: reindex_manager.py (2), semantic-search-indexer.md (1), SKILL.md (15), check-prerequisites (2), CLAUDE.md.backup (2)

3. **Created MCP dependency strategy documentation:**
   - `docs/architecture/MCP-DEPENDENCY-STRATEGY.md` (479 lines)
   - Explains why MCP is library-only (merkle, chunking, embeddings)
   - Documents what we DON'T use (buggy mcp_server/CodeSearchServer)

**Testing:**
- ✅ Deprecated script shows error + exits immediately
- ✅ `incremental-reindex --full` creates IndexIDMap2 index (verified)
- ✅ Auto-reindex SUCCESS after cooldown (3 consecutive successes vs 18 failures before)
- ✅ Index operations work: add_with_ids() ✅, remove_ids() ✅
- ✅ Index grew correctly: 6048 → 6166 vectors (+118)

**Impact:**
- ✅ Users can't accidentally use buggy MCP wrapper
- ✅ Clear error message guides to correct script
- ✅ All documentation consistent
- ✅ Auto-reindex works correctly
- ✅ Index corruption prevented

**Files Changed:**
- `.claude/skills/semantic-search/scripts/index` (deleted)
- `.claude/skills/semantic-search/scripts/index.mcp-native.DEPRECATED` (NEW)
- `.claude/utils/reindex_manager.py` (2 refs updated)
- `.claude/agents/semantic-search-indexer.md` (1 ref updated)
- `.claude/skills/semantic-search/SKILL.md` (15 refs updated)
- `.claude/skills/semantic-search/scripts/check-prerequisites` (2 refs updated)
- `.claude/CLAUDE.md.backup` (2 refs updated)
- `docs/architecture/MCP-DEPENDENCY-STRATEGY.md` (NEW - 479 lines)

**Related Commits:**
- Commit 197bcc2 (original IndexIDMap2 fix)
- Commit 2ba522c (this fix)

---

## [2.4.0] - 2025-12-04

### ✨ Feature Release: Production-Grade Auto-Reindex + Comprehensive Tracing

**96 commits across 7 development phases** (Nov 28 - Dec 4, 2025)

This feature release transforms the semantic search skill from basic functionality to a production-grade system with comprehensive auto-indexing, decision tracing, and architectural refinements. All changes are backward compatible with no breaking changes.

---

### ✨ Added

#### Auto-Reindex System
- **Post-file-modification auto-reindex** - Automatically reindex after Write/Edit operations
  - Triggers on file changes with smart filtering (include/exclude patterns)
  - 4-layer filtering: include patterns, exclude directories, exclude patterns, cooldown
  - Cooldown mechanism (default 300s, configurable per-project)
  - Auto-reindex with IndexFlatIP auto-fallback (full reindex only, 3-10 min)
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
- **Performance improvement:** Auto-reindex with IndexFlatIP auto-fallback
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

#### From v2.3.0 to v2.4.0

**No breaking changes** - This is a feature release with backward compatibility following semantic versioning (MINOR bump for new features).

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
