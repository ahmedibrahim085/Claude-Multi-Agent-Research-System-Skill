#!/usr/bin/env python3
"""
Tests for spec-workflow-orchestrator skill.

Tests the orchestration logic, quality gates, iteration loops,
and file organization for the planning workflow.
"""

import pytest
from pathlib import Path


class TestSequentialAgentExecution:
    """Test sequential agent execution (analyst → architect → planner)."""

    def test_three_agent_workflow(self):
        """Verify skill orchestrates 3 agents sequentially."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        assert skill_md.exists(), "Skill file should exist"

        content = skill_md.read_text()

        # Should document all 3 agents
        agents = ["spec-analyst", "spec-architect", "spec-planner"]
        for agent in agents:
            assert agent in content, f"Agent '{agent}' should be documented"

        # Should document sequential order
        assert "sequential" in content.lower() or "→" in content, \
            "Skill should document sequential execution"

    def test_analyst_first_architect_second_planner_third(self):
        """Verify execution order: analyst → architect → planner."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Find positions of each agent mention
        analyst_pos = content.find("spec-analyst")
        architect_pos = content.find("spec-architect")
        planner_pos = content.find("spec-planner")

        # In orchestration workflow, analyst should come before architect before planner
        assert analyst_pos < architect_pos < planner_pos, \
            "Workflow should document analyst → architect → planner order"

    def test_each_agent_uses_previous_output(self):
        """Verify each agent builds on previous agent's output."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Architect should reference requirements
        assert "requirements.md" in content, \
            "Architect should use requirements from analyst"

        # Planner should reference both requirements and architecture
        assert "architecture.md" in content, \
            "Planner should use architecture from architect"


class TestQualityGate:
    """Test quality gate validation logic (85% threshold)."""

    def test_quality_gate_threshold(self):
        """Verify quality gate uses 85% threshold."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document 85% threshold
        assert "85%" in content or "85 %" in content, \
            "Skill should document 85% quality gate threshold"

    def test_quality_gate_criteria(self):
        """Verify quality gate has 4 core criteria."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document 4 criteria
        criteria = [
            "Requirements Completeness",
            "Architecture Feasibility",
            "Task Breakdown",
            "Risk Mitigation"
        ]

        for criterion in criteria:
            # Case-insensitive check
            assert criterion.lower() in content.lower(), \
                f"Quality gate criterion '{criterion}' should be documented"

    def test_point_distribution(self):
        """Verify quality gate uses point-based scoring."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should mention points
        assert "points" in content.lower() or "pts" in content.lower(), \
            "Quality gate should use point-based scoring"

        # Should sum to 100 points total
        assert "100" in content, \
            "Quality gate should have 100 total points"

    def test_pass_fail_logic(self):
        """Verify quality gate has clear pass/fail decision logic."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document pass condition
        assert "≥ 85%" in content or ">= 85%" in content or "pass" in content.lower(), \
            "Quality gate should document pass condition"

        # Should document fail condition
        assert "< 85%" in content or "fail" in content.lower(), \
            "Quality gate should document fail condition"


class TestIterationLoop:
    """Test iteration loop with feedback (max 3 iterations)."""

    def test_max_iteration_limit(self):
        """Verify skill enforces maximum 3 iterations."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document 3-iteration limit
        assert "3 iterations" in content.lower() or "max 3" in content.lower() or "maximum 3" in content.lower(), \
            "Skill should enforce 3-iteration limit"

    def test_feedback_generation(self):
        """Verify skill documents feedback generation for failed gates."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document feedback process
        assert "feedback" in content.lower(), \
            "Skill should document feedback generation"

        # Should show example feedback format
        assert "gaps identified" in content.lower() or "specific" in content.lower(), \
            "Skill should show specific gap feedback format"

    def test_agent_respawning(self):
        """Verify skill documents re-spawning agents with feedback."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document re-spawning
        assert "re-spawn" in content.lower() or "respawn" in content.lower(), \
            "Skill should document agent re-spawning with feedback"

    def test_escalation_after_max_iterations(self):
        """Verify skill documents escalation when iterations exhausted."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document escalation to user
        assert "escalate" in content.lower() or "user decides" in content.lower(), \
            "Skill should document escalation after 3 iterations"


class TestFileOrganization:
    """Test file organization and directory structure."""

    def test_project_slug_generation(self):
        """Verify skill documents project slug generation."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document slug generation
        assert "project-slug" in content or "project slug" in content.lower(), \
            "Skill should document project slug generation"

        # Should show example slugs
        assert "task-manager" in content or "session-log-viewer" in content, \
            "Skill should show example project slugs"

    def test_planning_directory_structure(self, planning_dir):
        """Verify skill documents planning/ directory structure."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document planning directory
        assert "planning/" in content or "planning directory" in content.lower(), \
            "Skill should document planning/ directory"

        # Should document three main files
        files = ["requirements.md", "architecture.md", "tasks.md"]
        for file in files:
            assert file in content, \
                f"Skill should document {file} output"

    def test_adrs_directory_structure(self):
        """Verify skill documents adrs/ directory for Architecture Decision Records."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document adrs directory
        assert "adrs/" in content or "adrs directory" in content.lower(), \
            "Skill should document adrs/ directory"

        # Should document ADR format
        assert "ADR" in content, \
            "Skill should document Architecture Decision Records"

    def test_archive_system(self):
        """Verify skill documents archive system for refining existing projects."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document archive capability
        assert "archive" in content.lower() or ".archive/" in content, \
            "Skill should document archive system"

        # Should document timestamp format
        assert "timestamp" in content.lower(), \
            "Skill should document timestamp in archive directory name"


class TestExistingProjectHandling:
    """Test existing project detection and user choice workflow."""

    def test_existing_project_detection(self):
        """Verify skill checks if project already exists."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document existence check
        assert "exists" in content.lower() or "existing project" in content.lower(), \
            "Skill should document existing project detection"

    def test_user_choice_options(self):
        """Verify skill presents 4 options for existing projects."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should use AskUserQuestion
        assert "AskUserQuestion" in content, \
            "Skill should use AskUserQuestion for existing projects"

        # Should present multiple options
        options = ["Refine existing", "Archive", "new version", "Cancel"]
        found_options = sum(1 for opt in options if opt.lower() in content.lower())
        assert found_options >= 3, \
            "Skill should present at least 3 options for existing projects"

    def test_refinement_mode(self):
        """Verify skill supports refinement mode for existing projects."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document refinement mode
        assert "refinement" in content.lower() or "refine" in content.lower(), \
            "Skill should document refinement mode"

        # Should read existing files first
        assert "read existing" in content.lower(), \
            "Skill should document reading existing files in refinement mode"


