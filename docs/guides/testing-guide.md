# Testing Procedures Guide
## Validating CLAUDE.md Modernization (Phase 4-5)

This guide provides step-by-step instructions to validate the @import modularization and ensure the modernization works correctly.

---

## Overview

**Purpose**: Validate that @import mechanism loads modular documentation correctly and that all workflows function as intended after Phase 4-5 modernization.

**When to Use**: Immediately after Phase 4-5 completion, and quarterly as part of maintenance compliance checks.

**Prerequisites**: Fresh Claude Code session (close and reopen to clear cached CLAUDE.md).

---

## Prerequisites Verification

Before starting tests, verify the modernization is in place:

```bash
# 1. Check CLAUDE.md line count (should be 86)
wc -l .claude/CLAUDE.md

# 2. Verify all modular docs exist
ls docs/workflows/*.md docs/configuration/*.md docs/guides/*.md

# 3. Check git status (should be clean or show only untracked files)
git status

# 4. Verify Phase 5 commit present
git log --oneline -1 | grep "PHASE-5"
```

**Expected Results**:
- CLAUDE.md: 86 lines
- 6 modular docs present (research-workflow.md, planning-workflow.md, compound-request-handling.md, semantic-search-hierarchy.md, configuration-guide.md, token-savings-guide.md)
- Git clean or backup files only
- Latest commit: acfec8a "MODERNIZATION-PHASE-5"

---

## Test Scenarios

### Test 1: Research Workflow Trigger

**Objective**: Verify research-workflow.md content loads via @import

**User Prompt**:
```
"research notification systems"
```

**Expected Behavior**:
- ✅ Hook message: "🔒 RESEARCH WORKFLOW ENFORCEMENT ACTIVATED"
- ✅ Can see "📖 Detailed workflow: docs/workflows/research-workflow.md" in hook message (Phase 5 enhancement)
- ✅ Access to detailed content: 49 trigger keywords (search, find, investigate, analyze, etc.)
- ✅ Mandatory workflow visible: STOP → INVOKE → DECOMPOSE → PARALLEL → SYNTHESIZE
- ✅ Synthesis Phase Enforcement section accessible (architectural constraint, Write tool exclusion)

**Verification Questions**:
1. Can you see the MANDATORY workflow section with 5 steps?
2. Are trigger keywords listed (Search/Discovery, Investigation, Collection, Learning, Contextual)?
3. Is the Synthesis Phase Enforcement section visible?

**Pass Criteria**: All 3 verification questions answered YES

---

### Test 2: Planning Workflow Trigger

**Objective**: Verify planning-workflow.md content loads via @import

**User Prompt**:
```
"build a local web interface for session logs"
```

**Expected Behavior**:
- ✅ Hook message: "🔒 PLANNING WORKFLOW ENFORCEMENT ACTIVATED"
- ✅ Can see "📖 Detailed workflow: docs/workflows/planning-workflow.md" in hook message (Phase 5 enhancement)
- ✅ Access to detailed content: 119 trigger keywords across 9 categories
- ✅ Mandatory workflow visible: STOP → INVOKE → ANALYZE → ARCHITECT → PLAN → VALIDATE
- ✅ Quality gate details: 85% threshold, 100 points, 4 criteria (Completeness, Technical Depth, Actionability, Clarity)

**Verification Questions**:
1. Can you see the quality gate scoring system (85% threshold)?
2. Are the 4 criteria explained (25 points each)?
3. Is the 3-agent workflow documented (spec-analyst → spec-architect → spec-planner)?

**Pass Criteria**: All 3 verification questions answered YES

---

### Test 3: Semantic Search Trigger

**Objective**: Verify semantic-search-hierarchy.md content loads via @import

**User Prompt**:
```
"find authentication logic in the codebase"
```

**Expected Behavior**:
- ✅ Hook message: "🔍 PROJECT CONTENT SEARCH ENFORCEMENT ACTIVATED (Token Savings)"
- ✅ Can see "📖 Detailed workflow: docs/workflows/semantic-search-hierarchy.md" in hook message (Phase 5 enhancement)
- ✅ Token savings value prop: "~8,000 tokens (traditional) vs ~600 tokens (semantic search) = 92% reduction"
- ✅ ABSOLUTE SEARCH HIERARCHY visible with 4-step decision tree
- ✅ Mandatory workflow: STOP → INVOKE → SKILL SPAWNS AGENT → AGENT EXECUTES → TOKEN SAVINGS

