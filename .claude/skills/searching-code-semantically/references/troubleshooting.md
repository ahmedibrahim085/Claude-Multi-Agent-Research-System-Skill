# Troubleshooting Guide for Semantic Code Search

**Common issues, corner cases, and solutions for the searching-code-semantically skill.**

This guide addresses all known edge cases, compatibility issues, and failure modes. If you encounter errors, start here before filing issues.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Index Issues](#index-issues)
4. [Script Execution Errors](#script-execution-errors)
5. [Corner Case Documentation](#corner-case-documentation)
6. [Platform-Specific Issues](#platform-specific-issues)
7. [Error Message Reference](#error-message-reference)

---

## Quick Diagnostics

**Run this diagnostic checklist first:**

```bash
# 1. Check if global installation exists
ls -la ~/.local/share/claude-context-local  # macOS/Linux
# OR
ls -la %LOCALAPPDATA%\claude-context-local  # Windows

# 2. Check if index exists
ls -la .code-search-index/

# 3. Verify Python version
python --version  # Should be Python 3.8+

# 4. Test script executability
python .claude/skills/searching-code-semantically/scripts/status.py

# 5. Check for import errors
python -c "from pathlib import Path; import sys; import json; print('Imports OK')"
```

**If all checks pass but searches fail**: Issue is likely with index content or query formulation. See [effective-queries.md](effective-queries.md).

---

## Installation Issues

### Error: "Global installation not found"

**Full Error**:
```json
{
  "success": false,
  "error": "Global installation not found",
  "install_path": "/Users/username/.local/share/claude-context-local",
  "install_cmd": "curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash"
}
```

**Cause**: The `claude-context-local` MCP server is not installed globally.

**Solution**:
```bash
# macOS/Linux
curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash

# Windows (PowerShell)
# Download and run the Windows installer from the project repository
```

**Verification**:
```bash
# Check installation directory exists
ls ~/.local/share/claude-context-local  # macOS/Linux
ls %LOCALAPPDATA%\claude-context-local  # Windows

# Expected contents: search/, indexing/, and other Python modules
```

---

### Error: "Failed to import search module"

**Full Error**:
```json
{
  "success": false,
  "error": "Failed to import search module: No module named 'sqlitedict'",
  "suggestion": "Global installation may be corrupted. Reinstall."
}
```

**Cause**: Global installation is present but corrupted or incomplete.

**Solution 1** (Reinstall):
```bash
# Remove existing installation
rm -rf ~/.local/share/claude-context-local  # macOS/Linux

# Reinstall
curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash
```

**Solution 2** (Manual dependency install):
```bash
# If you have pip access to the global installation environment
cd ~/.local/share/claude-context-local
pip install -r requirements.txt
```

---

### Corner Case #2: Multiple Python Versions

**Symptom**: Script works in terminal but fails when invoked by Claude Code, or vice versa.

**Cause**: Different Python versions in different environments:
- Terminal uses: `python3.11`
- Claude Code uses: `python3.9`
- Global installation was built with: `python3.10`

**Diagnosis**:
```bash
# Check which Python is being used
which python
which python3
python --version
python3 --version

# Check script shebang
head -1 .claude/skills/searching-code-semantically/scripts/search.py
# Should show: #!/usr/bin/env python3
```

**Solution**: Ensure global installation uses the same Python as your scripts.

```bash
# Reinstall using specific Python version
python3.11 -m pip install <package-name>

# Or update shebang in scripts to match
# Change: #!/usr/bin/env python3
# To: #!/usr/bin/env python3.11
```

**Prevention**: Always use `#!/usr/bin/env python3` (not `python`) and ensure `python3` symlink points to your preferred version:

```bash
# Check symlink
ls -la $(which python3)

# Update if needed (macOS example)
brew link python@3.11
```

**Note**: This skill's scripts use `#!/usr/bin/env python3` for maximum compatibility, but cannot guarantee cross-version compatibility if the global installation's dependencies differ.

---

## Index Issues

### Error: "Index not found"

**Full Error**:
```json
{
  "success": false,
  "error": "Index not found",
  "suggestion": "Run indexing first or check storage-dir path",
  "path": ".code-search-index"
}
```

**Cause**: No index exists at the specified path (default: `.code-search-index/`).

**Solution**: This skill does NOT create indexes. You must use the MCP server directly to index the codebase first.

**Indexing via MCP Server** (outside this skill):
```bash
# Option 1: Use Claude Code with MCP server enabled
# The MCP server provides index_directory tool

# Option 2: Use MCP server CLI directly
# (Check claude-context-local documentation for CLI usage)
```

**After indexing**, verify index exists:
```bash
ls -la .code-search-index/

# Expected files:
# - vector_store.db (SQLite database)
# - file_mappings.json
# - metadata.json
```

---

### Error: "Index corrupted" or "Unexpected index structure"

**Symptom**: Index exists but scripts fail with cryptic errors.

**Diagnosis**:
```bash
# Check index files
cd .code-search-index/
ls -lh

# Check metadata
cat metadata.json | python -m json.tool

# Check if vector_store.db is valid SQLite
sqlite3 vector_store.db ".tables"
```

**Solution**: Rebuild the index.

```bash
# Backup old index (optional)
mv .code-search-index .code-search-index.backup

# Re-index using MCP server
# (Use Claude Code with MCP server or CLI)
```

**Prevention**: Never manually edit index files. Always use the MCP server's indexing tools.

---

### Corner Case #4: Concurrent Execution

**Symptom**: Multiple searches running simultaneously produce errors or inconsistent results.

**Cause**: The underlying index uses SQLite, which has limited concurrent write support. While concurrent **reads** (searches) are generally safe, concurrent **indexing** + **searching** can cause lock errors.

**Limitation**: These wrapper scripts do NOT handle SQLite locking. If you run:
```bash
# Terminal 1: Searching
python scripts/search.py --query "authentication" &

# Terminal 2: Searching (usually safe)
python scripts/search.py --query "database queries" &

# Terminal 3: Indexing via MCP server (UNSAFE!)
# <mcp indexing command>
```

**Result**: Terminal 1 or 2 may get "database locked" errors.

**Solution**:

1. **Read-only concurrency (searches)**: Generally safe. SQLite allows multiple concurrent reads.

2. **Write concurrency (indexing)**: AVOID running searches while indexing. The scripts don't implement retry logic for lock errors.

3. **Production use**: If you need high concurrency, consider:
   - Use a separate read-only index copy for searching
   - Implement connection pooling (not currently supported)
   - Use a different backend (Postgres instead of SQLite)

**Current Status**: This is a known limitation. These scripts are designed for single-user, low-concurrency use cases (typical Claude Code usage).

---

## Script Execution Errors

### Error: "Permission denied"

**Full Error**:
```bash
bash: ./scripts/search.py: Permission denied
```

**Cause**: Scripts are not executable.

**Solution**:
```bash
# Make scripts executable
chmod +x .claude/skills/searching-code-semantically/scripts/*.py

# Verify
ls -la .claude/skills/searching-code-semantically/scripts/
# Should show -rwxr-xr-x for .py files
```

**Prevention**: The installation should set these automatically, but some file systems (Windows, network drives) don't preserve executable bits.

---

### Error: "No module named 'utils'"

**Full Error**:
```bash
ModuleNotFoundError: No module named 'utils'
```

**Cause**: Script can't find `utils.py` in the same directory.

**Corner Case #1: Import Path Resolution**

This occurs when:
1. Scripts are run from wrong directory
2. Symlinks confuse path resolution
3. Python path is polluted with conflicting modules

**Solution**: This is why all scripts use the SCRIPT_DIR pattern:

```python
# Top of every script
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
```

**If this still fails**:

```bash
# Diagnostic: Print script directory from within script
python -c "from pathlib import Path; import sys; print(Path(sys.argv[0]).parent.resolve())" .claude/skills/searching-code-semantically/scripts/search.py

# Should print: /full/path/to/.claude/skills/searching-code-semantically/scripts
```

**Workaround**:
```bash
# Run from script directory
cd .claude/skills/searching-code-semantically/scripts
python search.py --query "test"
```

---

### Corner Case #3: Symlinked Installation

**Symptom**: Scripts fail with import errors even though installation exists.

**Cause**: Installation directory is a symlink, and naive path resolution fails.

**Example**:
```bash
~/.local/share/claude-context-local -> /mnt/shared/claude-context-local
```

**Solution**: All scripts use `.resolve()` to follow symlinks:

```python
# In utils.py
INSTALL_DIR = INSTALL_DIR.resolve()  # Follows symlinks to real path
```

**Verification**:
```bash
# Check if installation path is symlink
ls -la ~/.local/share/ | grep claude-context-local

# If symlink:
lrwxr-xr-x  1 user  staff  35 Nov 28 12:00 claude-context-local -> /mnt/shared/claude-context-local

# Scripts should still work (resolve() follows the symlink)
```

**Edge Case**: If the symlink target is on a network drive or slow filesystem, you may experience performance degradation. Consider installing directly rather than symlinking.

---

## Corner Case Documentation

### Corner Case #5: Large Result Sets (k Value Limits)

**Issue**: What happens when you request `--k 10000`?

**Behavior**:
- Script passes `k=10000` to the search module
- Module returns up to 10,000 results (memory permitting)
- JSON output may be **massive** (>10MB for large k values)
- Terminal output may truncate or hang

**Recommendation**: Keep `k` between 5-50 for practical use.

```bash
# Good
python scripts/search.py --query "auth" --k 10

# Risky (may produce huge output)
python scripts/search.py --query "auth" --k 1000

# Dangerous (may exhaust memory)
python scripts/search.py --query "auth" --k 100000
```

**Solution**: If you need many results, use pagination:
```bash
# Not directly supported by scripts
# Would require modification to add --offset parameter
```

**Current Limitation**: No built-in pagination. For large result sets, process output with `jq` or similar:

```bash
# Get first 50 results
python scripts/search.py --query "auth" --k 100 | jq '.data.results[:50]'
```

**See**: [performance-tuning.md](performance-tuning.md) for optimal k value guidance.

---

### Corner Case #6: JSON Serialization Assumptions

**Issue**: What if search results contain non-JSON-serializable data?

**Example**:
```python
# If search module returns:
{
  "timestamp": datetime.now(),  # Not JSON-serializable!
  "code": b"binary_data"
}
```

**Behavior**:
```bash
TypeError: Object of type datetime is not JSON serializable
```

**Current Assumption**: This skill assumes the `claude-context-local` module returns JSON-serializable results. If this assumption breaks (e.g., module updates return datetime objects):

**Workaround** (requires modifying scripts):
```python
# Add to utils.py
import json
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Modify success() function:
def success(data):
    print(json.dumps(
        {"success": True, "data": data},
        indent=2,
        cls=CustomJSONEncoder  # Use custom encoder
    ))
```

**Future-Proofing**: If you encounter this issue, it means the MCP server's output format has changed. File an issue with the `claude-context-local` project.

---

### Corner Case #8: Script Naming Stability

**Issue**: Can script names change in future versions?

**Policy**: **Script names are stable API**. The following names will NOT change:
- `search.py`
- `status.py`
- `find-similar.py`
- `utils.py`

**Guarantee**: If functionality changes, we'll add NEW scripts, not rename existing ones.

**Example**:
```bash
# If we add new functionality:
# ✅ Good: Add advanced-search.py (new script)
# ❌ Bad: Rename search.py to semantic-search.py (breaks existing users)
```

**See**: [README.md](../README.md) for full API stability policy.

---

### Corner Case #10: API Version Requirements

**Issue**: What if `claude-context-local` updates its API and breaks these scripts?

**Current Version Compatibility**:
- Scripts tested with: `claude-context-local` v0.x (as of November 2024)
- Required modules: `search.searcher.IntelligentSearcher`, `indexing.index_manager.CodeIndexManager`

**Failure Mode**:
```bash
# If API changes:
ImportError: cannot import name 'IntelligentSearcher' from 'search.searcher'
```

**Detection**:
```python
# Check module API
python -c "from search.searcher import IntelligentSearcher; print(IntelligentSearcher.__doc__)"
```

**Solution**: If API breaks, you have two options:

1. **Pin to last working version**:
   ```bash
   # Reinstall specific version
   pip install claude-context-local==0.x.x
   ```

2. **Update scripts to match new API**:
   - Check `claude-context-local` changelog for API changes
   - Modify `utils.py` setup() function to use new import paths
   - Update script invocations if method signatures changed

**Mitigation**: The `setup()` function in `utils.py` centralizes all imports. If the API changes, you only need to update ONE file (`utils.py`), not all three scripts.

**Recommendation**: Subscribe to `claude-context-local` release notifications to catch breaking changes early.

---

## Platform-Specific Issues

### Windows: "FileNotFoundError" Despite Installation Existing

**Symptom**: Installation exists at `C:\Users\username\AppData\Local\claude-context-local`, but scripts report "installation not found".

**Cause**: Windows path handling in Python can be tricky with mixed separators (`\` vs `/`).

**Solution**: Scripts use `pathlib.Path` for cross-platform compatibility:

```python
# In utils.py
if os.name == 'nt':  # Windows
    INSTALL_DIR = Path.home() / "AppData" / "Local" / "claude-context-local"
```

**Verification**:
```powershell
# PowerShell
python -c "from pathlib import Path; import os; print(Path.home() / 'AppData' / 'Local' / 'claude-context-local')"

# Should print: C:\Users\username\AppData\Local\claude-context-local
```

**Edge Case**: If Windows username contains non-ASCII characters, path resolution may fail. No current workaround (limitation of Python on Windows).

---

### Corner Case #7: Windows Compatibility Testing

**Status**: Scripts are designed for cross-platform use but have been primarily tested on macOS/Linux.

**Known Windows Differences**:

1. **Path Separators**: Handled via `pathlib.Path`
2. **Shebang Lines**: Ignored on Windows (use `python script.py` not `./script.py`)
3. **Executable Permissions**: Not applicable on Windows
4. **Line Endings**: Python handles CRLF/LF automatically

**Testing Coverage**:
- ✅ Unit tests include platform detection
- ✅ pathlib used for all path operations
- ⚠️ Integration tests skip on non-Windows platforms
- ❌ No CI/CD testing on actual Windows machines

**If you encounter Windows-specific issues**:

1. Check Python version: `python --version` (must be 3.8+)
2. Verify installation path: `echo %LOCALAPPDATA%\claude-context-local`
3. Run with explicit python: `python scripts/search.py --query "test"` (not `./scripts/search.py`)
4. Check for antivirus interference (some antivirus software blocks Python script execution)

**Reporting Windows Bugs**: Include:
- Windows version
- Python version
- Full error output
- Result of `dir %LOCALAPPDATA%\claude-context-local`

---

## Error Message Reference

### All Possible Error Messages

| Error Message | Cause | Quick Fix |
|---------------|-------|-----------|
| "Global installation not found" | MCP server not installed | Run installation script |
| "Failed to import search module" | Installation corrupted | Reinstall MCP server |
| "Index not found" | No index at path | Create index using MCP server |
| "required: --query" | Missing argument | Add `--query "your query"` |
| "required: --chunk-id" | Missing argument (find-similar.py) | Add `--chunk-id "id"` |
| "Permission denied" | Script not executable | `chmod +x scripts/*.py` |
| "No module named 'utils'" | Import path issue | Check SCRIPT_DIR pattern |
| "database is locked" | Concurrent access | Wait for indexing to finish |
| "TypeError: Object of type X is not JSON serializable" | MCP server API change | File bug with claude-context-local |

### JSON Error Structure

All errors follow this schema:

```json
{
  "success": false,
  "error": "<error message>",
  "suggestion": "<optional: how to fix>",
  "install_cmd": "<optional: installation command>",
  "path": "<optional: relevant path>",
  ...additional context
}
```

**Programmatic Error Handling**:
```bash
# Check if command succeeded
python scripts/search.py --query "test" 2>/dev/null
if [ $? -eq 0 ]; then
  echo "Success"
else
  echo "Failed"
fi

# Parse error JSON
python scripts/search.py --query "test" 2>&1 >/dev/null | jq '.error'
```

---

## Getting Help

If this guide doesn't resolve your issue:

1. **Check**: [effective-queries.md](effective-queries.md) - Issue might be query formulation, not technical
2. **Check**: [performance-tuning.md](performance-tuning.md) - Issue might be performance-related
3. **Verify**: Run full diagnostic checklist (top of this document)
4. **Report**: File issue with:
   - Platform (OS, Python version)
   - Full error message (JSON output)
   - Steps to reproduce
   - Output of diagnostic checklist

---

**Remember**: Most issues are either (1) missing installation, (2) missing index, or (3) query formulation. Start with those before deep debugging.
