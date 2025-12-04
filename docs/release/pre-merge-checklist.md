# Pre-Merge Checklist for Feature Branch → Main

**Branch:** `feature/searching-code-semantically-skill`
**Target:** `main`
**Version:** v2.4.0 (confirmed via semantic versioning analysis)
**Date:** December 4, 2025
**Commits:** 96 commits across 7 development phases

---

## 🎯 Critical Priority (Do First)

These items must pass before proceeding with other checks:

- [ ] **Test fresh clone experience (End-to-End)**
  - Clone repo in temp directory as new user
  - Follow setup instructions from scratch
  - Test: `git clone → setup → first use`
  - Verify all prerequisites install correctly
  - Verify first skill invocation works
  - **Location:** Any temp directory outside project
  - **Why Critical:** If new users can't set up, nothing else matters

- [ ] **Verify auto-reindex tracing logs appear**
  - Create/edit a file in current session
  - Check `logs/session_*_transcript.txt` for AUTO-REINDEX entries
  - Verify skip reasons are logged (cooldown, pattern, etc.)
  - Verify run success is logged
  - **Location:** Current session transcript
  - **Why Critical:** Just implemented (commit e446cba), must verify it works

- [ ] **Test all skills work correctly**
  - semantic-search: Index, search, verify results
  - multi-agent-researcher: Full workflow with report synthesis
  - spec-workflow-orchestrator: analyst → architect → planner
  - **Location:** Test in real scenarios
  - **Why Critical:** Core product features

---

## 🧹 Cleanup Phase

- [ ] **Archive unnecessary files**
  - Test files created during development
  - Temporary documentation
  - Orphaned files from YAGNI removals
  - **Check:** `docs/testing/`, any `test-*` files
  - **Action:** Move to archive or delete

- [ ] **Update broken links and references**
  - Links to removed notebook support
  - References to deleted files
  - Internal doc cross-references
  - **Check:** All `*.md` files for `[...](..)` patterns
  - **Tools:** `grep -r "\.md" docs/ .claude/`

- [ ] **Search codebase for TODO, FIXME, HACK, XXX comments**
  - Review each one - resolve or document
  - Create issues for deferred items
  - **Command:** `grep -rn "TODO\|FIXME\|HACK\|XXX" .claude/ docs/ --exclude-dir=node_modules`

- [ ] **Check for hardcoded paths or user-specific configurations**
  - Look for `/Users/ahmedmaged/` or similar
  - Ensure all paths use `get_project_root()` or relative paths
  - **Check:** Python files, shell scripts, config files

- [ ] **Verify no debug code or console.log left in production**
  - Remove temporary print statements
  - Remove debug-only code blocks
  - Check for `console.log`, `print("DEBUG:")`, etc.
  - **Exclude:** Intentional logging (session_logger, etc.)

- [ ] **Check for duplicate code or files**
  - Look for copied/pasted functions
  - Check for backup files (`file.py.bak`, `old_*`)
  - **Tools:** Manual review + `find . -name "*.bak" -o -name "*~"`

- [ ] **Validate .gitignore is complete**
  - Covers all generated files (*.pyc, __pycache__, etc.)
  - Covers MCP caches and indexes
  - Covers session logs (already in?)
  - Covers OS files (.DS_Store, Thumbs.db)
  - **Test:** `git status` should show only tracked changes

- [ ] **Verify no sensitive data in git history**
  - No API keys, tokens, passwords
  - No personal information
  - No internal/proprietary data
  - **Tools:** `git log --all -p | grep -i "password\|api_key\|secret"`

---

## 🏗️ Architecture & Structure Review

- [ ] **Review project architecture against Claude Code standards**
  - Verify hooks structure matches official docs
  - Verify skills structure matches official docs
  - Verify utils organization follows best practices
  - **Reference:** Claude Code documentation (use claude-code-guide agent)

- [ ] **Verify file/folder structure aligns with official documentation**
  - `.claude/` structure correct
  - `docs/` organization logical
  - Scripts have proper locations
  - **Command:** Use `/verify-structure` slash command

- [ ] **Review commit history for quality**
  - Check commit messages are clear
  - Consider squashing WIP commits
  - Ensure clean, linear history
  - **Command:** `git log --oneline --graph`
  - **Note:** 96 commits - may need cleanup

---

## 📚 Documentation Phase

- [ ] **Update README.md with latest features**
  - Add semantic search feature
  - Add auto-reindex capability
  - Add multi-agent research workflow
  - Add spec workflow orchestrator
  - Update feature list, capabilities, screenshots

