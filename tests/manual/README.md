# Manual Integration Tests

This directory contains **test evidence documentation** for Layer 3 testing (quality evaluation) which requires human judgment.

---

## Why These Are Documentation, Not Scripts

AI agent systems are **non-deterministic**:
- Same input produces different valid outputs each run
- Quality evaluation requires subjective judgment ("Is this complete?")
- Content assessment cannot be coded as assertions

**The quality gate in SKILL.md IS the automated test** - it runs every workflow execution.
These documents capture the **evidence** of those evaluations.

---

## Directory Contents

| File | Description | Last Verified |
|------|-------------|---------------|
| `skill-execution-tests.md` | 6 tests: Skill activation, agent spawning, quality gate, handoff | 2025-11-19 |
| `edge-case-tests.md` | 3 tests: Iteration loop, missing files, progress tracking | 2025-11-19 |
| `integration-test-report.md` | Real-world validation with Session Log Viewer project | 2025-11-19 |

---

## What These Documents Capture

1. **Exact Input Used** - The prompt that triggered the workflow
2. **Actual Output Generated** - What the agents produced
3. **Scoring Rationale** - WHY each criterion scored X/Y points
4. **Pass/Fail Decision** - Final quality gate result
5. **Execution Timeline** - How long each phase took

---

## How To Use These Documents

### As Regression Baseline

When running the skill after changes:
1. Compare outputs to documented successful run
2. Look for missing sections, reduced quality
3. Document any differences as potential regressions

### For Onboarding

New team members can understand:
- What "good" skill output looks like
- How quality scoring works
- Expected timeline for workflow completion

### For Debugging

When quality drops:
1. Review documented successful run
2. Compare current output to baseline
3. Identify what changed

### As Audit Trail

Evidence that testing was performed:
- Test date and conditions
- Pass/fail status with reasoning
- Quality gate scores

---

## When To Re-Run Manual Tests

1. **After significant SKILL.md changes** - New workflow steps, different prompts
2. **After agent prompt modifications** - Changes to spec-analyst, spec-architect, spec-planner
3. **After quality gate criteria changes** - Different thresholds or scoring
4. **Quarterly verification** - Ensure consistent behavior over time

---

## How To Run Manual Tests

### Automated Alternative

For structural validation without human input, use the API-based integration test:

```bash
# Generate test fixtures via Anthropic API
export ANTHROPIC_API_KEY='your-key'
python3 tests/test_skill_integration.py --quick

# Then validate with structural tests
./tests/test_deliverable_structure.sh integration-test-hello-world
python3 tests/test_adr_format.py integration-test-hello-world
```

This generates outputs to `tests/fixtures/generated/` for automated validation.

### Skill Execution Test (Manual)

```bash
# 1. Invoke the skill
/skill spec-workflow-orchestrator

# 2. Provide test prompt
Plan a simple task management web application with user authentication

# 3. Observe all 7 workflow steps
# 4. Note quality gate score
# 5. Compare to skill-execution-tests.md
```

### Edge Case: Iteration Loop

```bash
# Requires incomplete output to trigger
# 1. Run skill with vague prompt that produces low-quality output
# 2. Observe feedback generation
# 3. Check iteration count tracking
# 4. Verify max 3 iterations enforced
```

### Edge Case: Missing Files

```bash
# After skill execution
# 1. Delete some ADR files
# 2. Re-run quality gate validation
# 3. Check gap detection
# 4. Verify feedback specifies missing files
```

### Integration Test

```bash
# 1. Use a real, complex project request
/skill spec-workflow-orchestrator

# 2. Provide complex prompt like:
Build a web interface for log analysis with search, filtering,
cross-session tracking, and local deployment

# 3. Validate all deliverables
# 4. Compare to integration-test-report.md
```

---

## Updating Documentation

After re-running tests:

1. **If tests pass** - Update "Last Verified" date
2. **If outputs differ** - Document differences
3. **If quality improved** - Update expected outputs
4. **If quality decreased** - Investigate regression

---

## Relationship to Automated Tests

```
tests/
├── e2e_hook_test.py              # Layer 1: Automated (148 tests)
├── test_production_implementation.sh  # Layer 1: Automated (~10 tests)
├── test_interactive_decision.sh  # Layer 1: Automated (~8 tests)
├── test_agent_structure.sh       # Layer 2: Automated (22 tests)
├── test_deliverable_structure.sh # Layer 2: Automated (20 tests)
├── test_adr_format.py            # Layer 2: Automated (15 tests)
├── test_skill_integration.py     # Integration: API-based E2E workflow
├── fixtures/generated/           # API-generated test outputs
│   └── integration-test-hello-world/
└── manual/                       # Layer 3: Human evaluation
    ├── README.md                 # This file
    ├── skill-execution-tests.md  # Agent spawning, quality gate
    ├── edge-case-tests.md        # Iteration, missing files
    └── integration-test-report.md # Real-world validation
```

**Total: ~223 automated tests**

**Automated tests** verify deterministic behavior (file exists, section present).
**Integration test** generates real outputs via API for structural validation.
**Manual tests** verify quality that requires judgment (content is good, complete).

---

## Key Insight

> The quality gate in SKILL.md runs **every execution**.
> These documents are **evidence** that the quality gate works correctly.
> They are NOT missing automation - they document tests that CANNOT be automated.

---

**Last Updated**: 2024-11-24
