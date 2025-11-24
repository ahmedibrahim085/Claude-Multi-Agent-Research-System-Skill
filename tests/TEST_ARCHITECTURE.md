# Test Architecture for AI Agent Systems

**Created**: 2024-11-24
**Purpose**: Document the testing philosophy and architecture for this dual-skill orchestration platform

---

## Core Principle: AI Agents Are Non-Deterministic

Traditional software testing relies on determinism:
```python
# Traditional - DETERMINISTIC
assert add(2, 2) == 4  # Same input ALWAYS produces same output
```

AI agent testing faces a fundamental challenge:
```python
# Agent - NON-DETERMINISTIC
output = spawn_spec_analyst("Plan a task management app")
# Output varies EVERY RUN:
# - Different wording
# - Different number of requirements (10? 15? 20?)
# - Different level of detail
# ALL could be valid!
```

**Implication**: Traditional assertions (`assert output == expected`) are IMPOSSIBLE for agent outputs.

---

## The AI Agent Test Pyramid

```
                    ┌─────────────────────┐
                    │   QUALITY EVAL      │  ← Human judgment required
                    │   (Manual tests)    │     CANNOT automate
                    │   Layer 3           │
                    └─────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │      BEHAVIOR TESTS         │  ← Partial automation
               │   (Triggers, discovery)     │     Layer 2
               └─────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │           INFRASTRUCTURE TESTS            │  ← Full automation
        │   (Utilities, state, hooks)               │     Layer 1
        └───────────────────────────────────────────┘
```

### Layer 1: Infrastructure Tests (FULLY AUTOMATABLE)

**What**: Utilities, state management, hooks, file operations

**Current Coverage**:
- `tests/common/e2e_hook_test.py` - Hook keyword detection, compound logic (148 tests)
- `tests/common/test_production_implementation.sh` - State, archive, restore, version (10 tests)
- `tests/spec-workflow/test_interactive_decision.sh` - Project detection, user choices (8 tests)

**Characteristics**:
- Deterministic inputs/outputs
- Can run in CI/CD
- Fast execution
- No Claude Code runtime required

### Layer 2: Behavior Tests (PARTIALLY AUTOMATABLE)

**What**: Skill triggers correctly, agents discovered at expected paths

**Current Coverage**:
- `tests/common/e2e_hook_test.py` - Verifies hook produces correct system messages
- `tests/common/test_agent_structure.sh` - Verifies agent files exist

**What CAN be automated**:
- File existence checks
- Frontmatter validation
- Path verification

**What CANNOT be automated**:
- Actual agent spawning (requires Claude Code runtime)
- Task tool invocation verification

### Layer 3: Quality Evaluation (HUMAN JUDGMENT REQUIRED)

**What**: Content quality, technical accuracy, actionability, completeness

**Current Coverage**:
- `tests/spec-workflow/manual/` - Documented test executions with human evaluation
- Quality gate in SKILL.md - Runs automatically every workflow execution

**Why it CANNOT be automated**:
- "Is this requirement complete?" - Subjective judgment
- "Is the architecture feasible?" - Requires domain expertise
- "Are tasks atomic enough?" - Context-dependent

**The Quality Gate IS The Test**:
The 4-criteria quality gate (85% threshold) embedded in SKILL.md runs EVERY execution.
Manual test documentation captures the evidence of these evaluations.

---

## What Can vs Cannot Be Automated

### CAN Automate ✅

| Check | Example | Test Location |
|-------|---------|---------------|
| Hook keyword detection | "research" triggers research workflow | `e2e_hook_test.py` |
| Compound request logic | "search AND build" asks user | `e2e_hook_test.py` |
| Utility functions | State save/load, archive/restore | `test_production_implementation.sh` |
| File existence | Agent files exist at `.claude/agents/` | `test_agent_structure.sh` |
| Format validation | ADR has required sections | `test_adr_format.py` |
| Structure checks | Requirements has FR/NFR sections | `test_deliverable_structure.sh` |
| Full workflow | API-driven agent chain | `test_skill_integration.py` |

### CANNOT Automate ❌

| Check | Why | Solution |
|-------|-----|----------|
| Content quality | Subjective, varies by context | Quality gate + manual evaluation |
| Technical accuracy | Requires domain expertise | Human review |
| Actionability | Judgment call | Quality gate scoring |
| Progress tracking | TodoWrite is UI feature | Manual observation |

