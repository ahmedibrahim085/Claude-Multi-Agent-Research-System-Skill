# Project Structure

**Last Updated**: 2025-12-01
**Status**: Post-Architecture-Cleanup

This document describes the canonical file organization for the Claude Multi-Agent Research System project.

## Core Principles

1. **No Absolute Paths**: All file references use relative/dynamic paths
2. **Logs Consolidated**: All session logs in `./logs` (configured in `.claude/config.json`)
3. **Agents Centralized**: All agent definitions in `.claude/agents/` (NOT in skill subdirectories)
4. **State Centralized**: All runtime state in `logs/state/` (NOT in `.claude/state/`)
5. **Skills Minimal**: Skills contain SKILL.md + optional docs (examples.md, reference.md)
6. **Planning Documents Organized**: Active plans vs. completed vs. archived

---

## Directory Structure

```
Claude-Multi-Agent-Research-System-Skill/
│
├── .claude/
│   ├── config.json                           # Project configuration (logs, research settings)
│   ├── CLAUDE.md                             # Project-specific instructions
│   ├── settings.json                         # Claude Code settings
│   ├── settings.local.json                   # (gitignored - user settings)
│   │
│   ├── agents/                               # ⭐ ALL AGENTS (centralized)
│   │   ├── researcher.md                     # Research agent
│   │   ├── report-writer.md                  # Synthesis agent
│   │   ├── semantic-search-reader.md         # Search READ operations
│   │   ├── semantic-search-indexer.md        # Search WRITE operations
│   │   ├── spec-analyst.md                   # Requirements agent
│   │   ├── spec-architect.md                 # Architecture agent
│   │   └── spec-planner.md                   # Task breakdown agent
│   │
│   ├── skills/
│   │   ├── skill-rules.json                  # Skill activation rules
│   │   │
│   │   ├── multi-agent-researcher/           # Research Skill
│   │   │   ├── SKILL.md                      # Orchestrator (required)
│   │   │   ├── reference.md                  # Documentation (optional)
│   │   │   └── examples.md                   # Examples (optional)
│   │   │
│   │   ├── semantic-search/                  # Semantic Content Search Skill
│   │   │   ├── SKILL.md                      # Orchestrator (required)
│   │   │   ├── scripts/                      # Bash orchestrators (skill-specific)
│   │   │   ├── tests/                        # Skill tests (skill-specific)
│   │   │   └── references/                   # Documentation (skill-specific)
│   │   │
│   │   └── spec-workflow-orchestrator/       # Planning Skill
│   │       ├── SKILL.md                      # Orchestrator (required)
│   │       ├── reference.md                  # Documentation (optional)
│   │       ├── examples.md                   # Examples (optional)
│   │       └── docs/reference/               # Archived docs (optional)
│   │           └── spec-orchestrator-original.md
│   │
│   ├── commands/                             # Slash commands
│   │   ├── plan-feature.md
│   │   ├── project-status.md
│   │   ├── research-topic.md
│   │   └── verify-structure.md
│   │
│   ├── hooks/                                # Hook scripts
│   │   ├── post-tool-use-track-research.py  # Research phase tracking, quality gate validation
│   │   ├── session-end.py                   # Session cleanup, finalize state
│   │   ├── session-start.py                 # Auto-reindex (smart, 60-min cooldown), session logging, prerequisites check
│   │   ├── stop.py                          # Skill completion detection, duration tracking
│   │   └── user-prompt-submit.py            # Universal skill activation (3 skills), conditional enforcement, compound detection
│   │
│   └── utils/                                # Utility modules
│       ├── config_loader.py
│       ├── session_logger.py
│       └── state_manager.py
│
├── docs/
│   ├── status/                               # Status & review documents
│   │   ├── AUTO-VENV-IMPLEMENTED.md
│   │   ├── COMPLIANCE-ACHIEVED.md
│   │   ├── HONEST_REVIEW.md
│   │   ├── PRODUCTION_READY_SUMMARY.md
│   │   ├── SKILL-FIXES-APPLIED.md
│   │   └── SKILL-REVIEW-FINAL.md
│   │
│   ├── architecture/                         # Architecture documentation
│   │   ├── SKILL_USAGE_DECISION_TREE.md
│   │   └── STRUCTURE_ALIGNMENT.md
│   │
│   ├── implementation/                       # Implementation notes
│   │   ├── semantic-search-logging-integration.md
│   │   ├── semantic-search-skill-agent-architecture-fix.md
│   │   ├── bash-command-errors-and-fixes.md
│   │   ├── semantic-search-folder-reorganization-analysis.md
│   │   └── comprehensive-architecture-audit-20251201.md
│   │
│   ├── plans/                                # Planning documents (gitignored)
│   │   ├── completed/                        # Phase 2 complete
│   │   │   ├── FOCUSED_IMPLEMENTATION_PLAN.md
│   │   │   ├── SPEC_ORCHESTRATOR_TO_SKILL_MAPPING.md
│   │   │   └── CONTENT_MERGE_ANALYSIS.md
│   │   └── archive/                          # Old verbose plans
│   │       ├── Spec_Workflow_Implementation_Plan_FINAL_v2.0.md
│   │       ├── COMPLETE_PHASES_3_TO_7.md
│   │       ├── PHASES_6_AND_7_FINAL.md
│   │       └── Spec_Workflow_Implementation_Plan_v2.0_MERGED.md
│   │
│   ├── analysis/                             # Analysis documents (gitignored)
│   │   ├── Spec_Workflow_Implementation_Guide_20251119-002049.md
│   │   ├── Conversion_of_Spec_Workflow_System_to_Skill-Based_Architecture_Analysis_20251119-002049.md
│   │   ├── Inspirational_Projects_Analysis_and_Architecture_Recommendations_20251119.md
│   │   └── Plan_Dependency_Analysis_Ultra_Deep.md
│   │
│   └── adrs/                                 # Architecture Decision Records (NOT gitignored)
│       └── (empty - for future project ADRs)
│
├── files/
│   ├── research_notes/                       # Researcher agent outputs (gitignored)
│   │   ├── README.md                         # Placeholder only
│   │   └── *.md                              # Individual research notes
│   └── reports/                              # Synthesized research reports (gitignored)
│       ├── README.md                         # Placeholder only
│       └── *.md                              # Final reports
│
├── logs/                                     # ALL session logs (gitignored, 2,700+ files)
│   ├── session_*_transcript.txt
│   ├── session_*_tool_calls.jsonl
│   └── state/                                # Runtime state (gitignored)
│       ├── current.json                      # Current skill/session state
│       ├── research-workflow-state.json      # Research workflow tracking
│       └── spec-workflow-state.json          # Planning workflow tracking
│
├── scripts/                                  # Project-level scripts
│   └── deploy-semantic-search.sh             # Skill deployment script
│
├── .gitignore                                # Privacy & logs configuration
├── CHANGELOG.md                              # Project changelog
├── PROJECT_STRUCTURE.md                      # This file (structure documentation)
└── README.md                                 # Project overview
```

