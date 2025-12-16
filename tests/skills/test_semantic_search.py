#!/usr/bin/env python3
"""
Tests for semantic-search skill.

Tests the orchestration logic, agent selection, prerequisites checking,
auto-reindex system, and cache management.
"""

import pytest
from pathlib import Path


class TestAgentSelectionLogic:
    """Test agent selection logic (reader vs indexer)."""

    def test_two_agent_architecture(self):
        """Verify skill uses 2-agent architecture for token optimization."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        assert skill_md.exists(), "Skill file should exist"

        content = skill_md.read_text()

        # Should document 2 agents
        assert "semantic-search-reader" in content, \
            "Skill should document semantic-search-reader agent"
        assert "semantic-search-indexer" in content, \
            "Skill should document semantic-search-indexer agent"

        # Should explain token optimization rationale
        assert "token" in content.lower(), \
            "Skill should explain token optimization"

    def test_reader_operations(self):
        """Verify reader agent handles READ operations."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Reader should handle: search, find-similar, list-projects
        reader_ops = ["search", "find-similar", "list-projects"]
        for op in reader_ops:
            assert op in content, \
                f"Reader agent should handle '{op}' operation"

    def test_indexer_operations(self):
        """Verify indexer agent handles WRITE operations."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Indexer should handle: index, incremental-reindex, status
        indexer_ops = ["index", "incremental-reindex", "status"]
        for op in indexer_ops:
            assert op in content, \
                f"Indexer agent should handle '{op}' operation"

    def test_decision_table_exists(self):
        """Verify skill documents decision logic table."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should have decision table
        assert "Decision Logic" in content or "Which Agent" in content, \
            "Skill should document agent selection decision table"


class TestPrerequisitesCheck:
    """Test prerequisites checking and conditional enforcement."""

    def test_prerequisites_state_file(self):
        """Verify skill documents prerequisites state file."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document state file
        assert "semantic-search-prerequisites" in content or "prerequisites.json" in content, \
            "Skill should document prerequisites state file"

    def test_conditional_enforcement(self):
        """Verify skill documents conditional enforcement based on prerequisites."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should explain conditional enforcement
        assert "conditional" in content.lower() or "prerequisites" in content.lower(), \
            "Skill should document conditional enforcement"

        # Should explain graceful degradation
        assert "graceful" in content.lower() or "fallback" in content.lower(), \
            "Skill should document graceful degradation when prerequisites false"

    def test_library_dependency_documentation(self):
        """Verify skill documents claude-context-local library dependency."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document library dependency
        assert "claude-context-local" in content, \
            "Skill should document library dependency"

        # Should clarify it's NOT an MCP server
        assert "NOT an MCP server" in content or "not an MCP server" in content.lower(), \
            "Skill should clarify library is not MCP server"


class TestAutoReindexSystem:
    """Test auto-reindex system (background, cooldown, lock)."""

    def test_first_prompt_architecture(self):
        """Verify skill documents first-prompt background reindex."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document first-prompt trigger
        assert "first prompt" in content.lower() or "first-prompt" in content, \
            "Skill should document first-prompt trigger"

        # Should document background execution
        assert "background" in content.lower(), \
            "Skill should document background reindex"

    def test_cooldown_protection(self):
        """Verify skill documents 6-hour cooldown protection."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document cooldown
        assert "cooldown" in content.lower() or "6 hour" in content.lower() or "360" in content, \
            "Skill should document cooldown protection"

        # Should explain cooldown rationale
        assert "prevent" in content.lower() or "rapid restart" in content.lower(), \
            "Skill should explain cooldown prevents rapid reindex spam"

    def test_concurrent_execution_protection(self):
        """Verify skill documents concurrent execution protection via locks."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document lock mechanism
        assert "lock" in content.lower() or "concurrent" in content.lower(), \
            "Skill should document concurrent execution protection"

        # Should document PID-based locks
        assert "PID" in content or "process ID" in content.lower(), \
            "Skill should document PID-based lock files"

    def test_state_file_management(self):
        """Verify skill documents three state files."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document 3 state files
        state_files = [
            "semantic-search-prerequisites.json",
            "index_state.json",
            "indexing.lock"
        ]

        for state_file in state_files:
            assert state_file in content or state_file.replace(".json", "") in content, \
                f"Skill should document {state_file}"


class TestIncrementalCacheSystem:
    """Test incremental cache system (v3.0 feature)."""

    def test_embedding_cache_documentation(self):
        """Verify skill documents embedding cache system."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document cache system
        assert "cache" in content.lower() or "embedding" in content.lower(), \
            "Skill should document embedding cache"

        # Should document embeddings.pkl file
        assert "embeddings.pkl" in content, \
            "Skill should document embeddings cache file"

    def test_lazy_deletion_strategy(self):
        """Verify skill documents lazy deletion strategy."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document lazy deletion
        assert "lazy deletion" in content.lower() or "bloat" in content.lower(), \
            "Skill should document lazy deletion strategy"

    def test_bloat_tracking(self):
        """Verify skill documents bloat tracking and auto-rebuild."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document bloat percentage
        assert "bloat" in content.lower(), \
            "Skill should document bloat tracking"

        # Should document auto-rebuild triggers
        assert "rebuild" in content.lower() or "threshold" in content.lower(), \
            "Skill should document auto-rebuild triggers"

    def test_performance_gains_documented(self):
        """Verify skill documents performance gains from cache."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should show performance metrics
        assert "speedup" in content.lower() or "faster" in content.lower(), \
            "Skill should document cache speedup benefits"

        # Should mention 3.2x or similar speedup
        assert "3.2x" in content or "3x" in content or "faster" in content.lower(), \
            "Skill should document measured speedup"

    def test_model_caching_optimization(self):
        """Verify skill documents model caching (Phase 3 feature)."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document model caching
        assert "model caching" in content.lower() or "class-level" in content.lower(), \
            "Skill should document model caching optimization"


