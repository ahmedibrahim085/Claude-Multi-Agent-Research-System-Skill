# Maintenance Guide
## Sustaining <100-Line CLAUDE.md Long-Term

This guide provides rules, decision trees, and procedures to prevent CLAUDE.md from regressing to a monolithic structure as the project evolves.

---

## Overview

**Purpose**: Keep CLAUDE.md under 100 lines as new skills, agents, and features are added.

**Golden Rule**: **Hot path in CLAUDE.md, cold path in @imports**

**Review Frequency**:
- **Per feature**: After adding/updating major skills or workflows
- **Quarterly**: Compliance check (line count, duplication, @import validity)
- **Annually**: Comprehensive audit (restructuring if needed)

---

## The 100-Line Rule

### Why 100 Lines?

**Anthropic Best Practice** (2025):
- Recommended: 50-75 lines (ideal)
- Maximum: 100 lines (hard limit)
- Beyond 100: Maintainability degrades, token efficiency lost

**Current State**:
- **CLAUDE.md**: 86 lines (14% margin below limit)
- **Modular docs**: 756 lines in 6 files
- **Total**: 842 lines (comprehensive, but focused)

### Thresholds

| Line Count | Status | Action Required |
|------------|--------|-----------------|
| **< 90** | ✅ GOOD | No action needed |
| **90-95** | ⚠️ WARNING | Review content, consider extracting |
| **95-100** | 🚨 CRITICAL | Immediate refactor required |
| **> 100** | ❌ VIOLATION | Emergency extraction to modular docs |

---

## Decision Tree: When to Inline vs @import

Use this decision tree **every time** you add or modify content:

### INLINE in CLAUDE.md When:

1. **Critical Decision Gate**:
   - ALWAYS/NEVER/MANDATORY directives
   - Example: "ALWAYS use multi-agent-researcher for multi-source research"

2. **Self-Check Questions**:
   - 2-3 question decision gates
   - Example: "Multi-source? Synthesis needed? >3 searches? → Use skill"

3. **High-Level Architecture Concept**:
   - System-wide patterns (hooks, skills, agents, progressive disclosure)
   - Example: "Hooks auto-detect trigger keywords → suggest/activate skills"

4. **Core Orchestration Rule**:
   - Non-negotiable workflows
   - Example: "Quality gate enforced: 85% threshold"

5. **Key Value Proposition**:
   - Token savings summary
   - Example: "Saves 5,000-10,000 tokens vs traditional Grep exploration"

**Character Limit per Inline**: ~100 characters max (aim for conciseness)

---

### @IMPORT to Modular Doc When:

1. **Detailed Trigger Keywords**:
   - Lists of >20 keywords
   - Example: 49 research keywords, 119 planning keywords

2. **Step-by-Step Workflow Instructions**:
   - Numbered procedures (>3 steps)
   - Example: "1. STOP 2. INVOKE 3. DECOMPOSE 4. PARALLEL 5. SYNTHESIZE"

3. **Examples and Violation Scenarios**:
   - ❌ WRONG / ✅ CORRECT comparisons
   - Example: "❌ I do 15 sequential WebSearch calls → ✅ I invoke multi-agent-researcher"

4. **Configuration Reference**:
   - Agents list (with tools)
   - Skills list (with descriptions)
   - Commands list
   - File organization conventions

5. **Technical Specifications**:
   - MCP server details
   - Hook implementation specifics
   - Quality gate criteria breakdown

6. **Token Economics Details**:
   - Before/after comparisons
   - Detailed cost analysis
   - Performance benchmarks

**Content Location**: `docs/workflows/` for workflows, `docs/configuration/` for reference, `docs/guides/` for explanatory content

---

### Decision Matrix

| Content Type | Location | Reasoning |
|--------------|----------|-----------|
| **"ALWAYS use X skill"** | CLAUDE.md | Critical decision gate |
| **"Multi-source? → Use skill"** | CLAUDE.md | Self-check question |
| **"85% quality threshold"** | CLAUDE.md | Key metric (inline), details @imported |
| **"Saves 5,000-10,000 tokens"** | CLAUDE.md | Value proposition |
| **49 trigger keywords** | @import workflow doc | Detailed list (too long) |
| **5-step workflow** | @import workflow doc | Detailed procedure |
| **Examples (WRONG/CORRECT)** | @import workflow doc | Educational content |
| **Agent tools list** | @import config doc | Reference material |
| **MCP technology specs** | @import config doc | Technical detail |

---

## Adding New Skills

