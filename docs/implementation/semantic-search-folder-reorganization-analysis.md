# Semantic-Search Folder Reorganization Analysis

**Date**: 2025-12-01
**Purpose**: Align semantic-search skill folder structure with project conventions
**References**: multi-agent-researcher, spec-workflow-orchestrator skills

---

## Current State Analysis

### Project-Level Conventions (from research/spec skills)

**Directory Structure**:
```
project-root/
├── .claude/
│   ├── config.json                    # Central configuration
│   ├── agents/                        # Agent definitions
│   ├── skills/                        # Skill orchestrators (minimal)
│   │   ├── multi-agent-researcher/
│   │   │   ├── SKILL.md              # Orchestration instructions
│   │   │   ├── examples.md           # Usage examples
│   │   │   └── reference.md          # Reference documentation
│   │   └── spec-workflow-orchestrator/
│   │       ├── SKILL.md              # Orchestration instructions
│   │       ├── examples.md           # Usage examples
│   │       ├── reference.md          # Reference documentation
│   │       └── docs/                 # Optional: Additional documentation
│   ├── hooks/                        # Project-level hooks
│   └── utils/                        # Shared utilities
├── files/                            # Skill outputs
│   ├── research_notes/              # Research agent outputs
│   └── reports/                     # Synthesis reports
├── logs/                            # All session logs (project-wide)
│   ├── session_*_transcript.txt
│   ├── session_*_tool_calls.jsonl
│   ├── session_*_state.json
│   └── state/                       # Current state tracking
│       ├── current.json             # Current skill/research
│       ├── research-workflow-state.json
│       └── spec-workflow-state.json
└── docs/                           # Project documentation
    └── implementation/              # Implementation notes
```

**Key Patterns Identified**:

1. **Skills are MINIMAL** - Only orchestration logic, no execution code
2. **Logs at PROJECT level** - `logs/` directory, not skill-specific
3. **State at PROJECT level** - `logs/state/` for all state files
4. **Outputs at PROJECT level** - `files/` for skill outputs
5. **Config centralized** - `.claude/config.json` defines all paths
6. **Agents separate** - `.claude/agents/` for agent definitions
7. **Utilities shared** - `.claude/utils/` for common code

---

## Semantic-Search Current Structure (INCORRECT)

### Project-Level (`.claude/skills/semantic-search/`)
```
.claude/skills/semantic-search/
├── SKILL.md                         ✅ Correct: Orchestration instructions
├── deploy-skill.sh                  ❌ Should not be in skill directory
├── .gitignore                       ❌ Skill-specific, not project-level
├── .DS_Store                        ❌ macOS artifact (should be gitignored)
├── logs/                            ❌ WRONG: Should be at project level
│   ├── session_*_transcript.txt    ❌ Belongs in project logs/
│   ├── session_*_tool_calls.jsonl  ❌ Belongs in project logs/
│   └── state/                       ❌ Belongs in project logs/state/
│       └── current.json             ❌ Belongs in project logs/state/
├── scripts/                         ⚠️  UNIQUE: Bash orchestrators (semantic-search specific)
│   ├── index
│   ├── search
│   ├── status
│   ├── find-similar
│   └── list-projects
├── tests/                           ⚠️  UNIQUE: Test files (semantic-search specific)
│   ├── test_search.py
│   ├── test_status.py
│   ├── test_find_similar.py
│   ├── test_integration.py
│   └── test_utils.py
├── references/                      ✅ Acceptable: Skill-specific documentation
│   ├── effective-queries.md
│   ├── performance-tuning.md
│   ├── troubleshooting.md
│   └── api-stability.md
├── .benchmarks/                     ❌ Should be at project level if needed
└── .code-search-index/              ❌ Should be at project level or in global location
```