**Verification Questions**:
1. Can you see the token economics (5,000-10,000 tokens saved)?
2. Is the ABSOLUTE SEARCH HIERARCHY section visible (4 steps)?
3. Are usage examples shown (create index, list projects, basic search)?

**Pass Criteria**: All 3 verification questions answered YES

---

### Test 4: Compound Request Detection

**Objective**: Verify compound-request-handling.md content loads via @import

**User Prompt**:
```
"research notification systems and build one"
```

**Expected Behavior**:
- ✅ Hook message: "COMPOUND REQUEST DETECTED" (if compound detection works)
- ✅ Access to compound-request-handling.md content
- ✅ Signal Strength Analysis table visible (STRONG/MEDIUM/WEAK/NONE)
- ✅ Decision Matrix visible (5 rows × 4 columns)
- ✅ AskUserQuestion template accessible (JSON format with 4 options)

**Verification Questions**:
1. Can you see the Signal Strength Analysis table?
2. Is the Decision Matrix visible with all 5 rows?
3. Can you access the AskUserQuestion template with 4 workflow options?

**Pass Criteria**: All 3 verification questions answered YES

**Note**: If compound detection doesn't trigger, manually verify by asking: "Show me the compound request handling workflow"

---

### Test 5: Configuration Reference

**Objective**: Verify configuration-guide.md content loads via @import

**User Prompt**:
```
"what agents are available in this project?"
```

**Expected Behavior**:
- ✅ Access to configuration-guide.md content
- ✅ All 7 agents listed:
  * researcher
  * report-writer
  * spec-analyst
  * spec-architect
  * spec-planner
  * semantic-search-reader
  * semantic-search-indexer
- ✅ Each agent shows: description + tools list
- ✅ "DO NOT invoke directly, use via skill" warning present

**Verification Questions**:
1. Are all 7 agents listed?
2. Do semantic-search-reader and semantic-search-indexer appear? (Phase 0 fix verification)
3. Are tool lists complete for each agent?

**Pass Criteria**: All 3 verification questions answered YES

---

## Performance Verification

After completing all 5 test scenarios, verify performance:

**Token Usage Check**:
- Compare token usage for semantic search query vs hypothetical Grep exploration
- Expected: 90%+ token savings for functionality searches

**Response Time Check**:
- @import should be near-instant (< 1 second added latency)
- If slow: Check modular doc sizes, look for circular imports

**Progressive Disclosure Confirmation**:
- Only relevant workflow docs should load per prompt
- CLAUDE.md (86 lines) always loaded
- Additional imports load on-demand

---

## What to Do If Tests Fail

### If Any Test Fails:

1. **Document the failure**:
   - Which test scenario?
   - What was expected vs actual?
   - Error messages (if any)?

2. **Consult troubleshooting guide**:
   - See: `docs/guides/troubleshooting-guide.md`
   - Common issues: @import not loading, hook not detecting, path errors

3. **Rollback if needed**:
   - Method 1: `git restore .claude/CLAUDE.md` (rollback to Phase 3, 726 lines)
   - Method 2: `cp .claude/CLAUDE.md.backup .claude/CLAUDE.md` (instant restore)
   - Method 3: Edit CLAUDE.md, inline problematic import (partial fix)

4. **Re-run tests after fix**:
   - Fresh session required after any CLAUDE.md changes
   - Start from Test 1 again

---

## Success Criteria Summary

| Test | Component | Pass Criteria |
|------|-----------|---------------|
| **Test 1** | Research Workflow | All 3 verification questions YES |
| **Test 2** | Planning Workflow | All 3 verification questions YES |
| **Test 3** | Semantic Search | All 3 verification questions YES |
| **Test 4** | Compound Handling | All 3 verification questions YES |
| **Test 5** | Configuration | All 3 verification questions YES |
| **Performance** | Token/Speed | 90%+ savings, <1s latency |

**Overall Success**: All 5 tests pass + performance acceptable

---

## Reporting Results

After completing tests, document results:

**If All Tests Pass** ✅:
- Delete backup: `rm .claude/CLAUDE.md.backup`
- Update plan file: Mark Phase 4-5 as "VERIFIED"
- Merge to main branch (if on feature branch)
- Share success metrics

**If Tests Fail** ❌:
- Document failure details
- Follow troubleshooting guide
- Report issue with reproduction steps
- Do NOT delete backup file

---

**For maintenance testing**: Run these tests quarterly as part of compliance checks (see `docs/guides/maintenance-guide.md`).