---

## ⭐ Agents Summary (7 Total)

**Location**: `.claude/agents/` (All agents in centralized registry)

### Research Skill (2 agents)
- **researcher.md** - Web research agent (WebSearch, Write, Read)
- **report-writer.md** - Synthesis agent (Read, Glob, Write)

### Semantic Search Skill (2 agents)
- **semantic-search-reader.md** - READ operations (search, find-similar, list-projects)
- **semantic-search-indexer.md** - WRITE operations (index, status)

### Planning Skill (3 agents)
- **spec-analyst.md** - Requirements gathering & analysis
- **spec-architect.md** - Architecture design & ADR creation
- **spec-planner.md** - Task breakdown & risk assessment

---

## File Organization Rules

### 1. Skills Directory

**Location**: `.claude/skills/{skill-name}/`

**Required Files**:
- `SKILL.md` - Orchestration logic (frontmatter with name, description, allowed-tools)
- Optional: `docs/reference/` for archived documentation
- Optional: `reference.md`, `examples.md` for skill documentation

**Note**: Agents are stored in `.claude/agents/`, NOT in skill subdirectories

**Pattern**:
```
.claude/skills/my-skill/
├── SKILL.md                  # Orchestration logic (required)
├── reference.md              # Optional documentation
├── examples.md               # Optional examples
└── docs/reference/           # Optional archived docs
    └── archived-source.md
```

---

### 2. Logs and State Directory

**Location**: `./logs/` (project root)