### User-Level (`~/.claude/skills/semantic-search/`)
```
~/.claude/skills/semantic-search/
├── SKILL.md                         ✅ Managed skill copy
├── scripts/                         ✅ Needed: Agents call these
├── tests/                           ✅ Needed: Verify functionality
├── references/                      ✅ Needed: Documentation
├── logs/                            ❌ WRONG: Should use project logs/
└── .benchmarks/                     ❌ Not needed at user level
```

---

## Problems Identified

### Critical Issues

1. **Logs in Wrong Location**
   - Current: `.claude/skills/semantic-search/logs/`
   - Correct: `logs/` (project root)
   - Impact: Session logs not aggregated with other skills
   - Violates: Project-wide logging convention

2. **State in Wrong Location**
   - Current: `.claude/skills/semantic-search/logs/state/current.json`
   - Correct: `logs/state/current.json` (project root)
   - Impact: State not tracked in central location
   - Violates: Centralized state management

3. **Deploy Script in Skill Directory**
   - Current: `.claude/skills/semantic-search/deploy-skill.sh`
   - Correct: Should be in project root scripts/ or .claude/scripts/
   - Impact: Confuses skill orchestration with deployment
   - Violates: Skill minimality principle

4. **Skill-Specific .gitignore**
   - Current: `.claude/skills/semantic-search/.gitignore`
   - Correct: Entries should be in project root .gitignore
   - Impact: Git configuration scattered
   - Violates: Centralized configuration

### Design Questions

1. **Where should `scripts/` live?**
   - Agents need to call these bash scripts
   - Scripts wrap claude-context-local MCP server
   - Options:
     a) Keep in skill directory (agents know where to find them)
     b) Move to `.claude/skills/semantic-search/scripts/` (still within skill)
     c) Move to project root `scripts/semantic-search/`
   - **Recommendation**: Keep in skill directory (unique to semantic-search)

2. **Where should `tests/` live?**
   - Tests verify bash script functionality
   - Not part of project test suite (specific to skill)
   - Options:
     a) Keep in skill directory
     b) Move to project root `tests/semantic-search/`
   - **Recommendation**: Keep in skill directory (skill-specific tests)

3. **Where should `references/` live?**
   - Skill-specific documentation (effective queries, performance)
   - Similar to examples.md, reference.md in other skills
   - **Recommendation**: Keep in skill directory

4. **Where should `.benchmarks/` and `.code-search-index/` live?**
   - These are development artifacts
   - .benchmarks: Performance testing data
   - .code-search-index: Test index for development
   - **Recommendation**: Add to .gitignore, keep local only

---

## Proposed New Structure

### Project-Level (`.claude/skills/semantic-search/`)

**After Reorganization**:
```
.claude/skills/semantic-search/
├── SKILL.md                         # Orchestration instructions
├── scripts/                         # Bash orchestrators (KEEP - agents use these)
│   ├── index
│   ├── search
│   ├── status
│   ├── find-similar
│   └── list-projects
├── tests/                           # Skill-specific tests (KEEP)
│   ├── test_search.py
│   ├── test_status.py
│   ├── test_find_similar.py
│   ├── test_integration.py
│   └── test_utils.py
├── references/                      # Documentation (KEEP)
│   ├── effective-queries.md
│   ├── performance-tuning.md
│   ├── troubleshooting.md
│   └── api-stability.md
└── .gitignore                       # Skill-specific ignores (MINIMAL)
```

**Skill-specific .gitignore**:
```gitignore
# Development artifacts (local only)
.benchmarks/
.code-search-index/
__pycache__/
*.pyc
.DS_Store

# Test outputs (generated during testing)
.pytest_cache/
*.log
```

### Project Root Changes

