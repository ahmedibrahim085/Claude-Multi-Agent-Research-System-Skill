# Archived Tests Migration Plan

**Created**: 2024-11-24
**Status**: ✅ COMPLETED (2024-11-24)
**Source**: `/Users/ahmedmaged/ai_storage/projects_docs_archives/Claude-Multi-Agent-Research-System-Skill_archive_20251120-113041/docs/testing/`

---

## Executive Summary

### Original (Incorrect) Assessment

> "Convert archived test documentation to executable tests"

### Corrected Assessment

**DO NOT convert archived docs to executable scripts.**

The archived test documentation is **test evidence for human evaluation** (Layer 3), not missing automation. Converting them to scripts would:
1. Create brittle, meaningless assertions
2. Fight the non-deterministic nature of AI agents
3. Provide false confidence without testing actual quality

---

## What Would Need Modification

### Phase 1: Preserve Manual Test Evidence (LOW EFFORT)

**Action**: Move archived docs to `tests/manual/` as reference documentation.

| Source File | Destination | Modification |
|-------------|-------------|--------------|
| `step-5.2-execution-test-results.md` | `tests/manual/skill-execution-tests.md` | Update paths to current structure |
| `step-5.3-edge-case-testing-summary.md` | `tests/manual/edge-case-tests.md` | Update paths to current structure |
| `phase-3-integration-test-report.md` | `tests/manual/integration-test-report.md` | Update paths to current structure |
| `edge-case-iteration-loop-test.md` | `tests/manual/iteration-loop-details.md` | None |
| `edge-case-missing-files-test.md` | `tests/manual/missing-files-details.md` | None |
| `edge-case-progress-tracking-test.md` | `tests/manual/progress-tracking-details.md` | None |

**New file to create**: `tests/manual/README.md` - Explains purpose and how to use

---

### Phase 2: Add Layer 2 Structural Tests (MEDIUM EFFORT)

These are NEW tests that validate automatable aspects not currently covered.

#### 2.1 Agent Structure Validation

**File**: `tests/test_agent_structure.sh`

**Purpose**: Verify agents exist and have valid structure (Layer 2 - Behavior)

```bash
#!/bin/bash
# Tests agent files exist and have required frontmatter

test_spec_analyst_exists() {
    [ -f ".claude/agents/spec-analyst.md" ]
}

test_spec_architect_exists() {
    [ -f ".claude/agents/spec-architect.md" ]
}

test_spec_planner_exists() {
    [ -f ".claude/agents/spec-planner.md" ]
}

test_researcher_exists() {
    [ -f ".claude/agents/researcher.md" ]
}

test_report_writer_exists() {
    [ -f ".claude/agents/report-writer.md" ]
}

test_agents_have_tools_frontmatter() {
    for agent in .claude/agents/*.md; do
        grep -q "^tools:" "$agent" || return 1
    done
}
```

**Why this is valid**: File existence and structure are deterministic - they either exist or don't.

---

#### 2.2 Deliverable Structure Validation

**File**: `tests/test_deliverable_structure.sh`

**Purpose**: After a skill run, verify output files have required sections

```bash
#!/bin/bash
# Run AFTER skill execution to validate output structure

test_requirements_has_fr_section() {
    grep -q "## Functional Requirements" docs/planning/requirements.md
}

test_requirements_has_nfr_section() {
    grep -q "## Non-Functional Requirements" docs/planning/requirements.md
}

test_requirements_has_user_stories() {
    grep -q "## User Stories" docs/planning/requirements.md
}

test_architecture_has_tech_stack() {
    grep -q "## Technology Stack" docs/planning/architecture.md
}

test_architecture_has_components() {
    grep -q "## System Components" docs/planning/architecture.md || \
    grep -q "## Components" docs/planning/architecture.md
}

test_adr_count_in_range() {
    count=$(ls docs/adrs/ADR-*.md 2>/dev/null | wc -l)
    [ "$count" -ge 3 ] && [ "$count" -le 7 ]
}

test_adr_has_status() {
    for adr in docs/adrs/ADR-*.md; do
        grep -q "## Status" "$adr" || return 1
    done
}

test_adr_has_decision() {
    for adr in docs/adrs/ADR-*.md; do
        grep -q "## Decision" "$adr" || return 1
    done
}

test_tasks_has_phases() {
    grep -q "## Phase" docs/planning/tasks.md
}
```

**Why this is valid**: Section headers are structural - they should be present regardless of content.

**Limitation**: These tests only run AFTER a successful skill execution. They validate format, not quality.

---

#### 2.3 ADR Format Validation

**File**: `tests/test_adr_format.py`

**Purpose**: Validate ADR files follow the expected format

