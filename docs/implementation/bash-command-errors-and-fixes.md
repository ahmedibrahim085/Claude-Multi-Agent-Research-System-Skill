# Bash Command Errors and Fixes

**Date**: 2025-12-01
**Context**: Session logging analysis commands that failed
**Shell**: zsh (macOS default)

---

## Error 1: Permission Denied in Multi-line Command

### Failed Command
```bash
echo "=== Agent Attribution Summary ===" && \
echo "" && \
echo "All Orchestrators in Session Logs:" && \
grep -h "ORCHESTRATOR" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r '.agent' | sort | uniq -c | sort -rn && \
echo "" && \
echo "=== Semantic-Search Agent Breakdown ===" && \
grep -h "SEMANTIC" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r 'select(.tool == "Task") | .agent + " spawned " + .input.subagent_type' | head -5
```

### Error
```
Exit code 126
(eval):1: permission denied:
```

### Root Cause
- Complex multi-line command with multiple `&&` chained together
- In zsh, when commands are evaluated through `(eval)`, complex pipelines can fail
- The `head -5` at the end without `-n` flag can cause issues in some zsh contexts
- Long command strings may exceed shell parsing limits

### Fix
**Option 1**: Break into separate commands
```bash
echo "=== Agent Attribution Summary ==="
echo ""
echo "All Orchestrators in Session Logs:"
grep -h "ORCHESTRATOR" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r '.agent' | sort | uniq -c | sort -rn
echo ""
echo "=== Semantic-Search Agent Breakdown ==="
grep -h "SEMANTIC" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r 'select(.tool == "Task") | .agent + " spawned " + .input.subagent_type' | head -n 5
```

**Option 2**: Use subshell grouping
```bash
{
  echo "=== Agent Attribution Summary ==="
  echo ""
  grep -h "ORCHESTRATOR" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r '.agent' | sort | uniq -c | sort -rn
  echo ""
  echo "=== Semantic-Search Agent Breakdown ==="
  grep -h "SEMANTIC" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r 'select(.tool == "Task") | .agent + " spawned " + .input.subagent_type' | head -n 5
}
```

**Option 3**: Use here-document for output
```bash
cat << 'EOF'
=== Agent Attribution Summary ===

EOF
grep -h "ORCHESTRATOR" logs/session_*_tool_calls.jsonl 2>/dev/null | jq -r '.agent' | sort | uniq -c | sort -rn
```

---

## Error 2: JQ Parse Error with Grep Pipeline

### Failed Command
```bash
grep "SEMANTIC" logs/session_20251201_21*.jsonl 2>/dev/null | grep "Task" | jq -r '"\(.agent) spawned \(.input.subagent_type)"'
```

### Error
```
Exit code 5
jq: parse error: Invalid numeric literal at line 1, column 46
```

### Root Cause
- When `grep` matches multiple files, it prepends filenames to output
- Output becomes: `filename.jsonl:{"json":"data"}`
- The filename prefix is NOT valid JSON, causing jq to fail
- Even with `-h` flag, grep might still have issues if glob matches no files

### Fix
**Option 1**: Use grep -h and ensure it works
```bash
grep -h "SEMANTIC" logs/session_20251201_21*.jsonl 2>/dev/null | grep "Task" | jq -r '"\(.agent) spawned \(.input.subagent_type)"'
```

**Option 2**: Iterate files individually (RECOMMENDED)
```bash
for file in logs/session_20251201_21*_tool_calls.jsonl; do
  grep "SEMANTIC" "$file" 2>/dev/null | grep "Task" | jq -r '"\(.agent) spawned \(.input.subagent_type)"'
done
```

**Option 3**: Use jq directly on files (BEST)
```bash
jq -r 'select(.agent | test("SEMANTIC")) | select(.tool == "Task") | "\(.agent) spawned \(.input.subagent_type)"' logs/session_20251201_21*_tool_calls.jsonl 2>/dev/null
```

**Why Option 3 is best**:
- jq can handle multiple files natively
- No grep needed (jq does the filtering)
- Clean JSON parsing, no filename prefix issues
- More efficient (one process instead of pipeline)

---

## Error 3: Parse Error with For Loop Pipeline

### Failed Command
```bash
for file in logs/session_20251201_21*_tool_calls.jsonl; do
  cat "$file" | jq -r 'select(.agent | test("SEMANTIC")) | select(.tool == "Task") | "\(.agent) → spawned → \(.input.subagent_type)"'
done 2>/dev/null | head -10
```

### Error
```
Exit code 1
(eval):1: parse error near `-10'
```

### Root Cause
- In zsh, the combination of `done 2>/dev/null | head -10` on the same line causes parsing confusion
- The parser sees `-10` and may interpret it incorrectly in the context of the for loop
- zsh is stricter than bash about loop syntax with redirections and pipes on the same line
- The `head -10` shorthand (without `-n`) can be ambiguous in some contexts

### Fix
**Option 1**: Use explicit -n flag
```bash
for file in logs/session_20251201_21*_tool_calls.jsonl; do
  cat "$file" | jq -r 'select(.agent | test("SEMANTIC")) | select(.tool == "Task") | "\(.agent) → spawned → \(.input.subagent_type)"'