Follow this process to add a new skill without violating the 100-line rule:

### Step 1: Create Workflow Documentation First

```bash
# Create new workflow doc
touch docs/workflows/{skill-name}-workflow.md

# Structure:
# - Title (# Skill Name Workflow)
# - Overview (purpose, when to use)
# - ALWAYS Use Section (trigger keywords, patterns)
# - MANDATORY Workflow (numbered steps)
# - Examples (violations to avoid)
# - Self-Check questions
```

**Estimated size**: 100-150 lines per workflow doc

---

### Step 2: Add @import to CLAUDE.md

```markdown
# In CLAUDE.md (top section, lines 5-11):

@import ../docs/workflows/research-workflow.md
@import ../docs/workflows/planning-workflow.md
@import ../docs/workflows/compound-request-handling.md
@import ../docs/workflows/semantic-search-hierarchy.md
@import ../docs/workflows/{NEW-SKILL}-workflow.md  # ADD HERE
@import ../docs/configuration/configuration-guide.md
@import ../docs/guides/token-savings-guide.md
```

**Impact**: +1 line (acceptable if still <100 total)

---

### Step 3: Add Critical Rule Summary to CLAUDE.md

```markdown
# In CLAUDE.md (## CRITICAL: Universal Orchestration Rules section):

### {New Skill Name}: {skill-name} Skill

**ALWAYS use when:**
- [2-3 bullet points, <100 chars each]

**NEVER:**
- [1-2 prohibitions]

**MANDATORY:**
- [1-2 key requirements]

**Self-check:** [2-3 questions] → Use skill
```

**Impact**: ~10-15 lines (verify total still <100)

---

### Step 4: Update Hook Messages (Optional - Phase 5 Pattern)

```python
# In .claude/hooks/user-prompt-submit.py:

def build_{skill_name}_enforcement_message(triggers: dict) -> str:
    """Build enforcement message for {skill-name} skill"""
    # ... existing message logic ...

    return f"""
    # ... message content ...

    📖 **Detailed workflow**: docs/workflows/{skill-name}-workflow.md

    ---
    """.strip()
```

**Impact**: +1 doc reference line in hook message (optional enhancement)

---

### Step 5: Update Skill Frontmatter (Optional - Phase 5 Pattern)

```yaml
# In .claude/skills/{skill-name}/SKILL.md:

---
name: {skill-name}
description: [existing description] (Full workflow documentation at docs/workflows/{skill-name}-workflow.md)
allowed-tools: [tool list]
version: 1.0.0
---
```

**Impact**: +1 doc reference in skill description (optional enhancement)

---

### Step 6: Verify Line Count

```bash
# Check CLAUDE.md line count
wc -l .claude/CLAUDE.md

# Target: < 95 lines (leave 5-line buffer)
# If > 95: Extract more content to workflow doc
```

---

## Updating Existing Workflows

### Rule: Edit Modular Docs, NOT CLAUDE.md

**Correct Approach** ✅:
```bash
# Update detailed workflow
vi docs/workflows/research-workflow.md

# Add new trigger keywords, examples, or clarifications
# CLAUDE.md remains unchanged
```

**Wrong Approach** ❌:
```bash
# DO NOT inline details from workflow docs into CLAUDE.md
# DO NOT expand critical rules beyond ~10 lines each
```

---

### Exception: Critical Rule Changes

**When to update CLAUDE.md**:
- Decision gate changes (ALWAYS/NEVER/MANDATORY directives)
- Self-check question modifications
- Core orchestration rule updates
- Key metric changes (e.g., quality threshold 85% → 90%)

**Process**:
1. Update CLAUDE.md critical rule (1-2 lines)
2. Update detailed workflow doc (full explanation)
3. Verify CLAUDE.md line count still <100
4. Test in fresh session
5. Commit with clear message

---

## Quarterly Compliance Check

Run this checklist every 3 months or after major feature additions:

### 1. Line Count Check

```bash
wc -l .claude/CLAUDE.md
```

**Target**: < 90 lines (ideally)
**Acceptable**: < 95 lines (with plan to reduce)
**Action Required**: > 95 lines (immediate refactor)

---

### 2. Duplication Measurement

```bash
# Check for duplicate content across docs
# Manual spot-check or use diff tools

# Example check:
diff docs/workflows/research-workflow.md docs/guides/token-savings-guide.md
```

**Target**: < 5% duplication
**Acceptable**: < 10% duplication (quick-reference checklists ok)
**Action Required**: > 10% duplication (consolidate or remove)