- [ ] **Validate installation instructions for fresh clone**
  - Step-by-step setup guide
  - Prerequisites list (Python, MCP, models)
  - Configuration steps
  - First-run instructions
  - **Test:** Follow your own README on fresh clone

- [ ] **Test prerequisites setup flow for new users**
  - MCP server installation
  - sentence-transformers package
  - Model download (google/embeddinggemma-300m)
  - Prerequisites state file creation
  - **Verify:** User gets clear feedback at each step

- [ ] **Verify configuration instructions are complete**
  - `.claude/config.json` setup
  - `settings.json` hook configuration
  - Cooldown tuning guidance
  - File pattern customization
  - **Check:** All configs documented in docs/configuration/

- [ ] **Verify all workflow documentation is accurate**
  - Research workflow (docs/workflows/research-workflow.md)
  - Planning workflow (docs/workflows/planning-workflow.md)
  - Semantic search hierarchy (docs/workflows/semantic-search-hierarchy.md)
  - Compound request handling
  - **Action:** Read each, verify against actual implementation

- [ ] **Update or create CONTRIBUTING.md guidelines**
  - How to contribute
  - Code style guidelines
  - PR process
  - Testing requirements
  - **Location:** Root or docs/

- [ ] **Verify LICENSE file is present and correct**
  - Check license type (MIT, Apache, etc.)
  - Verify copyright year (2025)
  - Verify author/organization
  - **Location:** Root LICENSE file

- [ ] **Create/update CHANGELOG.md with all changes**
  - All 96 commits summarized
  - Organized by type (Features, Fixes, Docs, etc.)
  - Breaking changes highlighted
  - **Format:** Keep-a-Changelog format
  - **Source:** `docs/history/feature-branch-semantic-search-timeline.md`

- [ ] **Update project badges in README (if applicable)**
  - Build status
  - License badge
  - Version badge
  - Coverage badge (if tests exist)

- [ ] **Verify all examples in documentation work correctly**
  - Code snippets are accurate
  - Commands execute successfully
  - Expected outputs match reality
  - **Check:** All code blocks in `*.md` files

- [ ] **Review and update issue templates (if any)**
  - Bug report template
  - Feature request template
  - **Location:** `.github/ISSUE_TEMPLATE/`

- [ ] **Review and update PR templates (if any)**
  - PR description template
  - Checklist for contributors
  - **Location:** `.github/PULL_REQUEST_TEMPLATE.md`

---

## 🧪 Testing Phase

- [ ] **Test all slash commands work correctly**
  - `/project-status`
  - `/plan-feature`
  - `/verify-structure`
  - `/research-topic`
  - **Method:** Execute each in live session

- [ ] **Test all hooks fire correctly**
  - session-start (startup, resume, clear, compact)
  - post-tool-use (Write, Edit, Skill invocations)
  - user-prompt-submit (research/planning triggers)
  - **Check:** Session logs show hook executions

- [ ] **Performance test auto-reindex**
  - Full reindex: Verify ~225s for ~200 files
  - Incremental: Verify ~5s for single file
  - Cooldown: Verify skip during cooldown period
  - **Metrics:** Time, files processed, chunks indexed

- [ ] **Test error scenarios**
  - Missing prerequisites (state file false)
  - Corrupted state files
  - Missing index
  - Concurrent reindex attempts
  - File permission errors
  - **Verify:** Graceful degradation, clear error messages

- [ ] **Verify cross-platform compatibility**
  - macOS: Primary development platform (verified)
  - Linux: Test if accessible
  - Windows: Document limitations if any
  - **Focus:** Path handling, script shebangs

- [ ] **Security review**
  - File operations use safe paths (no directory traversal)
  - Script execution doesn't allow injection
  - No exposed secrets or credentials
  - User input sanitized where applicable
  - **Check:** All file I/O, subprocess calls

- [ ] **Verify all error handling is production-ready**
  - Try/except blocks present
  - Errors logged appropriately
  - User gets actionable feedback
  - No silent failures
  - **Check:** All Python scripts, hook files

- [ ] **Check logging levels are appropriate**
  - Not too verbose (spam)
  - Not too silent (blind)
  - Info/Debug/Error used correctly
  - **Verify:** Session transcript readability

---

## 🚀 Release Preparation