done 2>/dev/null | head -n 10
```

**Option 2**: Separate the redirection
```bash
{
  for file in logs/session_20251201_21*_tool_calls.jsonl; do
    cat "$file" | jq -r 'select(.agent | test("SEMANTIC")) | select(.tool == "Task") | "\(.agent) → spawned → \(.input.subagent_type)"'
  done
} 2>/dev/null | head -n 10
```

**Option 3**: Avoid the loop entirely (RECOMMENDED)
```bash
jq -r 'select(.agent | test("SEMANTIC")) | select(.tool == "Task") | "\(.agent) → spawned → \(.input.subagent_type)"' logs/session_20251201_21*_tool_calls.jsonl 2>/dev/null | head -n 10
```

**Why Option 3 is best**:
- jq handles multiple files natively
- No loop needed
- Cleaner syntax, less error-prone
- Faster execution (one process)

---

## Best Practices to Avoid These Errors

### 1. Keep Commands Simple
❌ **Bad**: Long chains of && with complex pipelines
```bash
cmd1 && cmd2 && cmd3 | filter1 | filter2 && cmd4 && cmd5 | filter3 | filter4
```

✅ **Good**: Break into logical steps
```bash
cmd1
cmd2
cmd3 | filter1 | filter2
cmd4
cmd5 | filter3 | filter4
```

---

### 2. Use jq Directly on Files
❌ **Bad**: Grep then jq
```bash
grep "pattern" file.jsonl | jq '.field'
```

✅ **Good**: Let jq do the filtering
```bash
jq 'select(. | test("pattern")) | .field' file.jsonl
```

**Why**:
- jq is designed for JSON
- No filename prefix issues
- Better error messages
- More efficient

---

### 3. Explicit Flags Over Shortcuts
❌ **Bad**: Ambiguous shorthand
```bash
head -10
tail -20
```

✅ **Good**: Explicit flags
```bash
head -n 10
tail -n 20
```

**Why**:
- Works consistently across shells (bash, zsh, sh)
- More readable
- Avoids parser confusion

---

### 4. Proper Loop Syntax
❌ **Bad**: Redirection and pipe on same line as `done`
```bash
for f in *; do
  cat "$f"
done 2>/dev/null | head -10
```

✅ **Good**: Use subshell grouping or separate steps
```bash
{
  for f in *; do
    cat "$f"
  done
} 2>/dev/null | head -n 10
```

Or better yet, avoid the loop:
```bash
cat * 2>/dev/null | head -n 10
```

---

### 5. Test Glob Patterns First
❌ **Bad**: Assume glob matches
```bash
grep "text" logs/session_*.jsonl | jq '.'
```

✅ **Good**: Verify files exist
```bash
if ls logs/session_*.jsonl >/dev/null 2>&1; then
  jq '.' logs/session_*.jsonl
else
  echo "No matching files found"
fi
```

Or use find:
```bash
find logs -name "session_*.jsonl" -exec jq '.' {} +
```

---

## Quick Reference: Safe Command Patterns

### Pattern 1: Process Multiple JSON Files
```bash
# Process all files with jq directly
jq -r 'select(.field == "value") | .output' files/*.jsonl 2>/dev/null

# Count unique values across files
jq -r '.field' files/*.jsonl 2>/dev/null | sort | uniq -c

# Filter and format
jq -r 'select(.type == "error") | "\(.timestamp): \(.message)"' logs/*.jsonl 2>/dev/null
```

### Pattern 2: Safe Multi-Step Analysis
```bash
# Step 1: Extract data
jq -r '.agent' logs/session_*.jsonl 2>/dev/null > /tmp/agents.txt

# Step 2: Analyze
sort /tmp/agents.txt | uniq -c | sort -rn

# Step 3: Cleanup
rm /tmp/agents.txt
```

### Pattern 3: Safe Iteration
```bash
# Use find instead of glob when you need to handle files individually
find logs -name "session_*_tool_calls.jsonl" -type f -print0 |
  while IFS= read -r -d '' file; do
    jq -r '.agent' "$file" 2>/dev/null
  done | sort | uniq -c
```

---

## Error Prevention Checklist

Before running complex bash commands, verify:

- [ ] No long chains of `&&` (break into separate commands)
- [ ] Use explicit flags (`-n`, `-r`, etc.) not shortcuts
- [ ] Use `jq` directly on files instead of `grep | jq`
- [ ] Test glob patterns match files (`ls pattern` first)
- [ ] Redirect stderr (`2>/dev/null`) to suppress noise
- [ ] Use subshell `{}` for loop grouping if needed
- [ ] Avoid `cat file | command` (use `command < file` or `command file`)
- [ ] Quote variables and file arguments (`"$file"` not `$file`)

---

## Summary of Fixes

| Error | Root Cause | Fix |
|-------|-----------|-----|
| Permission denied (126) | Complex multi-line && chains | Break into separate commands or use `{}` grouping |
| JQ parse error (5) | Grep prepends filenames to JSON | Use `jq` directly on files, avoid `grep \| jq` |
| Parse error near -10 (1) | Loop syntax with `done 2>&1 \| head -10` | Use `head -n 10`, wrap loop in `{}`, or avoid loop |

**Key Takeaway**: Use jq directly on files whenever possible. Avoid complex pipelines with grep when processing JSON.
