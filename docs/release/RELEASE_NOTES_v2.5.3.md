# Release Notes v2.5.3

**Release Date:** December 22, 2025

## Overview

This release adds CLAUDE.md automation for skill discovery and fixes critical stdout buffering issues in hooks that prevented output from appearing during fresh clone setup.

## Changes

### Bug Fixes

#### Fix stdout Buffering in Hooks
- **Problem:** Hook output wasn't appearing during fresh clone setup, making it seem like the process was hanging
- **Root Cause:** Python uses full buffering (not line buffering) when running as a subprocess
- **Fix:** Added `flush=True` to all print statements and `sys.stdout.flush()` before exit
- **Files:** `.claude/hooks/first-prompt-reindex.py`

#### Fix stdin Inheritance in Background Processes
- **Problem:** Background reindex process could potentially block on stdin inheritance
- **Fix:** Added `stdin=subprocess.DEVNULL` to Popen call in `spawn_background_reindex()`
- **Files:** `.claude/utils/reindex_manager.py`

### New Features

#### CLAUDE.md Automation for Skill Discovery
- **New Function:** `setup_claude_md()` - Creates or updates `.claude/CLAUDE.md` with skill documentation
- **New Function:** `verify_claude_md()` - Checks if skill instructions are present
- **Integration:** Added to `repair_setup()` and `verify_only()` flows
- **Idempotent:** Skips if instructions already exist (supports both simplified and full versions)
- **Files:** `setup.py`

#### Post-Installation Documentation
- Added "Post-Installation: CLAUDE.md Setup" section to README
- Explains how to add skill instructions for Options 2 & 3 installations
- **Files:** `README.md`

## Upgrade Notes

### From v2.5.2

No breaking changes. Simply pull the latest changes:

```bash
git pull origin main
```

To update CLAUDE.md in existing installations:

```bash
python3 setup.py --repair
```

## Technical Details

### Commits Included

| Commit | Type | Description |
|--------|------|-------------|
| bfd06cf | fix | Fix stdout buffering and stdin inheritance in hooks |
| c34b7e7 | feat | Add CLAUDE.md automation for skill discovery |

### Files Changed

- `.claude/hooks/first-prompt-reindex.py` - stdout buffering fix
- `.claude/utils/reindex_manager.py` - stdin inheritance fix
- `setup.py` - CLAUDE.md automation functions
- `README.md` - Post-Installation documentation

## Contributors

- Claude Code (Anthropic)
