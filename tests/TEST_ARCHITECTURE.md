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
- `tests/e2e_hook_test.py` - Hook keyword detection, compound logic (148 tests)
- `tests/test_production_implementation.sh` - State, archive, restore, version (10 tests)
- `tests/test_interactive_decision.sh` - Project detection, user choices (8 tests)

**Characteristics**:
- Deterministic inputs/outputs
- Can run in CI/CD
- Fast execution
- No Claude Code runtime required

### Layer 2: Behavior Tests (PARTIALLY AUTOMATABLE)

**What**: Skill triggers correctly, agents discovered at expected paths

**Current Coverage**:
- `tests/e2e_hook_test.py` - Verifies hook produces correct system messages
- `tests/test_agent_structure.sh` (NEW) - Verifies agent files exist

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
- `tests/manual/` - Documented test executions with human evaluation
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
| Format validation | ADR has required sections | `test_adr_format.sh` |
| Structure checks | Requirements has FR/NFR sections | `test_deliverable_structure.sh` |

### CANNOT Automate ❌

| Check | Why | Solution |
|-------|-----|----------|
| Content quality | Subjective, varies by context | Quality gate + manual evaluation |
| Technical accuracy | Requires domain expertise | Human review |
| Actionability | Judgment call | Quality gate scoring |
| Agent spawning | Requires Claude Code runtime | Manual integration test |
| Iteration loop | Requires runtime re-spawning | Manual integration test |
| Progress tracking | TodoWrite is UI feature | Manual observation |

---

## Test Directory Structure

```
tests/
├── e2e_hook_test.py              # Layer 1: Hook behavior (148 tests)
├── test_production_implementation.sh  # Layer 1: Utilities (10 tests)
├── test_interactive_decision.sh  # Layer 1: Interactive flow (8 tests)
├── test_agent_structure.sh       # Layer 2: Agent discovery (NEW)
├── test_deliverable_structure.sh # Layer 2: Output format (NEW)
└── manual/                       # Layer 3: Human evaluation evidence
    ├── README.md                 # How to run manual tests
    ├── skill-execution-tests.md  # Evidence: Agent spawning, quality gate
    ├── edge-case-tests.md        # Evidence: Iteration loop, missing files
    └── integration-test-report.md # Evidence: Full workflow execution
```

---

## Manual Test Documentation Purpose

The `tests/manual/` directory contains **test evidence**, not missing automation.

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
2. Document the execution in `tests/manual/`
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

| Layer | Automation | Current Tests | Approach |
|-------|------------|---------------|----------|
| Infrastructure | Full | `e2e_hook_test.py`, `test_production_*.sh` | Traditional unit/integration tests |
| Behavior | Partial | `test_agent_structure.sh` (NEW) | Structural validation |
| Quality | None | `tests/manual/*.md` | Documentation + embedded quality gate |

**Key Insight**: The quality gate in SKILL.md IS the test framework for Layer 3.
It runs automatically every execution. Manual documentation captures the evidence.
