#!/usr/bin/env python3
"""
Shared fixtures and utilities for skill tests.

This module provides common test fixtures for testing the three specialized skills:
- multi-agent-researcher
- spec-workflow-orchestrator
- semantic-search
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create basic project structure
    (project_dir / "src").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "docs").mkdir()

    # Create some sample files
    (project_dir / "src" / "main.py").write_text("def main():\n    pass\n")
    (project_dir / "README.md").write_text("# Test Project\n")

    return project_dir


@pytest.fixture
def mock_skill_metadata() -> Dict[str, Dict[str, Any]]:
    """Provide metadata for all three skills."""
    return {
        "multi-agent-researcher": {
            "name": "multi-agent-researcher",
            "version": "2.1.2",
            "allowed_tools": ["Task", "Read", "Glob", "TodoWrite"],
            "excluded_tools": ["Write"],  # Enforced architectural constraint
        },
        "spec-workflow-orchestrator": {
            "name": "spec-workflow-orchestrator",
            "version": "1.0.0",
            "allowed_tools": ["Task", "Read", "Glob", "TodoWrite", "Write", "Edit"],
        },
        "semantic-search": {
            "name": "semantic-search",
            "version": "3.0.0",
            "allowed_tools": ["Bash", "Read", "Glob", "Grep"],
        }
    }


@pytest.fixture
def research_notes_dir(tmp_path):
    """Create a temporary directory for research notes."""
    notes_dir = tmp_path / "files" / "research_notes"
    notes_dir.mkdir(parents=True)
    return notes_dir


@pytest.fixture
def reports_dir(tmp_path):
    """Create a temporary directory for research reports."""
    reports_dir = tmp_path / "files" / "reports"
    reports_dir.mkdir(parents=True)
    return reports_dir


@pytest.fixture
def planning_dir(tmp_path):
    """Create a temporary directory for planning outputs."""
    project_dir = tmp_path / "docs" / "projects" / "test-project"
    planning_dir = project_dir / "planning"
    adrs_dir = project_dir / "adrs"

    planning_dir.mkdir(parents=True)
    adrs_dir.mkdir(parents=True)

    return {
        "project": project_dir,
        "planning": planning_dir,
        "adrs": adrs_dir
    }


@pytest.fixture
def sample_research_notes(research_notes_dir):
    """Create sample research notes for testing synthesis."""
    notes = [
        ("subtopic-1-foundations.md", "# Theoretical Foundations\n\nKey findings:\n- Finding 1\n- Finding 2\n"),
        ("subtopic-2-implementations.md", "# Current Implementations\n\nSurvey results:\n- Implementation A\n- Implementation B\n"),
        ("subtopic-3-future.md", "# Future Directions\n\nEmerging trends:\n- Trend 1\n- Trend 2\n"),
    ]

    for filename, content in notes:
        (research_notes_dir / filename).write_text(content)

    return research_notes_dir


@pytest.fixture
def sample_planning_artifacts(planning_dir):
    """Create sample planning artifacts for testing."""
    planning = planning_dir["planning"]
    adrs = planning_dir["adrs"]

    # Create requirements.md
    (planning / "requirements.md").write_text("""# Requirements

## Functional Requirements
- FR1: User registration
- FR2: Task creation

## Non-Functional Requirements
- NFR1: Response time < 200ms
""")

    # Create architecture.md
    (planning / "architecture.md").write_text("""# Architecture

## Technology Stack
- Frontend: React
- Backend: Node.js
- Database: PostgreSQL
""")

    # Create tasks.md
    (planning / "tasks.md").write_text("""# Implementation Tasks

## Phase 1
- T1.1: Setup project (2h)
- T1.2: Create database schema (3h)
""")

    # Create sample ADR
    (adrs / "ADR-001-technology-stack.md").write_text("""# ADR 001: Technology Stack

## Status: Accepted

## Context
Need to choose technology stack.

## Decision
Use MERN stack.

## Rationale
Team expertise, mature ecosystem.
""")

    return planning_dir


def assert_file_exists(file_path: Path, message: str = None):
    """Helper assertion to check file exists with custom message."""
    if not file_path.exists():
        msg = message or f"Expected file does not exist: {file_path}"
        raise AssertionError(msg)


def assert_file_contains(file_path: Path, expected_content: str, message: str = None):
    """Helper assertion to check file contains expected content."""
    if not file_path.exists():
        raise AssertionError(f"File does not exist: {file_path}")

    content = file_path.read_text()
    if expected_content not in content:
        msg = message or f"Expected content not found in {file_path}"
        raise AssertionError(msg)


def count_files_in_dir(directory: Path, pattern: str = "*") -> int:
    """Count files matching pattern in directory."""
    return len(list(directory.glob(pattern)))