**Current State**: 7% residual duplication (acceptable)

---

### 3. @import Path Validation

```bash
# Verify all @import paths exist
cd .claude
for file in ../docs/workflows/research-workflow.md \
            ../docs/workflows/planning-workflow.md \
            ../docs/workflows/compound-request-handling.md \
            ../docs/workflows/semantic-search-hierarchy.md \
            ../docs/configuration/configuration-guide.md \
            ../docs/guides/token-savings-guide.md; do
  [ -f "$file" ] && echo "✓ $file exists" || echo "✗ $file MISSING"
done
```

**Target**: All paths valid
**Action Required**: Any missing file (restore from git or recreate)

---

### 4. Test All Scenarios

Use testing guide to validate workflows:

```bash
# See: docs/guides/testing-guide.md

# Test all 5 scenarios:
1. Research workflow trigger
2. Planning workflow trigger
3. Semantic search trigger
4. Compound detection
5. Configuration reference
```

**Target**: All 5 tests pass
**Action Required**: Any test fails (see troubleshooting-guide.md)

---

### 5. Review Content Drift

**Check for**:
- Critical rules that migrated to workflow docs (should stay in CLAUDE.md)
- Inline examples in CLAUDE.md (should move to workflow docs)
- Redundant self-checks (consolidate)
- Outdated information (update)

**Action**: Realign content to hot/cold path separation

---

## Warning Signs of Regression

Watch for these indicators that maintenance is needed:

### 🚨 Critical Warning Signs

1. **CLAUDE.md > 95 lines**
   - **Action**: Extract content to workflow docs immediately
   - **Target**: Return to <90 lines within 1 week

2. **Duplication > 10%**
   - **Action**: Consolidate duplicate content
   - **Method**: Keep in most specific location, remove from general docs

3. **Critical Rules in Workflow Docs**
   - **Action**: Move back to CLAUDE.md (hot path)
   - **Example**: ALWAYS/NEVER directives should be in CLAUDE.md

4. **Multiple Inline Examples**
   - **Action**: Extract to workflow docs
   - **Keep**: 1 example max in CLAUDE.md (if necessary)

---

### ⚠️ Early Warning Signs

1. **CLAUDE.md 90-95 lines**
   - **Action**: Review for extraction candidates
   - **Timeline**: Before next major feature

2. **Duplication 5-10%**
   - **Action**: Plan consolidation
   - **Timeline**: Next quarterly check

3. **Self-Check Questions Expanding**
   - **Action**: Keep to 2-3 questions max per skill
   - **Method**: Move detailed decision trees to workflow docs

4. **New Skills Without Workflow Docs**
   - **Action**: Create workflow doc before inlining
   - **Prevention**: Follow "Adding New Skills" process above

---

## Emergency Refactoring

If CLAUDE.md exceeds 100 lines:

### Step 1: Identify Extraction Candidates

**Look for**:
- Lists longer than 5 items → Extract to workflow doc
- Examples (WRONG/CORRECT) → Extract to workflow doc
- Detailed procedures (>3 steps inline) → Extract to workflow doc
- Technical specifications → Extract to config doc

---

### Step 2: Create/Update Modular Docs

```bash
# Move content to appropriate doc
vi docs/workflows/{skill-name}-workflow.md

# Add extracted content with proper structure
```

---

### Step 3: Replace with @import Reference

```markdown
# In CLAUDE.md, replace extracted content with:

See docs/workflows/{skill-name}-workflow.md for [detailed content]
```

**Or** if already @imported: Keep inline summary to ~5 lines

---

### Step 4: Verify and Test

```bash
# Check line count
wc -l .claude/CLAUDE.md  # Target: < 95

# Test in fresh session
# Run all 5 test scenarios (see testing-guide.md)
```

---

## Best Practices Summary

1. ✅ **ALWAYS** create workflow docs before inlining rules
2. ✅ **ALWAYS** verify line count after CLAUDE.md changes
3. ✅ **ALWAYS** test in fresh session after modular doc updates
4. ✅ **QUARTERLY** run compliance check
5. ✅ **NEVER** inline detailed examples in CLAUDE.md
6. ✅ **NEVER** exceed 100 lines without immediate refactor
7. ✅ **PREFER** extraction over expansion
8. ✅ **KEEP** critical rules hot path, details cold path

---

**For testing procedures**: See `docs/guides/testing-guide.md`
**For troubleshooting**: See `docs/guides/troubleshooting-guide.md`
**For design rationale**: See `docs/adrs/001-modular-claude-md.md`