**Configuration**: `.claude/config.json` line 5: `"logs": "logs"`

**Content**:
- All session logs (transcript.txt, tool_calls.jsonl) - 2,700+ files
- Runtime state in `logs/state/` subdirectory:
  - `current.json` - Current skill/session state
  - `research-workflow-state.json` - Research workflow tracking
  - `spec-workflow-state.json` - Planning workflow tracking

**Rules**:
- NEVER create logs subdirectories elsewhere. All logs consolidated here.
- State was moved from `.claude/state/` to `logs/state/` (following best practices)
- All state files are gitignored (runtime-generated)

---

### 3. Documentation Directory

**docs/status/** (tracked - status & review documents):
- Project status documents (AUTO-VENV-IMPLEMENTED.md, COMPLIANCE-ACHIEVED.md, etc.)
- Review documents (HONEST_REVIEW.md, SKILL-REVIEW-FINAL.md, etc.)
- Moved from project root for cleaner organization

**docs/architecture/** (tracked - architecture documentation):
- SKILL_USAGE_DECISION_TREE.md - Skill activation decision flow
- STRUCTURE_ALIGNMENT.md - Structure alignment documentation
- Moved from `.claude/` for better organization

**docs/implementation/** (tracked - implementation notes):
- Detailed implementation notes for features and fixes
- Architecture decisions and analysis
- Migration guides and audit reports

**docs/plans/** (gitignored - private planning):
- `completed/` - Finished implementation plans
- `archive/` - Old/superseded plans

**docs/analysis/** (gitignored - private analysis):
- Research and analysis documents

**docs/adrs/** (NOT gitignored - project ADRs):
- Architecture Decision Records for project itself

---

### 4. Research Outputs

**files/research_notes/** (gitignored):
- Individual researcher agent outputs (one file per subtopic)
- Format: `{subtopic-slug}.md`

**files/reports/** (gitignored):
- Synthesized research reports from report-writer agent
- Format: `{topic-slug}_{timestamp}.md`

---

## Path References

### ✅ CORRECT (Relative/Dynamic):

```markdown
# In SKILL.md
subagent_type: "spec-analyst"
prompt: "Save to: docs/planning/requirements.md"

# In config.json
{
  "paths": {
    "logs": "logs",
    "reports": "files/reports"
  }
}

# In documentation
See `.claude/skills/spec-workflow-orchestrator/SKILL.md`
```

### ❌ INCORRECT (Absolute paths):

```markdown
# NEVER do this
subagent_type: "spec-analyst"
prompt: "Save to: /Users/username/projects/.../docs/planning/requirements.md"
```

**Note**: Always use relative paths from project root, not absolute paths.

---

## Verification Commands

Check for absolute paths in active files:
```bash
# Skills
grep -r "/Users/" .claude/skills/spec-workflow-orchestrator/ --include="*.md" --include="*.json"

# Should return nothing (or only archived docs)
```

Verify logs location:
```bash
# Should show only one logs directory
find . -type d -name "logs" | grep -v node_modules | grep -v ".git"
# Output: ./logs
```

Check file organization:
```bash
# Plans should be in completed/ or archive/
ls docs/plans/
# Output: completed/  archive/

# No loose files in docs/plans/ root
```

---

## Phase 2 Completion Status

✅ **Phase 0**: Privacy & Pre-Flight (5 tasks)
✅ **Phase 1**: Infrastructure Setup (6 tasks)
✅ **Phase 2**: SKILL.md Implementation (5 tasks)

**Deliverables**:
- spec-workflow-orchestrator skill (planning-only, 3 agents)
- Battle-tested content merged from spec-orchestrator.md
- Project-agnostic prompt templates
- Proper file organization and log consolidation

**Tagged**:
- `spec-workflow-v1.0-phase-0-complete`
- `spec-workflow-v1.0-phase-1-complete`
- Phase 2 tag pending final review

---

## Maintenance

When adding new files:
1. Follow the structure above
2. Use relative paths only (no `/Users/...`)
3. Put logs in `./logs` (configured in .claude/config.json)
4. Skills go in `.claude/skills/{skill-name}/`
5. Completed plans move to `docs/plans/completed/`

When refactoring:
1. Check all file references are relative
2. Update this document if structure changes
3. Verify logs still go to `./logs`
4. Keep skills self-contained in their folders