**Note**: Agent spawning and iteration loops CAN now be tested via `test_skill_integration.py` which calls the Anthropic API directly.

---

## Test Directory Structure

```
tests/
├── common/                              # Tests for BOTH skills
│   ├── e2e_hook_test.py                # Hook behavior (148 tests)
│   ├── test_agent_structure.sh         # Agent discovery (22 tests)
│   └── test_production_implementation.sh  # Utilities (~10 tests)
│
├── research-skill/                      # Research skill tests (35 files)
│   ├── README.md                       # Index and overview
│   ├── manual/                         # Human evaluation evidence
│   │   ├── README.md
│   │   ├── skill-execution-tests.md
│   │   ├── edge-case-tests.md
│   │   └── integration-test-report.md
│   ├── test-scripts/                   # Hook router test queries (32 tests)
│   │   ├── phase1-test-queries.sh
│   │   ├── production_validation.sh
│   │   ├── production_deploy_standard.sh
│   │   └── production_cleanup_inplace.sh
│   ├── phase-results/                  # Historical test execution results
│   │   ├── PHASE1_TEST_RESULTS.md
│   │   ├── PHASE2_TEST_RESULTS.md
│   │   ├── PHASE3_TEST_RESULTS.md
│   │   ├── PHASE4_TEST_RESULTS.md
│   │   ├── PHASE5_INTEGRATION_RESULTS.md
│   │   ├── PHASE6_TESTING_COMPLETE.md
│   │   └── TIER3_TEST_FINDINGS.md
│   ├── design-docs/                    # Implementation docs
│   ├── lessons-learned/                # 30+ testing lessons
│   └── analysis/                       # Failure analysis, bug fixes
│
├── spec-workflow/                       # Spec workflow tests
│   ├── README.md                       # Index and overview
│   ├── test_skill_integration.py       # API-based E2E (main test)
│   ├── test_adr_format.py              # ADR compliance (15 tests)
│   ├── test_deliverable_structure.sh   # Output format (20 tests)
│   ├── test_interactive_decision.sh    # Interactive flow (~8 tests)
│   ├── manual/                         # Human evaluation evidence
│   │   ├── README.md
│   │   ├── skill-execution-tests.md
│   │   ├── edge-case-tests.md
│   │   └── integration-test-report.md
│   └── fixtures/                       # Test outputs
│       └── generated/
│           └── integration-test-hello-world/
│
├── TEST_ARCHITECTURE.md                 # This file
└── ARCHIVED_TESTS_MIGRATION_PLAN.md
```

**Total Automated Tests**: ~223 tests across 7 test files
**Structure**: Organized by skill with common tests shared

---

## Manual Test Documentation Purpose

The `tests/spec-workflow/manual/` directory contains **test evidence**, not missing automation.

### What These Documents Capture

1. **Exact Input Used** - The prompt that triggered the workflow
2. **Actual Output Generated** - What the agents produced
3. **Scoring Rationale** - WHY each criterion scored X/Y points
4. **Pass/Fail Decision** - Final quality gate result
5. **Execution Timeline** - How long each phase took

### How To Use Them

1. **Regression Baseline**: Compare future runs to documented successful runs
2. **Onboarding**: New team members understand what "good" looks like
3. **Debugging**: When quality drops, compare to known-good documentation
4. **Audit Trail**: Evidence that testing was performed

### When To Update Them

- After significant SKILL.md changes
- After agent prompt modifications
- After quality gate criteria changes
- Periodically (quarterly) to verify consistency

---

## Adding New Automated Tests

### For Infrastructure (Layer 1)

Add to existing test files or create new `.sh`/`.py` files:
```bash
# Example: New utility test
test_new_utility() {
    result=$(.claude/utils/new_utility.sh "input")
    assert_equals "$result" "expected_output"
}
```

### For Behavior (Layer 2)

Create structural validation tests:
```bash
# Example: Verify agent has required frontmatter
test_agent_has_tools() {
    grep -q "^tools:" .claude/agents/spec-analyst.md
    assert_success
}
```

### For Quality (Layer 3)

DO NOT try to automate. Instead:
1. Run the skill manually with a test prompt
2. Document the execution in `tests/spec-workflow/manual/`
3. Record the quality gate score and rationale

---

## Anti-Patterns to Avoid

### ❌ Brittle Content Assertions

