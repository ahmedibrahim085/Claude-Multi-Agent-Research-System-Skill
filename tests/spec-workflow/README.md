# Spec Workflow Tests

> **PURPOSE**: Test documentation for the spec-workflow-orchestrator skill
> **STATUS**: Active

---

## Overview

Comprehensive testing for the `spec-workflow-orchestrator` skill which provides planning from ideation to development-ready specifications.

**Skill Components**:
- **spec-analyst** - Requirements gathering agent
- **spec-architect** - System design agent
- **spec-planner** - Task breakdown agent

---

## Directory Structure

```
tests/spec-workflow/
├── README.md                      # This file
├── test_skill_integration.py      # API-based E2E workflow test
├── test_adr_format.py             # ADR compliance validation (15 tests)
├── test_deliverable_structure.sh  # Output format validation (20 tests)
├── test_interactive_decision.sh   # Interactive flow tests (~8 tests)
├── manual/                        # Layer 3: Human evaluation
│   ├── README.md                 # Manual test documentation
│   ├── skill-execution-tests.md  # Agent spawning, quality gate
│   ├── edge-case-tests.md        # Iteration, missing files
│   └── integration-test-report.md # Real-world validation
└── fixtures/                      # Test outputs
    └── generated/
        └── integration-test-hello-world/
```

---

## Running Tests

### Automated Tests

```bash
# API-based E2E (requires ANTHROPIC_API_KEY)
python3 tests/spec-workflow/test_skill_integration.py --dry-run   # Without API
python3 tests/spec-workflow/test_skill_integration.py --quick     # With API

# Structural validation (after skill execution)
./tests/spec-workflow/test_deliverable_structure.sh [project-slug]
python3 tests/spec-workflow/test_adr_format.py [project-slug]

# Interactive decision flow
./tests/spec-workflow/test_interactive_decision.sh
```

### Manual Tests

See `manual/README.md` for Layer 3 (human evaluation) test procedures.

---

## Test Categories

### 1. Integration Test (`test_skill_integration.py`)

**Purpose**: Automate end-to-end skill testing via Anthropic API

**Features**:
- Calls API directly with pre-prepared prompts
- Chains outputs: spec-analyst → spec-architect → spec-planner
- Outputs to `fixtures/generated/{project-slug}/`
- Supports `--dry-run`, `--quick`, `--model` options

**Usage**:
```bash
export ANTHROPIC_API_KEY='your-key'
python3 tests/spec-workflow/test_skill_integration.py --quick
```

### 2. Deliverable Structure (`test_deliverable_structure.sh`)

**Purpose**: Validate output files have required sections

**Checks**:
- requirements.md has FR/NFR sections, user stories
- architecture.md has tech stack, components
- tasks.md has phases, task IDs
- ADR count in range (3-7)
- File size sanity checks

### 3. ADR Format (`test_adr_format.py`)

**Purpose**: Validate ADR files follow standard format

**Required Sections**:
- `## Status`
- `## Context`
- `## Decision`
- `## Consequences`

### 4. Interactive Decision (`test_interactive_decision.sh`)

**Purpose**: Test project detection and user choices

**Scenarios**:
- Fresh project creation
- Existing project detection
- Archive/Refine decision flow

---

## Test Outputs

### Generated Fixtures

After running `test_skill_integration.py`:

```
fixtures/generated/integration-test-hello-world/
├── planning/
│   ├── requirements.md
│   ├── architecture.md
│   └── tasks.md
└── adrs/
    ├── ADR-001-*.md
    ├── ADR-002-*.md
    └── ...
```

### Manual Test Evidence

After running manual tests, document results in `manual/`:
- `skill-execution-tests.md` - Agent spawning validation
- `edge-case-tests.md` - Error handling scenarios
- `integration-test-report.md` - Real-world project planning

---

## Quality Gates

The spec-workflow-orchestrator enforces quality standards:

| Criterion | Weight | Threshold |
|-----------|--------|-----------|
| Completeness | 25 pts | 21/25 |
| Technical Depth | 25 pts | 21/25 |
| Actionability | 25 pts | 21/25 |
| Clarity | 25 pts | 21/25 |
| **Total** | 100 pts | **85%** |

**Max Iterations**: 3 attempts per agent before escalation

---

## Relationship to Common Tests

Shared infrastructure tests in `tests/common/`:
- `e2e_hook_test.py` - Hook keyword detection (148 tests)
- `test_agent_structure.sh` - Agent file validation (22 tests)
- `test_production_implementation.sh` - Utility tests (~10 tests)

---

**Last Updated**: 2024-11-24