**logs/** (no changes needed - already correct):
```
logs/
├── session_*_transcript.txt         # All session logs
├── session_*_tool_calls.jsonl
├── session_*_state.json
└── state/                           # State tracking
    ├── current.json                 # Used by all skills
    ├── research-workflow-state.json
    └── spec-workflow-state.json
```

**scripts/** (NEW - for deployment utilities):
```
scripts/                             # NEW: Project-level scripts
└── deploy-semantic-search.sh       # MOVE: from skill directory
```

**.gitignore** (ADD semantic-search artifacts):
```gitignore
# Semantic-search artifacts
.claude/skills/semantic-search/.benchmarks/
.claude/skills/semantic-search/.code-search-index/
.claude/skills/semantic-search/__pycache__/
```

---

## Migration Plan

### Phase 1: Remove Incorrect Files

1. **Delete logs/ from skill directory**
   ```bash
   rm -rf .claude/skills/semantic-search/logs/
   ```
   - ✅ Session logs already exist in project logs/
   - ✅ State file (current.json) already exists in project logs/state/
   - Impact: Removes 150+ old log files from wrong location

2. **Move deploy-skill.sh to project scripts/**
   ```bash
   mkdir -p scripts
   mv .claude/skills/semantic-search/deploy-skill.sh scripts/deploy-semantic-search.sh
   ```

3. **Delete development artifacts**
   ```bash
   rm -rf .claude/skills/semantic-search/.benchmarks/
   rm -rf .claude/skills/semantic-search/.code-search-index/
   ```

### Phase 2: Update .gitignore Files

1. **Create skill-specific .gitignore**
   ```bash
   cat > .claude/skills/semantic-search/.gitignore << 'EOF'
   # Development artifacts
   .benchmarks/
   .code-search-index/
   __pycache__/
   *.pyc
   .DS_Store
   .pytest_cache/
   *.log
   EOF
   ```

2. **Update project root .gitignore**
   ```bash
   echo "" >> .gitignore
   echo "# Semantic-search development artifacts" >> .gitignore
   echo ".claude/skills/semantic-search/.benchmarks/" >> .gitignore
   echo ".claude/skills/semantic-search/.code-search-index/" >> .gitignore
   echo ".claude/skills/semantic-search/__pycache__/" >> .gitignore
   ```

### Phase 3: User-Level Skill Sync

1. **Remove user-level logs/**
   ```bash
   rm -rf ~/.claude/skills/semantic-search/logs/
   ```

2. **Remove user-level development artifacts**
   ```bash
   rm -rf ~/.claude/skills/semantic-search/.benchmarks/
   rm -rf ~/.claude/skills/semantic-search/.code-search-index/
   ```

---

## Verification Checklist

After reorganization, verify:

### Structural Verification
- [ ] No logs/ directory in `.claude/skills/semantic-search/`
- [ ] No state/ directory in `.claude/skills/semantic-search/`
- [ ] deploy-skill.sh moved to `scripts/deploy-semantic-search.sh`
- [ ] .benchmarks/ and .code-search-index/ removed
- [ ] scripts/, tests/, references/ remain in skill directory
- [ ] .gitignore created in skill directory
- [ ] Project root .gitignore updated

### Functional Verification
- [ ] Agents can still find and execute scripts/
- [ ] Session logs appear in project logs/ (not skill logs/)
- [ ] State tracking uses logs/state/current.json
- [ ] Tests still pass (scripts/ in expected location)
- [ ] User-level skill synced with same structure

### Documentation Verification
- [ ] SKILL.md script paths still correct (relative to skill dir)
- [ ] Agent definitions reference correct script paths
- [ ] README updated if needed
- [ ] Implementation notes added to docs/

---

## Path References to Update

### Agent Definitions
Check `.claude/agents/semantic-search-{reader,indexer}.md`:
- Scripts referenced as `~/.claude/skills/semantic-search/scripts/*`
- Should remain unchanged (correct)

### SKILL.md
Check `.claude/skills/semantic-search/SKILL.md`:
- Example commands show `scripts/search`, `scripts/index` etc.
- These are relative to skill directory
- Should remain unchanged (correct)

### Hooks
Check `.claude/hooks/` if any reference semantic-search paths:
- No semantic-search-specific paths expected
- session_logger.py uses agent detection, not paths
- Should remain unchanged

---

## Comparison with Other Skills

### multi-agent-researcher
```
.claude/skills/multi-agent-researcher/
├── SKILL.md              # Minimal - only orchestration
├── examples.md           # Usage examples
└── reference.md          # Reference docs
```
- **No logs/** ✅
- **No scripts/** (agents write directly to files/)
- **No tests/** (logic in agents, not skill)
- **Minimal structure** ✅

### spec-workflow-orchestrator
```
.claude/skills/spec-workflow-orchestrator/
├── SKILL.md              # Minimal - only orchestration
├── examples.md           # Usage examples
├── reference.md          # Reference docs
└── docs/                 # Optional: Additional docs
    └── reference/
```
- **No logs/** ✅
- **No scripts/** (agents write directly, use .claude/utils/)
- **No tests/** (logic in agents, not skill)
- **Minimal + optional docs** ✅

### semantic-search (UNIQUE NEEDS)
```
.claude/skills/semantic-search/
├── SKILL.md              # Minimal - only orchestration
├── scripts/              # UNIQUE: Bash orchestrators for MCP wrapper
├── tests/                # UNIQUE: Tests for bash scripts
└── references/           # UNIQUE: Skill-specific query docs
```
- **No logs/** ✅ (after cleanup)
- **Has scripts/** ⚠️ (JUSTIFIED - wraps external MCP server)
- **Has tests/** ⚠️ (JUSTIFIED - verifies bash scripts work)
- **Has references/** ⚠️ (JUSTIFIED - skill-specific docs)

**Why semantic-search is different**:
1. Wraps external tool (claude-context-local MCP server)
2. Uses bash scripts as orchestrators (not pure Python agents)
3. Requires skill-specific documentation (query patterns, performance)
4. Needs tests for bash script functionality

**Justified exceptions**:
- scripts/: Agents need to call these to interact with MCP server
- tests/: Verify bash scripts work correctly
- references/: Skill-specific usage documentation

---

## Summary

### Changes Required

| Item | Current Location | New Location | Action |
|------|-----------------|--------------|--------|
| Session logs | `.claude/skills/semantic-search/logs/` | `logs/` | DELETE (already in logs/) |
| State files | `.claude/skills/semantic-search/logs/state/` | `logs/state/` | DELETE (already in logs/state/) |
| deploy-skill.sh | `.claude/skills/semantic-search/` | `scripts/` | MOVE |
| .benchmarks/ | `.claude/skills/semantic-search/` | (deleted) | DELETE |
| .code-search-index/ | `.claude/skills/semantic-search/` | (deleted) | DELETE |
| scripts/ | `.claude/skills/semantic-search/` | (stay) | KEEP |
| tests/ | `.claude/skills/semantic-search/` | (stay) | KEEP |
| references/ | `.claude/skills/semantic-search/` | (stay) | KEEP |

### Principles Applied

1. ✅ **Logs at project level** - All session logs in logs/
2. ✅ **State at project level** - All state in logs/state/
3. ✅ **Minimal skill directory** - Only orchestration + skill-specific tools
4. ✅ **Justified exceptions** - scripts/, tests/, references/ serve specific purpose
5. ✅ **Centralized configuration** - .gitignore rules at project level
6. ✅ **No duplication** - Remove redundant logs/state

### Expected Outcome

After reorganization:
- **Logs**: All in `logs/` (consistent with other skills)
- **State**: All in `logs/state/` (consistent with other skills)
- **Scripts**: In skill dir (unique to semantic-search, needed by agents)
- **Tests**: In skill dir (verify bash scripts work)
- **Docs**: In references/ (skill-specific usage patterns)
- **Clean structure**: Aligned with project conventions while respecting unique needs

**Status**: Ready for implementation
