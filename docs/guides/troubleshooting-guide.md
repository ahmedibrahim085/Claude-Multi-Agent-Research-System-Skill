# Troubleshooting Guide
## Resolving CLAUDE.md Modernization Issues

This guide provides diagnostic procedures and solutions for common issues with @import modularization, hooks, and skill activation.

---

## Overview

**Purpose**: Diagnose and resolve issues with the modular CLAUDE.md architecture.

**When to Use**:
- Tests fail (see `testing-guide.md`)
- Unexpected behavior (workflows not loading, hooks not triggering)
- Performance issues (slow responses, high token usage)
- After updates (git pull, file modifications)

**Quick Reference**: Jump to [Common Issues](#common-issues--solutions) for immediate solutions.

---

## Common Issues & Solutions

### Issue 1: @import Content Not Loading

**Symptoms**:
- Imported workflow docs not visible in fresh session
- Claude doesn't have access to detailed workflow instructions
- Hook messages show but detailed content missing

**Diagnosis**:

```bash
# 1. Check CLAUDE.md syntax
cat .claude/CLAUDE.md | grep "@import"

# Expected output (6 lines):
# @import ../docs/workflows/research-workflow.md
# @import ../docs/workflows/planning-workflow.md
# @import ../docs/workflows/compound-request-handling.md
# @import ../docs/workflows/semantic-search-hierarchy.md
# @import ../docs/configuration/configuration-guide.md
# @import ../docs/guides/token-savings-guide.md

# 2. Verify all import paths exist
cd .claude
for file in ../docs/workflows/*.md ../docs/configuration/*.md ../docs/guides/token-savings-guide.md; do
  [ -f "$file" ] && echo "✓ $file" || echo "✗ MISSING: $file"
done

# 3. Check for path typos
# Common mistakes:
# - ./docs/ instead of ../docs/ (wrong relative path)
# - docs/workflow/ instead of docs/workflows/ (missing 's')
# - Missing file extension (.md)

# 4. Check file permissions
ls -la docs/workflows/*.md
# Should show read permissions (r-- or rw-)
```

**Solutions**:

1. **Fix Path Typos**:
```bash
# Edit CLAUDE.md to fix paths
vi .claude/CLAUDE.md

# Correct format: @import ../docs/workflows/filename.md
# From .claude/ directory, need ../ to go up one level
```

2. **Recreate Missing Files** (from git history):
```bash
# Check if file exists in git history
git log --all --full-history -- docs/workflows/research-workflow.md

# Restore from specific commit
git checkout <commit-hash> -- docs/workflows/research-workflow.md
```

3. **Fix File Permissions**:
```bash
# Make files readable
chmod 644 docs/workflows/*.md docs/configuration/*.md docs/guides/*.md
```

4. **Check Claude Code Version**:
```bash
# Verify Claude Code supports @import (feature added in recent versions)
# If using older version, upgrade or use rollback Method 2
```

**Verification**:
```bash
# Start fresh Claude Code session
# Test with: "research notification systems"
# Expected: Can see research-workflow.md content (49 trigger keywords, etc.)
```

---

### Issue 2: Hook Not Detecting Keywords

**Symptoms**:
- Skills not auto-activating despite using trigger words
- No enforcement messages appearing
- Hook seems to not run at all

**Diagnosis**:

```bash
# 1. Check hook execution (manual test)
cd .claude/hooks
echo "research machine learning systems" | python3 user-prompt-submit.py

# Expected: Hook output with enforcement message
# If error: Check Python syntax or dependencies

# 2. Verify hook permissions
ls -la .claude/hooks/user-prompt-submit.py
# Should show execute permissions (x)

# 3. Check Python syntax errors
python3 -m py_compile .claude/hooks/user-prompt-submit.py
# Expected: No output (success)
# If error: Syntax error message

# 4. Verify skill-rules.json unchanged
git diff .claude/skills/skill-rules.json
# Expected: No changes (or only intentional updates)

# 5. Check for hook configuration
# Verify Claude Code settings have hook enabled
```

**Solutions**:

1. **Restore Hook from Git** (if corrupted):
```bash
git checkout HEAD -- .claude/hooks/user-prompt-submit.py
```

2. **Fix Hook Permissions**:
```bash
chmod +x .claude/hooks/user-prompt-submit.py
```

3. **Fix Python Syntax Errors**:
```bash
# If Phase 5 changes caused syntax error:
git diff .claude/hooks/user-prompt-submit.py

# Check lines 586, 631, 691 for Phase 5 additions
# Verify proper indentation and syntax
```

4. **Verify Trigger Keywords** (in skill-rules.json):
```bash
# Check if trigger keywords present
grep -A 5 '"keywords":' .claude/skills/skill-rules.json | head -20

# Expected: Lists of keywords for research, planning, semantic-search
```

5. **Test Hook Manually**:
```python
# Create test file test_hook.py
import subprocess
result = subprocess.run(
    ['python3', '.claude/hooks/user-prompt-submit.py'],
    input='research notification systems',
    capture_output=True,
    text=True
)
print(result.stdout)
print(result.stderr)
```

**Verification**:
```bash
# Start fresh session
# Use explicit trigger: "I want to research machine learning"
# Expected: Hook enforcement message appears
```

---

### Issue 3: Skill Not Auto-Activating

**Symptoms**:
- Hook detects keywords and shows message
- But skill doesn't actually run/activate
- Have to manually invoke skill with /skill command

**Diagnosis**:

```bash
# 1. Check skill allowed-tools frontmatter
head -10 .claude/skills/multi-agent-researcher/SKILL.md
head -10 .claude/skills/spec-workflow-orchestrator/SKILL.md
head -10 .claude/skills/semantic-search/SKILL.md

# Expected: allowed-tools: Task, Read, Glob, ...

# 2. Verify SKILL.md syntax (YAML)
python3 -c "
import yaml
with open('.claude/skills/multi-agent-researcher/SKILL.md') as f:
    content = f.read()
    yaml_part = content.split('---')[1]
    yaml.safe_load(yaml_part)
print('✓ YAML valid')
"

# 3. Check for skill description issues
# Phase 5 added doc references - verify they don't break YAML
```

**Solutions**:

1. **Fix YAML Syntax Errors**:
```bash
# If Phase 5 changes broke YAML:
vi .claude/skills/multi-agent-researcher/SKILL.md

# Check line 3 (description field)
# Verify parentheses balanced: (Full workflow documentation at ...)
# Verify quotes matched if any
```

2. **Restore Skill Frontmatter from Git**:
```bash
git diff .claude/skills/multi-agent-researcher/SKILL.md

# If Phase 5 changes look wrong:
git checkout HEAD~1 -- .claude/skills/multi-agent-researcher/SKILL.md
```

3. **Validate All 3 Skill Frontmatters**:
```bash
for skill in multi-agent-researcher spec-workflow-orchestrator semantic-search; do
  echo "=== Checking $skill ==="
  python3 -c "
import yaml, sys
with open('.claude/skills/$skill/SKILL.md') as f:
    try:
        parts = f.read().split('---')
        yaml.safe_load(parts[1])
        print('✓ YAML valid')
    except Exception as e:
        print(f'✗ Error: {e}', file=sys.stderr)
        sys.exit(1)
  "
done
```

4. **Check Skill Activation Settings**:
```bash
# Verify Claude Code settings allow skill auto-activation
# Check .claude/settings.json or .claude/settings.local.json
```

**Verification**:
```bash
# Start fresh session
# Use trigger: "research open source libraries for authentication"
# Expected: Skill auto-activates (not just hook message)
```

---

### Issue 4: Performance Degradation

**Symptoms**:
- Slow response times after Phase 4-5
- High token usage compared to baseline
- Lag when workflows triggered

**Diagnosis**:

```bash
# 1. Check import depth (should be 1 hop)
grep -c "@import" .claude/CLAUDE.md
# Expected: 6 (one level deep)

# If any imported file has @import statements: PROBLEM (nested imports)
grep "@import" docs/workflows/*.md docs/configuration/*.md docs/guides/*.md
# Expected: No matches (no nested imports)

# 2. Check modular doc sizes
wc -l docs/workflows/*.md docs/configuration/*.md docs/guides/*.md
# Expected: All < 500 lines each

# 3. Verify no duplication across files
# Use diff or manual spot-check
diff docs/workflows/research-workflow.md docs/guides/token-savings-guide.md | wc -l
# Expected: < 20 lines overlap (7% residual acceptable)

# 4. Check for circular references
grep -r "See docs/" docs/ | grep -v ".md:"
# Look for references that might cause loading loops
```

**Solutions**:

1. **Remove Nested Imports** (if any):
```bash
# Modular docs should NOT have @import statements
# If found, inline that content or restructure
```

2. **Consolidate Large Docs**:
```bash
# If any file > 500 lines, consider splitting
# Or remove redundant content
```

3. **Remove Duplication**:
```bash
# Identify duplicate sections
# Keep in most specific location
# Remove from general docs
# Update cross-references instead of duplicating
```

4. **Inline Frequently-Used Content**:
```bash
# If specific content accessed every session:
# Consider moving from @import to CLAUDE.md (if <10 lines)
# Trade-off: Slight line count increase for performance gain
```

**Verification**:
```bash
# Measure baseline token usage
# Test scenario: "research notification systems"
# Compare token count vs expected (~600 tokens for semantic search)

# Response time should be < 2 seconds additional latency
```

---

### Issue 5: Phase 5 References Not Showing

**Symptoms**:
- Hook enforcement messages missing "📖 Detailed workflow: ..." line
- Skill descriptions missing "(Full workflow documentation at ...)" references

**Diagnosis**:

```bash
# 1. Check hook file for Phase 5 additions
grep "📖 \*\*Detailed workflow\*\*" .claude/hooks/user-prompt-submit.py
# Expected: 3 matches (lines 586, 631, 691)

# 2. Check skill frontmatters for Phase 5 additions
grep "Full workflow documentation" .claude/skills/*/SKILL.md
# Expected: 3 matches (one per skill)

# 3. Verify Phase 5 commit applied
git log --oneline -1
# Expected: Should see "PHASE-5" commit (acfec8a)
```

**Solutions**:

1. **Re-apply Phase 5 Changes**:
```bash
# If Phase 5 commit missing, cherry-pick it
git cherry-pick acfec8a

# Or manually add the lines:
vi .claude/hooks/user-prompt-submit.py
# Add after line 584: 📖 **Detailed workflow**: docs/workflows/research-workflow.md
# Add after line 629: 📖 **Detailed workflow**: docs/workflows/planning-workflow.md
# Add after line 689: 📖 **Detailed workflow**: docs/workflows/semantic-search-hierarchy.md
```

2. **Update Skill Frontmatters**:
```bash
# Manually add doc references to descriptions
vi .claude/skills/multi-agent-researcher/SKILL.md
# Line 3: Append " (Full workflow documentation at docs/workflows/research-workflow.md)"

vi .claude/skills/spec-workflow-orchestrator/SKILL.md
# Line 3: Append " (Full workflow documentation at docs/workflows/planning-workflow.md)"

vi .claude/skills/semantic-search/SKILL.md
# Line 11: Add "  (Full workflow documentation at docs/workflows/semantic-search-hierarchy.md)"
```

**Verification**:
```bash
# Start fresh session
# Trigger: "research machine learning"
# Expected: Hook message includes "📖 Detailed workflow: docs/workflows/research-workflow.md"
```

---

## Diagnostic Procedures

### Step-by-Step Debugging

Use this procedure when the cause is unclear:

#### Step 1: Verify File Structure

```bash
# Check all required files exist
tree -L 3 .claude docs

# Expected structure:
# .claude/
# ├── CLAUDE.md (86 lines)
# ├── CLAUDE.md.backup (726 lines)
# ├── hooks/user-prompt-submit.py
# └── skills/[3 skills]/SKILL.md
#
# docs/
# ├── workflows/[4 workflow files]
# ├── configuration/configuration-guide.md
# └── guides/[3 guide files]

# Verify line counts
wc -l .claude/CLAUDE.md docs/**/*.md
```

#### Step 2: Syntax Validation

```bash
# Python syntax (hook file)
python3 -m py_compile .claude/hooks/user-prompt-submit.py && echo "✓ Python OK"

# YAML syntax (skill frontmatters)
for skill in multi-agent-researcher spec-workflow-orchestrator semantic-search; do
  python3 -c "
import yaml
with open('.claude/skills/$skill/SKILL.md') as f:
    yaml.safe_load(f.read().split('---')[1])
  " && echo "✓ $skill YAML OK"
done

# Markdown syntax (visual check)
# Open each .md file, look for:
# - Unclosed code blocks (``` without closing ```)
# - Broken links ([text](path) with invalid paths)
# - Malformed tables (inconsistent column counts)
```

#### Step 3: Path Verification

```bash
# Test @import paths from .claude/ directory
cd .claude
for path in ../docs/workflows/research-workflow.md \
            ../docs/workflows/planning-workflow.md \
            ../docs/workflows/compound-request-handling.md \
            ../docs/workflows/semantic-search-hierarchy.md \
            ../docs/configuration/configuration-guide.md \
            ../docs/guides/token-savings-guide.md; do
  if [ -f "$path" ]; then
    echo "✓ $path"
  else
    echo "✗ MISSING: $path"
  fi
done
cd ..
```

#### Step 4: Fresh Session Test

```bash
# 1. Close Claude Code completely
# 2. Clear any caches (if applicable)
# 3. Reopen Claude Code
# 4. Start new conversation
# 5. Test with simple trigger: "research X"
# 6. Verify workflow content loads
```

#### Step 5: Git Diff Check

```bash
# Compare to last known good state
git diff 4886046..HEAD .claude/CLAUDE.md
# Expected: Only Phase 5 commit changes if clean

# If unexpected changes found:
git diff .claude/CLAUDE.md
# Review and decide: keep, revert, or fix
```

---

## Rollback Procedures

### When to Rollback

- @import mechanism completely broken
- Multiple tests failing
- Hook errors preventing all skill activation
- Unsure how to fix issues

### Rollback Methods

#### Method 1: Git Restore (Recommended)

**Rollback to Phase 3** (726-line CLAUDE.md, no @imports):

```bash
# Full rollback
git restore .claude/CLAUDE.md

# Verify
wc -l .claude/CLAUDE.md
# Expected: 726 lines (Phase 3 state)

# Note: Phase 5 changes to hooks/skills remain
# To revert those too:
git restore .claude/hooks/user-prompt-submit.py
git restore .claude/skills/*/SKILL.md
```

**Rollback only Phase 5** (keep Phase 4):

```bash
# Revert to Phase 4 (86-line CLAUDE.md, but no Phase 5 doc references)
git diff 4886046..acfec8a | git apply -R

# Verify
git diff acfec8a
# Expected: Shows Phase 5 changes reverted
```

**Advantages**:
- Clean, versioned rollback
- Can rollback specific commits
- Git history preserved

**Disadvantages**:
- Requires git knowledge
- May affect uncommitted changes

---

#### Method 2: Backup File (Instant)

**Rollback to Pre-Phase 4** (726-line CLAUDE.md):

```bash
# Copy backup to CLAUDE.md
cp .claude/CLAUDE.md.backup .claude/CLAUDE.md

# Verify
wc -l .claude/CLAUDE.md
# Expected: 726 lines

# Verify content (spot-check)
head -20 .claude/CLAUDE.md
# Expected: Should start with "# Project Instructions" and show old structure
```

**Advantages**:
- Instant rollback
- No git required
- Simple command

**Disadvantages**:
- Only restores to one specific state (pre-Phase 4)
- Doesn't revert Phase 5 changes to hooks/skills
- Backup file may be out of sync if further modified

---

#### Method 3: Partial Rollback (Surgical)

**Inline Specific Problematic Import**:

If only ONE import is failing:

```bash
# 1. Read the problematic workflow doc
cat docs/workflows/research-workflow.md

# 2. Edit CLAUDE.md
vi .claude/CLAUDE.md

# 3. Remove the @import line:
# @import ../docs/workflows/research-workflow.md

# 4. Inline the critical content (condensed):
# Copy key sections from workflow doc
# Keep to <50 lines

# 5. Verify line count
wc -l .claude/CLAUDE.md
# Target: Still < 100 lines
```

**When to Use**:
- One specific workflow not loading
- Other imports working fine
- Don't want full rollback

**Advantages**:
- Keeps working imports
- Minimal disruption
- Can iterate on problematic content

**Disadvantages**:
- Manual effort
- Violates 100-line rule if too much inlined
- May need to redo later

---

### After Rollback

1. **Test Baseline Functionality**:
```bash
# Verify system works in rolled-back state
# Start fresh session
# Test basic workflows
```

2. **Analyze Root Cause**:
```bash
# What went wrong?
# @import path issue?
# Syntax error?
# Claude Code version incompatible?
```

3. **Plan Fix**:
```bash
# Small incremental fix?
# Or wait for Claude Code update?
# Or modify approach (less aggressive modularization)?
```

4. **Re-apply Carefully**:
```bash
# After fixing root cause:
# Re-apply Phase 4-5 changes
# Test at each step
# Commit incrementally
```

---

## Recovery Strategies

### Strategy 1: Inline All Imports (Nuclear Option)

If @import fundamentally broken:

```bash
# 1. Backup current state
cp .claude/CLAUDE.md .claude/CLAUDE.md.modular-backup

# 2. Inline all 6 workflow docs into CLAUDE.md
# (Manual process - copy critical content from each)

# 3. Result: ~400-500 line CLAUDE.md
# (Still better than original 614, but loses progressive disclosure)

# 4. Remove @import statements

# 5. Test thoroughly
```

**When**: @import completely unsupported or broken
**Trade-off**: Lose progressive disclosure, but regain functionality

---

### Strategy 2: Reduce Import Count

If performance issues:

```bash
# Consolidate some workflow docs
# Example: Merge research + planning into single orchestration-workflows.md

# Reduce from 6 imports to 3-4
# Keep semantic-search separate (different domain)
```

**When**: Performance degradation from too many imports
**Trade-off**: Larger files, but fewer import operations

---

### Strategy 3: Hybrid Approach

Mix inline + @import:

```bash
# Keep most-accessed content inline in CLAUDE.md (hot path)
# @import only rarely-accessed content (cold path)

# Example:
# - Research workflow: Inline critical rules (~20 lines)
# - @import: Detailed examples, full keyword list

# Target: CLAUDE.md ~150 lines (50% over target but functional)
```

**When**: Can't get to <100 lines but want some modularization benefits
**Trade-off**: Partial solution, requires discipline to not grow further

---

## Getting Help

If issues persist after troubleshooting:

### 1. Document the Problem

```markdown
# Issue Report Template

**What I'm trying to do**: [test Phase 4-5, use research workflow, etc.]

**What's happening**: [error message, unexpected behavior, etc.]

**Expected behavior**: [what should happen]

**Steps to reproduce**:
1. [step 1]
2. [step 2]
3. [error occurs]

**Environment**:
- Claude Code version: [version]
- OS: [macOS/Linux/Windows]
- Git status: [clean/modified/etc.]

**Diagnostics run**:
- [ ] Syntax validation (passed/failed)
- [ ] Path verification (passed/failed)
- [ ] Fresh session test (passed/failed)
- [ ] Git diff check (what changed?)

**Attempted fixes**:
- [what I tried]
- [results]
```

### 2. Check Git History

```bash
# Review recent changes
git log --oneline -10 --decorate

# Check specific file history
git log --follow .claude/CLAUDE.md

# See what changed in specific commit
git show acfec8a
```

### 3. Test in Isolation

```bash
# Comment out imports one by one to identify problematic one
# Edit CLAUDE.md:

# @import ../docs/workflows/research-workflow.md  # WORKS
# @import ../docs/workflows/planning-workflow.md  # TEST THIS
## @import ../docs/workflows/compound-request-handling.md  # COMMENTED OUT
## @import ../docs/workflows/semantic-search-hierarchy.md  # COMMENTED OUT
# ... etc

# Test after each change to isolate issue
```

### 4. Compare with Known Good State

```bash
# Checkout clean version in new directory
cd /tmp
git clone /path/to/repo repo-clean
cd repo-clean
git checkout 4886046  # Phase 4 (known good)

# Compare files
diff /tmp/repo-clean/.claude/CLAUDE.md /path/to/repo/.claude/CLAUDE.md
```

---

**For testing procedures**: See `docs/guides/testing-guide.md`
**For maintenance procedures**: See `docs/guides/maintenance-guide.md`
**For design decisions**: See `docs/adrs/001-modular-claude-md.md`