- [ ] **Create ultra-detailed release notes**
  - Major features with descriptions
  - Statistics (96 commits, 39 files, ~7,700 lines)
  - Breaking changes clearly marked
  - Bug fixes grouped by category
  - Contributors acknowledged
  - **Template:** See structure below
  - **Source:** `docs/history/feature-branch-semantic-search-timeline.md`

- [ ] **Version bump and create git tag**
  - Update version to v2.4.0 ✅ (semver verified: MINOR bump for features, no breaking changes)
  - Create annotated tag: `git tag -a v2.4.0 -m "message"`
  - Tag message includes feature summary
  - **Verify:** Semantic versioning (major.minor.patch) ✅ Correct

- [ ] **Verify backward compatibility or document breaking changes**
  - Skill invocation changes?
  - Hook configuration changes?
  - Config file structure changes?
  - API/interface changes?
  - **Action:** Document migration path if breaking

- [ ] **Create migration guide if breaking changes exist**
  - Step-by-step upgrade instructions
  - Config file migration examples
  - Deprecated feature alternatives
  - **Location:** `docs/release/MIGRATION-v2-to-v3.md`

- [ ] **Check dependency versions**
  - Python version requirement
  - sentence-transformers version
  - MCP server version compatibility
  - **Action:** Pin or range appropriately in docs

- [ ] **Verify all scripts have proper shebang and execute permissions**
  - `#!/usr/bin/env python3` for Python scripts
  - `#!/bin/bash` for shell scripts
  - Execute permissions: `chmod +x`
  - **Check:** All files in `.claude/hooks/`, `.claude/skills/*/scripts/`

---

## 📋 Additional Checks

- [ ] **Verify all config files have .example templates**
  - `.env.example` if env vars used
  - `config.json.example` for user customization
  - **Purpose:** Users know what to configure

- [ ] **Create troubleshooting guide**
  - Common errors and solutions
  - How to check prerequisites
  - How to debug auto-reindex
  - How to check hook execution
  - **Location:** `docs/guides/troubleshooting.md` or README section

- [ ] **Add Quick Start section to README**
  - Goal: < 5 minutes to first success
  - Essential steps only
  - Link to detailed docs
  - **Format:** Numbered steps, copy-paste commands

---

## 📊 Metrics to Include in Release Notes

**Performance:**
- Auto-reindex: Full (225s) vs Incremental (5.29s) = 42x improvement
- Token savings: Semantic search vs Grep = 90% reduction
- Example: 1 semantic search + 2 reads vs 15 Grep + 26 reads

**Code Stats:**
- 96 commits across 7 development phases
- 39 files added/modified
- ~7,700 lines of code
- 18 tests with 100% pass rate (if applicable)

**Triggers:**
- 90+ research trigger keywords
- 37+ planning trigger keywords
- 5 production utility scripts
- 4 slash commands

**Known Limitations:**
- MCP server: 15 file extensions only (no .ipynb)
- Hooks: May not fire in resumed sessions (platform limitation)
- Auto-reindex: 300s default cooldown (tune per project)

---

## 🎯 Release Notes Template