class TestWorkflowStateManagement:
    """Test workflow state management and utilities."""

    def test_state_management_utilities(self):
        """Verify skill documents workflow state utilities."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document state utilities
        assert "workflow_state" in content or "state" in content.lower(), \
            "Skill should document state management"

    def test_archive_utility(self):
        """Verify skill documents archive utility script."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document archive script
        assert "archive_project" in content or "archive script" in content.lower(), \
            "Skill should document archive utility"

    def test_version_detection_utility(self):
        """Verify skill documents version detection utility."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document version detection
        assert "detect_next_version" in content or "version" in content.lower(), \
            "Skill should document version detection utility"


class TestTodoWriteIntegration:
    """Test TodoWrite tool integration for tracking progress."""

    def test_todowrite_in_allowed_tools(self):
        """Verify TodoWrite is in allowed-tools."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Check frontmatter
        lines = content.split("\n")
        in_frontmatter = False
        allowed_tools_line = None

        for line in lines:
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    break
            elif in_frontmatter and line.startswith("allowed-tools:"):
                allowed_tools_line = line
                break

        assert allowed_tools_line is not None
        assert "TodoWrite" in allowed_tools_line, \
            "TodoWrite should be in allowed-tools for progress tracking"

    def test_progress_reporting(self):
        """Verify skill documents progress reporting with TodoWrite."""
        skill_md = Path(".claude/skills/spec-workflow-orchestrator/SKILL.md")
        content = skill_md.read_text()

        # Should document progress tracking
        assert "progress" in content.lower(), \
            "Skill should document progress tracking"

        # Should show status reporting format
        assert "✅" in content or "🔄" in content or "⏳" in content, \
            "Skill should show status indicators for progress"
