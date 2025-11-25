# Changelog

All notable changes to the Claude Multi-Agent Research System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