```markdown
# v2.4.0 - Multi-Skill Orchestration Platform

**Release Date:** December 4, 2025
**Branch:** feature/searching-code-semantically-skill (96 commits)

---

## 🎉 Major Features

### Semantic Search Skill
FAISS-based vector search with massive efficiency gains over traditional keyword search.

**Features:**
- Auto-reindex on file modifications (42x faster incremental vs full)
- Comprehensive decision tracing for debugging
- 90% token savings vs traditional Grep exploration
- Smart file filtering (include/exclude patterns)
- Cooldown mechanism prevents rapid reindex spam

**Performance:**
- Full reindex: ~225s for 196 files, 5755 chunks
- Incremental: ~5s for single file modification
- Example savings: 1 search + 2 reads vs 15 Grep + 26 reads

### Multi-Agent Research Workflow
Orchestrate 2-4 specialized researcher agents in parallel, synthesize findings into comprehensive reports.

**Features:**
- Parallel researcher coordination
- Mandatory report-writer synthesis
- Quality gates with 85% threshold
- 90+ trigger keywords for auto-activation

### Spec Workflow Orchestrator
From ideation to development-ready specifications via 3-agent pipeline.

**Features:**
- spec-analyst: Requirements gathering, user stories
- spec-architect: System design, ADRs, tech stack
- spec-planner: Task breakdown, implementation plan
- Quality gates (85% threshold, 3 iterations max)
- Per-project directory structure
- Interactive decision flow (New/Refine/Archive)
- Archive system with integrity verification

---

## 🏗️ Infrastructure

**Universal Skill Activation:**
- Hook-based auto-detection (user-prompt-submit)
- 90+ research triggers, 37+ planning triggers
- Compound request handling with user clarification

**Auto-Reindex System:**
- Session-start auto-reindex (startup/resume triggers)
- Post-tool-use auto-reindex (Write/Edit triggers)
- Comprehensive decision tracing (NEW in e446cba)
- File filtering: 4-layer logic (include, exclude dirs, exclude patterns, cooldown)
- Cooldown: Configurable per-project (default 300s)

**Session Logging:**
- Transcript: Human-readable tool call log
- JSONL: Structured tool call data
- State: Per-session research/planning tracking
- Auto-reindex decisions: Full visibility for debugging

**Testing & Quality:**
- 18 tests with 100% pass rate
- 5 production utility scripts
- 4 slash commands

---

## 📊 Statistics

- **96 commits** across 7 development phases (Nov 28 - Dec 4, 2025)
- **39 files** added/modified
- **~7,700 lines** of code
- **7 phases:** Infrastructure → Integration → Cleanup → Modernization → Auto-Reindex → ADRs → YAGNI

---

## ⚠️ Breaking Changes

[Document any breaking changes from v2.x here]

**Migration Required:**
- [If config changes, list steps]
- [If hook setup changed, list steps]

---

## 🐛 Bug Fixes

**Auto-Reindex:**
- Fixed cooldown not respecting parameter override
- Fixed timezone-naive datetime comparison errors
- Fixed concurrent reindex handling (return None, not False)
- Fixed file filtering logic for logs/ directory

**Session Logging:**
- Fixed state loading failures breaking reindex
- Fixed session ID not initialized on logging failure

**YAGNI Removals:**
- Removed notebook support (no .ipynb files in project)
- Removed NotebookEdit trigger (unused)

---

## 📚 Documentation

**New Documentation:**
- `docs/history/feature-branch-semantic-search-timeline.md` - Complete development timeline
- `docs/architecture/ADR-001-direct-script-vs-agent-for-auto-reindex.md` - Architecture decision
- `docs/architecture/auto-reindex-design-quick-reference.md` - Quick reference guide
- `docs/workflows/semantic-search-hierarchy.md` - Search hierarchy workflow
- `docs/release/pre-merge-checklist.md` - This checklist

**Updated Documentation:**
- `docs/workflows/research-workflow.md` - Multi-agent research
- `docs/workflows/planning-workflow.md` - Spec workflow orchestrator
- `.claude/CLAUDE.md` - Project instructions with workflow imports

---

## 🚧 Known Limitations

1. **MCP Server File Support:**
   - Only 15 file extensions supported (.py, .js, .ts, .java, .go, .rs, .c, .cpp, .cs, .svelte, etc.)
   - No .ipynb notebook support (MCP backend limitation)

2. **Hook Execution:**
   - Hooks may not fire in resumed sessions after context compaction (Claude Code platform limitation)
   - Workaround: Manual reindex command available

3. **Auto-Reindex Cooldown:**
   - Default 300s cooldown may be too long/short for some projects
   - Users should tune via `.claude/config.json`

---

## 🎯 Upgrade Instructions

[If breaking changes exist, provide step-by-step upgrade guide]

1. Pull latest from main
2. Update config files (see migration guide)
3. Re-run prerequisites setup
4. Test auto-reindex in session

---

## 🙏 Contributors

[List contributors if applicable]

---

## 📎 Full Development Timeline

See `docs/history/feature-branch-semantic-search-timeline.md` for complete chronological breakdown of all 96 commits.
```

---

## ✅ Sign-Off

Once all items are checked:

- [ ] **Final review by maintainer(s)**
- [ ] **Approval from key stakeholders**
- [ ] **Create PR: feature/searching-code-semantically-skill → main**
- [ ] **Merge strategy decided** (merge commit, squash, rebase)
- [ ] **Post-merge verification plan** (smoke tests, monitoring)

---

## 📝 Notes

**Last Updated:** December 4, 2025
**Checklist Created By:** Claude Code
**Estimated Completion Time:** 8-12 hours (comprehensive review)

**Tips:**
- Check items off as you complete them: `- [x]`
- Add notes under items if needed
- Update this file as you discover additional requirements
- Commit this file to track progress

**Priority Order:**
1. Critical Priority items first
2. Testing Phase (catch issues early)
3. Cleanup Phase (remove cruft)
4. Documentation Phase (user-facing polish)
5. Release Preparation (final packaging)