```python
# BAD - Will fail randomly
def test_spec_analyst():
    output = run_agent("Plan task app")
    assert "FR-001" in output  # Might be "REQ-001" instead
    assert len(output) > 1000  # Arbitrary, meaningless
```

### ❌ Mocking Agent Behavior

```python
# BAD - Doesn't test real system
def test_with_mock():
    mock_agent.return_value = "fake output"
    # This tests nothing useful
```

### ❌ Forcing Determinism

```python
# BAD - Fighting the nature of AI
def test_exact_output():
    assert output == EXPECTED_REQUIREMENTS_MD  # Impossible
```

### ✅ Correct Approaches

```bash
# GOOD - Structural validation
test_requirements_has_sections() {
    grep -q "## Functional Requirements" docs/planning/requirements.md
    grep -q "## Non-Functional Requirements" docs/planning/requirements.md
}

# GOOD - Format validation
test_adr_format() {
    grep -q "## Status" docs/adrs/ADR-001*.md
    grep -q "## Decision" docs/adrs/ADR-001*.md
}

# GOOD - Count validation
test_adr_count() {
    count=$(ls docs/adrs/ADR-*.md | wc -l)
    [ "$count" -ge 3 ] && [ "$count" -le 7 ]
}
```

---

## Summary

| Layer | Automation | Tests | Location |
|-------|------------|-------|----------|
| Infrastructure | Full | `e2e_hook_test.py` (148), `test_production_*.sh` (~10) | `common/` |
| Behavior | Full | `test_agent_structure.sh` (22), `test_deliverable_structure.sh` (20), `test_adr_format.py` (15) | `common/`, `spec-workflow/` |
| Integration | API-based | `test_skill_integration.py`, `test_interactive_decision.sh` | `spec-workflow/` |
| Quality | Manual | `manual/*.md` | `spec-workflow/manual/` |

**Total Automated Tests**: ~223 across 7 test files

**Key Insights**:
- The quality gate in SKILL.md IS the test framework for Layer 3
- `test_skill_integration.py` enables automated E2E testing via Anthropic API
- Structural tests validate format without asserting content quality

---

## Research Skill Tests

The `tests/research-skill/` directory contains test documentation for the `multi-agent-researcher` skill (from November 2025 development).

### Purpose

These tests serve as:
1. **Reference** for implementing research skill tests in the current project
2. **Lessons Learned** - 30+ documented lessons applicable to any agent system
3. **Test Patterns** - Reusable patterns for hook routing, tier testing, quality gates

### Content Summary

| Category | Files | Key Content |
|----------|-------|-------------|
| Phase Results | 7 | PHASE1-6 test outcomes, all 5 tiers validated |
| Design Docs | 9 | Implementation plan, design decisions, conversion maps |
| Test Scripts | 4 | 32 hook router queries, production validation |
| Lessons | 2 | 30+ lessons from development |
| Analysis | 8 | Failure analysis, bug fixes, empirical evidence |

### Key Lessons (Applicable to Current Project)

From the archived lessons learned:

1. **Test automation AFTER restart** - Fresh session validates CLAUDE.md rules
2. **Comprehensive test evidence docs** - 200-400 line reports prove completion
3. **User questions reveal gaps** - "Why isn't X working?" exposes missing infra
4. **Clean historical broken data** - When fixing bugs, clean old artifacts
5. **spawned_by matters** - Track which orchestrator spawned each agent

### Comparison: Research vs Spec-Workflow Tests

| Aspect | Research Skill | Spec-Workflow |
|--------|----------------|---------------|
| Location | `tests/research-skill/` | `tests/spec-workflow/` |
| Hook Router Tests | ✅ 32 queries | ❌ Not implemented |
| Tier/Agent Tests | ✅ 5 tiers validated | ✅ 3 agents validated |
| Quality Gate Tests | ✅ Documented | ✅ Embedded in SKILL.md |
| Integration Tests | ✅ Phase 5-6 | ✅ test_skill_integration.py |
| Failure Analysis | ✅ Extensive | ⚠️ Limited |
| Lessons Learned | ✅ 30+ documented | ⚠️ To be documented |

### Next Steps

To achieve parity between research and planning skill testing:

1. Implement hook router tests for planning skill triggers
2. Document tier-equivalent tests (analyst → architect → planner flow)
3. Create failure analysis documentation as issues are found
4. Extract lessons learned from planning skill development