```python
#!/usr/bin/env python3
"""Validate ADR format compliance."""

import re
from pathlib import Path

REQUIRED_SECTIONS = [
    "## Status",
    "## Context",
    "## Decision",
    "## Consequences"
]

OPTIONAL_SECTIONS = [
    "## Alternatives",
    "## Rationale",
    "## Implementation"
]

def validate_adr(filepath: Path) -> tuple[bool, list[str]]:
    """Check if ADR has required sections."""
    content = filepath.read_text()
    missing = []

    for section in REQUIRED_SECTIONS:
        if section not in content:
            missing.append(section)

    return len(missing) == 0, missing

def test_all_adrs():
    """Test all ADR files in docs/adrs/."""
    adr_dir = Path("docs/adrs")
    if not adr_dir.exists():
        print("SKIP: docs/adrs/ does not exist")
        return

    adrs = list(adr_dir.glob("ADR-*.md"))
    if not adrs:
        print("SKIP: No ADR files found")
        return

    all_passed = True
    for adr in adrs:
        passed, missing = validate_adr(adr)
        if passed:
            print(f"PASS: {adr.name}")
        else:
            print(f"FAIL: {adr.name} - Missing: {', '.join(missing)}")
            all_passed = False

    return all_passed
```

**Why this is valid**: ADR format is a convention - required sections should always be present.

---

### Phase 3: Create Manual Test README (LOW EFFORT)

**File**: `tests/manual/README.md`

```markdown
# Manual Integration Tests

This directory contains **test evidence documentation** for Layer 3 testing
(quality evaluation) which requires human judgment.

## Purpose

These documents capture:
- Test execution inputs and outputs
- Quality gate scoring rationale
- Pass/fail decisions with reasoning

They are NOT missing automation - they document tests that CANNOT be automated.

## When to Re-Run Manual Tests

1. After significant changes to SKILL.md
2. After modifying agent prompts
3. After quality gate criteria changes
4. Quarterly verification runs

## How to Run

1. Invoke the skill with a test prompt:
   ```
   /skill spec-workflow-orchestrator
   > Plan a [test project description]
   ```

2. Observe quality gate scoring

3. Document results in new or updated markdown file

4. Compare to previous documentation for regression

## Files

| File | Tests | Last Run |
|------|-------|----------|
| skill-execution-tests.md | Agent spawning, quality gate | 2025-11-19 |
| edge-case-tests.md | Iteration loop, missing files | 2025-11-19 |
| integration-test-report.md | Full workflow E2E | 2025-11-19 |
```

---

## What NOT To Do

### ❌ DO NOT: Create Content Quality Assertions

```python
# WRONG - This is meaningless
def test_requirements_quality():
    content = read("docs/planning/requirements.md")
    assert len(content) > 10000  # Arbitrary
    assert "FR-001" in content   # Might use different format
    assert content.count("shall") > 5  # Brittle
```

### ❌ DO NOT: Mock Agent Execution

```python
# WRONG - Tests nothing real
def test_with_mock():
    mock_spec_analyst.return_value = FAKE_REQUIREMENTS
    result = run_workflow()
    assert result == expected  # Only tests the mock
```

### ❌ DO NOT: Force Deterministic Output

```python
# WRONG - AI outputs vary legitimately
def test_exact_match():
    output = run_agent(prompt)
    assert output == EXPECTED_REQUIREMENTS_MD  # Will always fail
```

---

## Implementation Order

| Phase | Effort | Impact | Priority | Status |
|-------|--------|--------|----------|--------|
| 1. Move archived docs to `tests/manual/` | Low | High | P0 | ✅ DONE |
| 2.1 Create `test_agent_structure.sh` | Low | Medium | P1 | ✅ DONE |
| 2.2 Create `test_deliverable_structure.sh` | Medium | Medium | P1 | ✅ DONE |
| 2.3 Create `test_adr_format.py` | Medium | Low | P2 | ✅ DONE |
| 2.4 Create `test_skill_integration.py` | Medium | High | P1 | ✅ DONE |
| 3. Create `tests/manual/README.md` | Low | High | P0 | ✅ DONE |

### Phase 2.4: API-Based Integration Test (Added)

**File**: `tests/test_skill_integration.py`

**Purpose**: Automate end-to-end skill testing without human intervention

- Calls Anthropic API directly with pre-prepared prompts
- Chains outputs: spec-analyst → spec-architect → spec-planner
- Outputs to `tests/fixtures/generated/{project-slug}/`
- Validates structure and content patterns
- Supports `--dry-run`, `--quick`, `--model` options

**Usage**:
```bash
python3 tests/test_skill_integration.py --dry-run   # Test without API
python3 tests/test_skill_integration.py --quick     # Fast test with API key
```

---

## Final Test Coverage After Migration

| Layer | Test Type | Files | Tests |
|-------|-----------|-------|-------|
| Infrastructure | Automated | `e2e_hook_test.py` | 148 |
| Infrastructure | Automated | `test_production_implementation.sh` | ~10 |
| Infrastructure | Automated | `test_interactive_decision.sh` | ~8 |
| Behavior | Automated | `test_agent_structure.sh` | 22 |
| Behavior | Automated | `test_deliverable_structure.sh` | 20 |
| Behavior | Automated | `test_adr_format.py` | 15 |
| Integration | API-based | `test_skill_integration.py` | E2E workflow |
| Quality | Manual | `tests/manual/*.md` | Human evaluation |

**Total Automated Tests**: ~223 tests
**Integration Test**: Full workflow automation via API
**Manual Test Documentation**: 4 files with execution evidence
