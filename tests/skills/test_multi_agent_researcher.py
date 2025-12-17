#!/usr/bin/env python3
"""
Tests for multi-agent-researcher skill.

Tests the orchestration logic, parallel spawning, mandatory delegation,
and file organization for the research workflow.
"""

import pytest
from pathlib import Path


class TestQueryDecomposition:
    """Test query analysis and subtopic decomposition logic."""

    def test_decomposition_patterns_exist(self):
        """Verify skill documentation defines decomposition patterns."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        assert skill_md.exists(), "Skill file should exist"

        content = skill_md.read_text()

        # Check for documented decomposition patterns
        patterns = ["Temporal", "Categorical", "Stakeholder", "Problem-Solution", "Geographic"]
        for pattern in patterns:
            assert pattern in content, f"Decomposition pattern '{pattern}' should be documented"

    def test_subtopic_count_guidance(self):
        """Verify skill enforces 2-4 subtopic range."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document 2-4 subtopic guidance
        assert "2-4" in content or "2-4 subtopics" in content.lower(), \
            "Skill should recommend 2-4 subtopics"

        # Should warn against too many or too few
        assert "Too many" in content or "Too few" in content, \
            "Skill should document anti-patterns for subtopic count"


class TestParallelExecution:
    """Test parallel researcher spawning requirements."""

    def test_parallel_spawning_requirement(self):
        """Verify skill mandates parallel spawning (not sequential)."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should explicitly require parallel spawning
        assert "parallel" in content.lower(), \
            "Skill should document parallel spawning requirement"

        # Should warn against sequential
        assert "not sequential" in content.lower() or "never sequential" in content.lower(), \
            "Skill should warn against sequential spawning"

    def test_task_tool_usage_for_spawning(self):
        """Verify skill uses Task tool for agent spawning."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document Task tool usage
        assert "Task tool" in content or "Task(" in content, \
            "Skill should document using Task tool for spawning"

        # Should specify subagent_type
        assert "researcher" in content.lower(), \
            "Skill should specify 'researcher' subagent type"


class TestResearchNotesVerification:
    """Test research notes verification before synthesis."""

    def test_glob_verification_before_synthesis(self, research_notes_dir):
        """Verify skill requires Glob check before synthesis."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should require verification step
        assert "Verify" in content or "confirm" in content.lower(), \
            "Skill should require verification of research notes"

        # Should use Glob tool
        assert "Glob" in content, \
            "Skill should document using Glob to verify notes exist"

    def test_research_notes_directory_structure(self, research_notes_dir):
        """Verify research notes are saved to correct directory."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document file path pattern
        assert "research_notes" in content or "research notes" in content.lower(), \
            "Skill should document research_notes directory"

        # Should show markdown format
        assert ".md" in content, \
            "Skill should document markdown format for notes"


class TestReportWriterDelegation:
    """Test mandatory report-writer agent delegation."""

    def test_write_tool_excluded(self):
        """Verify Write tool is excluded from allowed-tools."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Check frontmatter for allowed-tools
        lines = content.split("\n")
        in_frontmatter = False
        allowed_tools_found = False

        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    break  # End of frontmatter
            elif in_frontmatter and "allowed-tools:" in line.lower():
                allowed_tools_found = True
                # Extract tools list
                tools_text = line.split("allowed-tools:", 1)[1] if ":" in line else ""
                # Split by comma and strip whitespace
                tools_list = [t.strip() for t in tools_text.split(",")]

                # Write should NOT be in allowed-tools list (but TodoWrite is OK)
                assert "Write" not in tools_list, \
                    f"Write tool should be excluded from allowed-tools (found: {tools_list})"
                break

        assert allowed_tools_found, "Skill should have allowed-tools frontmatter"

    def test_report_writer_mandatory(self):
        """Verify skill mandates report-writer agent delegation."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should explicitly state report-writer is MANDATORY
        assert "MANDATORY" in content or "mandatory" in content.lower(), \
            "Skill should mark report-writer delegation as mandatory"

        # Should document report-writer subagent type
        assert "report-writer" in content, \
            "Skill should specify 'report-writer' subagent type"

    def test_synthesis_delegation_enforcement(self):
        """Verify skill enforces delegation (not self-synthesis)."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should warn against doing synthesis yourself
        assert "CANNOT" in content or "DO NOT" in content, \
            "Skill should explicitly prohibit self-synthesis"

        # Should document architectural constraint
        assert "allowed-tools" in content.lower(), \
            "Skill should reference allowed-tools enforcement"


class TestFileOrganization:
    """Test file organization and directory structure."""

    def test_research_notes_location(self, research_notes_dir):
        """Verify research notes are saved to files/research_notes/."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document research_notes directory
        assert "files/research_notes" in content or "research_notes/" in content, \
            "Skill should document research_notes directory path"

    def test_reports_location(self):
        """Verify reports are saved to files/reports/."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document reports directory
        assert "files/reports" in content or "reports/" in content, \
            "Skill should document reports directory path"

    def test_timestamp_in_report_filename(self):
        """Verify report filenames include timestamp."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document timestamp format in filename
        assert "timestamp" in content.lower(), \
            "Skill should document timestamp in report filename"

        # Should show date command or similar
        assert "date" in content.lower(), \
            "Skill should show how to generate timestamp"


class TestTodoWriteIntegration:
    """Test TodoWrite tool integration for tracking progress."""

    def test_todowrite_in_allowed_tools(self):
        """Verify TodoWrite is in allowed-tools."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
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

    def test_todowrite_workflow_documentation(self):
        """Verify skill documents TodoWrite usage in workflow."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should document TodoWrite usage
        assert "TodoWrite" in content, \
            "Skill should document TodoWrite for tracking"

        # Should show example task list structure
        assert "[ ]" in content or "- [ ]" in content, \
            "Skill should show checklist format for TodoWrite"


class TestErrorHandling:
    """Test error handling patterns documented in skill."""

    def test_researcher_failure_handling(self):
        """Verify skill documents how to handle researcher failures."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should have Error Handling section
        assert "Error Handling" in content or "error handling" in content.lower(), \
            "Skill should document error handling"

        # Should address researcher failures
        assert "fail" in content.lower(), \
            "Skill should document handling researcher failures"

    def test_partial_results_handling(self):
        """Verify skill documents handling partial results."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should address partial results
        assert "partial" in content.lower(), \
            "Skill should document handling partial results"

    def test_contradictory_findings_handling(self):
        """Verify skill documents handling contradictory findings."""
        skill_md = Path(".claude/skills/multi-agent-researcher/SKILL.md")
        content = skill_md.read_text()

        # Should address contradictions
        assert "contradict" in content.lower(), \
            "Skill should document handling contradictory findings"