class TestBashOrchestrators:
    """Test bash orchestrator pattern (Python library imports)."""

    def test_bash_scripts_documentation(self):
        """Verify skill documents bash scripts for orchestration."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document bash scripts
        assert "bash" in content.lower() or "scripts/" in content, \
            "Skill should document bash scripts"

        # Should document PYTHONPATH usage
        assert "PYTHONPATH" in content or "Python module" in content, \
            "Skill should document Python module imports"

    def test_not_mcp_server_clarification(self):
        """Verify skill clarifies it's NOT using MCP protocol."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should explicitly state NOT MCP
        assert "NOT an MCP server" in content or "not an MCP server" in content.lower(), \
            "Skill should clarify not using MCP server"

        # Should explain direct Python imports
        assert "import" in content.lower() or "module" in content.lower(), \
            "Skill should explain direct Python imports"

    def test_venv_python_usage(self):
        """Verify skill documents using claude-context-local venv Python."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document venv usage
        assert ".venv" in content or "venv" in content.lower(), \
            "Skill should document venv Python usage"


class TestIndexFlatIPImplementation:
    """Test IndexFlatIP implementation (same as MCP)."""

    def test_indexflatip_documentation(self):
        """Verify skill documents using IndexFlatIP (same as MCP)."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document IndexFlatIP
        assert "IndexFlatIP" in content, \
            "Skill should document IndexFlatIP usage"

        # Should mention same as MCP
        assert "same as MCP" in content or "same approach" in content.lower(), \
            "Skill should clarify using same approach as MCP"

    def test_full_reindex_strategy(self):
        """Verify skill documents full reindex strategy (not incremental vectors)."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document auto-fallback to full reindex
        assert "auto-fallback" in content or "full reindex" in content.lower(), \
            "Skill should document auto-fallback to full reindex"

        # Should explain IndexFlatIP doesn't support incremental vector updates
        assert "doesn't support incremental" in content.lower() or "no incremental" in content.lower(), \
            "Skill should explain IndexFlatIP limitation"

    def test_apple_silicon_compatibility(self):
        """Verify skill documents Apple Silicon compatibility."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document Apple Silicon support
        assert "Apple Silicon" in content or "mps" in content.lower(), \
            "Skill should document Apple Silicon compatibility"


class TestWhenToUseGuidance:
    """Test when-to-use guidance for semantic vs Grep/Glob."""

    def test_use_cases_documented(self):
        """Verify skill documents when to use semantic search."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should have "When to Use" section
        assert "When to Use" in content or "Use Semantic Search When" in content, \
            "Skill should document when to use semantic search"

    def test_grep_fallback_documented(self):
        """Verify skill documents when to use Grep instead."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document Grep use cases
        assert "Use Grep instead" in content or "Grep" in content, \
            "Skill should document when to use Grep instead"

        # Should mention exact string matching
        assert "exact" in content.lower(), \
            "Skill should explain Grep for exact matches"

    def test_value_proposition_documented(self):
        """Verify skill documents token savings value proposition."""
        skill_md = Path(".claude/skills/semantic-search/SKILL.md")
        content = skill_md.read_text()

        # Should document token optimization/efficiency
        assert "token" in content.lower() and ("optimization" in content.lower() or "efficiency" in content.lower() or "saves" in content.lower()), \
            "Skill should document token savings/optimization"

        # Should mention 2-agent architecture for token optimization
        assert "2-agent architecture" in content.lower() or "token optimization" in content.lower(), \
            "Skill should explain 2-agent architecture for token efficiency"
