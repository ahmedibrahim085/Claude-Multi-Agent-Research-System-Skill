---
description: Verify project structure aligns with official Claude Code standards
---

Please verify that the project structure follows official Claude Code architecture:

1. **Agent Registry** (.claude/agents/):
   - Check all 5 agents exist: spec-analyst, spec-architect, spec-planner, researcher, report-writer
   - Verify frontmatter format (name, description, tools only)
   - Confirm no agents in skill subdirectories

2. **Skills Directory** (.claude/skills/):
   - multi-agent-researcher: Check SKILL.md exists
   - spec-workflow-orchestrator: Check SKILL.md exists
   - Verify no nested agents/ directories

3. **Configuration Files**:
   - CLAUDE.md: Check orchestration rules
   - settings.json: Verify hooks configuration
   - config.json: Check paths configuration

4. **File Organization**:
   - logs/: All session logs consolidated
   - files/research_notes/: Research agent outputs
   - files/reports/: Synthesis reports
   - docs/plans/: Active planning documents

Report any deviations from official structure or broken references.
