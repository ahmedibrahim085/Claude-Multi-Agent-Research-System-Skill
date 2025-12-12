# Claim File Path Correction

**Date:** 2025-12-12
**Issue:** Documentation shows incorrect claim file path
**Impact:** Developers reading docs will look in wrong location for debugging

---

## The Problem

**Documentation (WRONG):**
```python
claim_file = project_path / '.claude' / 'skills' / 'semantic-search' / '.reindex-claim'
# Example: /path/to/project/.claude/skills/semantic-search/.reindex-claim
```

**Code (CORRECT):**
```python
storage_dir = get_project_storage_dir(project_path)
claim_file = storage_dir / '.reindex_claim'
# Example: ~/.claude_code_search/projects/my_project_abc123/.reindex_claim
```

---

## Two Errors

### 1. Wrong Directory
- ❌ **Docs say:** Inside project directory (`.claude/skills/semantic-search/`)
- ✅ **Reality:** In user's home directory (`~/.claude_code_search/projects/{name}_{hash}/`)

### 2. Wrong Filename
- ❌ **Docs say:** `.reindex-claim` (dash)
- ✅ **Reality:** `.reindex_claim` (underscore)

---

## Correct Path Formula

```python
# Step 1: Get storage directory
from pathlib import Path
import hashlib

def get_project_storage_dir(project_path: Path) -> Path:
    """Returns: ~/.claude_code_search/projects/{project_name}_{hash}/"""
    project_name = project_path.name
    project_hash = hashlib.sha256(str(project_path).encode()).hexdigest()[:8]

    storage_base = Path.home() / '.claude_code_search' / 'projects'
    return storage_base / f"{project_name}_{project_hash}"

# Step 2: Get claim file
storage_dir = get_project_storage_dir(Path.cwd())
claim_file = storage_dir / '.reindex_claim'  # underscore!
```

**Example:**
```
Project: /Users/alice/projects/my-app
Storage: ~/.claude_code_search/projects/my-app_a1b2c3d4/
Claim:   ~/.claude_code_search/projects/my-app_a1b2c3d4/.reindex_claim
```

---

## How to Find Your Claim File

**For Current Project:**
```bash
# Get project name
basename $(pwd)

# Get project hash (first 8 chars of SHA256)
echo -n "$(pwd)" | shasum -a 256 | cut -c1-8

# Construct path
ls -la ~/.claude_code_search/projects/$(basename $(pwd))_$(echo -n "$(pwd)" | shasum -a 256 | cut -c1-8)/.reindex_claim
```

**Or use Python:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / '.claude' / 'utils'))
import reindex_manager

storage_dir = reindex_manager.get_project_storage_dir(Path.cwd())
claim_file = storage_dir / '.reindex_claim'
print(f"Claim file location: {claim_file}")
```

---

## Files Affected

**Documentation files with wrong path:**
1. `docs/implementation/stop-hook-background-migration-plan.md:244`
2. `docs/testing/ULTRA-DEEP-VERIFICATION-FINAL-REPORT.md:448`
3. `docs/testing/STOP-HOOK-MIGRATION-GLOBAL-VERIFICATION.md:75, 197`
4. `docs/testing/STOP-HOOK-MIGRATION-COMPLETE-VERIFICATION.md:212, 299`

**All fixed in this commit.**

---

## Why This Matters

**For Debugging:**
- If you're looking for the claim file to debug concurrent processes
- You need to check the CORRECT location

**For Development:**
- Code that hardcodes the wrong path will fail
- Tests that mock the wrong path will pass but not test reality

**For Documentation:**
- Developers trust docs - wrong info wastes time

---

## Verification

**Check claim file exists:**
```bash
# After triggering a reindex
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, '.claude/utils')
import reindex_manager
claim = reindex_manager.get_project_storage_dir(Path.cwd()) / '.reindex_claim'
print(f'Claim file: {claim}')
print(f'Exists: {claim.exists()}')
if claim.exists():
    print(f'Content: {claim.read_text().strip()}')
"
```

**Output example:**
```
Claim file: /Users/alice/.claude_code_search/projects/my-app_a1b2c3d4/.reindex_claim
Exists: True
Content: 12345:2025-12-12T15:30:00Z
```

---

**Status:** ✅ Documentation updated to match code
**Date:** 2025-12-12
