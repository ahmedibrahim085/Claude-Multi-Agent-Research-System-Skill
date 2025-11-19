# Project Structure

**Last Updated**: 2025-11-19
**Status**: Phase 2 Complete

This document describes the canonical file organization for the Claude Multi-Agent Research System project.

## Core Principles

1. **No Absolute Paths**: All file references use relative/dynamic paths
2. **Logs Consolidated**: All session logs in `./logs` (configured in `.claude/config.json`)
3. **Skills Self-Contained**: Each skill has agents/, docs/ subdirectories within skill folder
4. **Planning Documents Organized**: Active plans vs. completed vs. archived

---

## Directory Structure

```
.
├── .claude/
│   ├── config.json                    # Project configuration (logs path, research settings)
│   ├── CLAUDE.md                      # Project-specific instructions
│   └── skills/
│       ├── skill-rules.json           # Skill activation rules (both skills)
│       ├── multi-agent-researcher/    # Research orchestration skill
│       │   ├── SKILL.md               # Orchestrator logic
│       │   ├── agents/
│       │   │   ├── researcher.md      # Web research agent
│       │   │   └── report-writer.md   # Synthesis agent
│       │   └── README.md
│       └── spec-workflow-orchestrator/ # Planning workflow skill ✨ NEW
│           ├── SKILL.md                # Orchestrator logic
│           ├── agents/
│           │   ├── spec-analyst.md     # Requirements analysis
│           │   ├── spec-architect.md   # Architecture design
│           │   └── spec-planner.md     # Task breakdown
│           └── docs/reference/
│               ├── README.md
│               └── spec-orchestrator-original.md  # Archived reference
│
├── docs/
│   ├── plans/                         # Planning documents (gitignored)
│   │   ├── completed/                 # Phase 2 complete
│   │   │   ├── FOCUSED_IMPLEMENTATION_PLAN.md
│   │   │   ├── SPEC_ORCHESTRATOR_TO_SKILL_MAPPING.md
│   │   │   └── CONTENT_MERGE_ANALYSIS.md
│   │   └── archive/                   # Old verbose plans
│   │       ├── Spec_Workflow_Implementation_Plan_FINAL_v2.0.md
│   │       └── ...
│   ├── analysis/                      # Analysis documents (gitignored)
│   └── adrs/                          # Architecture Decision Records (NOT gitignored)
│
├── files/
│   ├── research_notes/                # Researcher agent outputs (gitignored)
│   └── reports/                       # Synthesized research reports (gitignored)
│
├── logs/                              # ALL session logs (gitignored, 1,700+ files)
│
├── .gitignore                         # Defines what's tracked vs. private
├── PROJECT_STRUCTURE.md               # This file
└── README.md                          # Project overview

```

---

## File Organization Rules

### 1. Skills Directory

**Location**: `.claude/skills/{skill-name}/`

**Required Files**:
- `SKILL.md` - Orchestration logic (frontmatter with name, description, allowed-tools)
- `agents/*.md` - Spawnable agent files (frontmatter with name, tools, model)
- Optional: `docs/reference/` for archived documentation

**Pattern**:
```
.claude/skills/my-skill/
├── SKILL.md
├── agents/
│   ├── agent-one.md
│   └── agent-two.md
└── docs/reference/  # Optional
    └── archived-source.md
```

---

### 2. Logs Directory

**Location**: `./logs/` (project root)

**Configuration**: `.claude/config.json` line 5: `"logs": "logs"`

**Content**: All session logs (transcript.txt, tool_calls.jsonl)

**Rule**: NEVER create logs subdirectories elsewhere. All logs consolidated here.

---

### 3. Documentation Directory

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
prompt: "Save to: /Users/ahmedmaged/ai_storage/projects/.../docs/planning/requirements.md"
```

**Exception**: Archived historical planning documents may contain absolute paths as historical record of commands executed.

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
