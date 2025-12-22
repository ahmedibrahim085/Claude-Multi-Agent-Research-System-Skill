# Release Notes v2.5.4

**Release Date:** December 22, 2025

## Overview

This release fixes fresh clone crashes and reduces semantic-search trigger keywords to eliminate overlap with the multi-agent-researcher skill.

## Changes

### Bug Fixes

#### P0: Fresh Clone Crashes Fixed
- **Problem:** Fresh clones crashed when storage directory didn't exist
- **Root Cause:** `_acquire_reindex_lock()` in reindex_manager.py didn't create the storage directory
- **Fix:** Added `storage_dir.mkdir(parents=True, exist_ok=True)` before lock file creation

#### Debug Logging Added
- Added traceback logging to stderr in first-prompt-reindex.py exception handler
- Previously exceptions were silently swallowed, making debugging impossible
- Added `state_dir.mkdir()` safety check to ensure logs/state exists

### Refactoring

#### Semantic-Search Trigger Keywords Reduced (YAGNI)
- **Before:** 70 keywords, 28 intent patterns
- **After:** 49 keywords, 17 intent patterns
- **Reduction:** 30% keywords, 39% patterns

**Removed (overlapped with multi-agent-researcher):**
- Generic questions: "how does", "how is", "where is", "what is", "show me"
- Explanations: "explain the code", "explain implementation"
- Similarity: "find similar", "similar to", "like this", "related to"
- References: "identify instances", "all occurrences of", "where else", "show all references", "used by"

**Kept (unambiguous semantic-search triggers):**
- Indexing operations (18 keywords)
- Explicit codebase references (16 keywords)
- Documentation search (15 keywords)

## Upgrade Notes

No breaking changes. Pull the latest:

```bash
git pull origin main
```

## Technical Details

### Commits Included

| Commit | Type | Description |
|--------|------|-------------|
| 7551369 | fix | P0 - Fix fresh clone crashes and add debug logging |
| 32b19df | refactor | Reduce trigger keywords from 70 to 49 |

### Files Changed

- `.claude/utils/reindex_manager.py` - Storage directory auto-creation
- `.claude/hooks/first-prompt-reindex.py` - Debug logging, state dir safety
- `.claude/skills/skill-rules.json` - Reduced semantic-search triggers

## Contributors

- Claude Code (Anthropic)
