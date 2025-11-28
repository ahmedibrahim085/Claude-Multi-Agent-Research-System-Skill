# API Stability Policy

**Script API Guarantees for searching-code-semantically Skill**

This document defines the stability guarantees for the Python wrapper scripts (`search.py`, `find-similar.py`, `status.py`) provided by this skill. These guarantees ensure that automation, workflows, and integrations built on these scripts will continue to work across updates.

---

## Stable APIs

The following are **guaranteed stable** and will NOT change in future versions:

### Script Names

- ✅ `search.py` - Will NOT be renamed
- ✅ `status.py` - Will NOT be renamed
- ✅ `find-similar.py` - Will NOT be renamed
- ✅ `utils.py` - Will NOT be renamed

### Script Arguments

- ✅ `--query` argument format (required string)
- ✅ `--chunk-id` argument format (required string)
- ✅ `--k` argument format (optional int, default 5)
- ✅ `--storage-dir` argument format (optional path string)

### JSON Output Structure

```json
{
  "success": true|false,
  "data": {...}|null,
  "error": "message"|null
}
```

**Guarantees**:
- ✅ Top-level `success` key will always exist (boolean)
- ✅ Top-level `data` key will always exist on success
- ✅ Top-level `error` key will always exist on failure
- ✅ Output is always valid JSON
- ✅ Errors always output to stderr, success to stdout

---

## Evolution Policy

### When we add features, we will:

- ✅ Add NEW scripts (e.g., `advanced-search.py`)
- ✅ Add NEW optional arguments to existing scripts
- ✅ Add NEW keys to JSON output (backwards-compatible)

### When we fix bugs, we will:

- ✅ Fix behavior without changing APIs
- ✅ Document breaking changes in release notes if unavoidable

### We will NEVER:

- ❌ Rename existing scripts
- ❌ Remove existing arguments
- ❌ Change argument semantics (e.g., making --k required)
- ❌ Remove keys from JSON output
- ❌ Change JSON output to non-JSON format
- ❌ Change which stream (stdout/stderr) is used for output

---

## Versioning

This skill follows semantic versioning:

- **Major version**: Breaking API changes (we'll avoid these!)
- **Minor version**: New features (new scripts, new optional arguments)
- **Patch version**: Bug fixes, documentation updates

**Current version**: 1.0.0 (Initial release)

---

## Deprecation Process

If we must deprecate an API (extremely rare), we will:

1. **Announce** deprecation in release notes
2. **Maintain** deprecated API for at least 6 months
3. **Warn** users in script output when using deprecated features
4. **Provide** migration guide
5. **Remove** only after 6+ months and major version bump

---

## Dependencies on claude-context-local

**External dependency**: These scripts depend on the `claude-context-local` MCP server's API.

**Compatibility**: If `claude-context-local` updates its API and breaks these scripts:
1. We'll update `utils.py` to adapt to new API
2. Script APIs remain stable (users don't change their commands)
3. Release notes will document the underlying change

**Mitigation**: All imports are centralized in `utils.py`. API changes only require updating one file.

---

## Why This Matters

These stability guarantees mean you can:
- Build shell scripts and automation that won't break
- Integrate these tools into CI/CD pipelines confidently
- Parse JSON output without version-checking logic
- Upgrade the skill without fear of breaking existing workflows

**Example stable usage**:
```bash
# This command will work forever (barring major version bumps)
python scripts/search.py --query "authentication logic" --k 10 | jq '.data.results[]'
```

---

_Last updated: November 2024 (v1.0.0)_
