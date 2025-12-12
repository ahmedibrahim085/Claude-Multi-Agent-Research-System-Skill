# Recovery Procedures - Stop-Hook Background Reindex

**Purpose:** Step-by-step recovery procedures for common failure scenarios
**Audience:** Developers troubleshooting reindex issues
**Last Updated:** 2025-12-12

---

## Table of Contents

1. [Stuck Background Reindex](#1-stuck-background-reindex)
2. [Multiple Concurrent Processes](#2-multiple-concurrent-processes)
3. [Leaked Claim File](#3-leaked-claim-file)
4. [Session State Corruption](#4-session-state-corruption)
5. [Index Corruption](#5-index-corruption)
6. [Cooldown Not Expiring](#6-cooldown-not-expiring)
7. [First-Prompt Not Triggering](#7-first-prompt-not-triggering)
8. [Background Process Crashes](#8-background-process-crashes)
9. [Disk Full Errors](#9-disk-full-errors)
10. [Clock Change Issues](#10-clock-change-issues)

---

## 1. Stuck Background Reindex

### Symptoms
- Background reindex started but never completes
- Claim file exists with old timestamp (>10 minutes)
- No incremental-reindex process running

### Diagnosis
```bash
# Check claim file
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, '.claude/utils')
import reindex_manager
claim = reindex_manager.get_project_storage_dir(Path.cwd()) / '.reindex_claim'
if claim.exists():
    content = claim.read_text().strip()
    pid, timestamp = content.split(':')
    print(f'Claim PID: {pid}')
    print(f'Timestamp: {timestamp}')
    import subprocess
    result = subprocess.run(['ps', '-p', pid], capture_output=True)
    print(f'Process running: {result.returncode == 0}')
else:
    print('No claim file')
"
```

### Recovery Steps

**Step 1: Verify process is truly dead**
```bash
# Get PID from claim file
CLAIM_FILE=~/.claude_code_search/projects/$(basename $(pwd))_*/reindex_claim
PID=$(cat $CLAIM_FILE 2>/dev/null | cut -d: -f1)

# Check if process exists
ps -p $PID
# If "no such process", proceed to Step 2
```

**Step 2: Remove stale claim file**
```bash
# Manual removal
rm ~/.claude_code_search/projects/$(basename $(pwd))_*/.reindex_claim

# Verify removal
ls ~/.claude_code_search/projects/$(basename $(pwd))_*/.reindex_claim
# Should show "No such file or directory"
```

**Step 3: Trigger fresh reindex**
```bash
# Option A: Restart Claude Code (first-prompt will trigger)
# Option B: Manual reindex
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd)
```

**Expected Outcome:**
- Claim file removed
- Fresh reindex starts
- Completes in 3-10 minutes

---

## 2. Multiple Concurrent Processes

### Symptoms
- `ps aux | grep incremental-reindex` shows 2+ processes
- Multiple claim files in different project directories
- High CPU usage

### Diagnosis
```bash
# List all reindex processes
ps aux | grep incremental-reindex | grep -v grep

# Expected: 0-1 processes
# If 2+, proceed to recovery
```

### Recovery Steps

**Step 1: Identify legitimate process**
```bash
# Get all PIDs
pgrep -f incremental-reindex

# Check each PID age
for pid in $(pgrep -f incremental-reindex); do
    echo "PID: $pid"
    ps -p $pid -o etime=
done

# Youngest process is likely legitimate
```

**Step 2: Kill stale processes**
```bash
# Kill processes older than 15 minutes
# (normal reindex takes 3-10 minutes)

# Get PIDs older than 15min
ps -eo pid,etime,command | grep incremental-reindex | awk '$2 ~ /[0-9][0-9]:[0-9][0-9]/ && $2 !~ /0[0-9]:[0-9]/ {print $1}'

# Kill them
for pid in $(ps -eo pid,etime,command | grep incremental-reindex | awk '$2 ~ /[0-9][0-9]:[0-9][0-9]/ {print $1}'); do
    kill -9 $pid
done
```

**Step 3: Clean up claim files**
```bash
# Remove all claim files
rm ~/.claude_code_search/projects/*/.reindex_claim

# Verify
ls ~/.claude_code_search/projects/*/.reindex_claim 2>&1 | grep "No such file"
```

**Step 4: Restart**
```bash
# Restart Claude Code
# First-prompt will trigger fresh reindex
```

---

## 3. Leaked Claim File

### Symptoms
- Claim file exists but no process running
- Reindex won't start ("Another reindex process is running")
- Auto-reindex perpetually skipped

### Diagnosis
```bash
# Check claim + process
python3 <<'EOF'
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, '.claude/utils')
import reindex_manager

storage_dir = reindex_manager.get_project_storage_dir(Path.cwd())
claim_file = storage_dir / '.reindex_claim'

if not claim_file.exists():
    print("No claim file - system healthy")
    sys.exit(0)

content = claim_file.read_text().strip()
pid = int(content.split(':')[0])

result = subprocess.run(['ps', '-p', str(pid)], capture_output=True)
if result.returncode == 0:
    print(f"Process {pid} IS running - claim is valid")
else:
    print(f"Process {pid} NOT running - LEAKED CLAIM")
    print(f"Claim file: {claim_file}")
    print(f"Content: {content}")
EOF
```

### Recovery Steps

**Automatic (60-second timeout):**
- Wait 60 seconds
- System automatically removes stale claims >60s old
- Next reindex will succeed

**Manual (immediate):**
```bash
# Remove claim file
rm ~/.claude_code_search/projects/$(basename $(pwd))_*/.reindex_claim

# Trigger reindex
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd)
```

---

## 4. Session State Corruption

### Symptoms
- First-prompt triggers on every prompt (not just first)
- Or: First-prompt never triggers
- Session state file contains invalid JSON

### Diagnosis
```bash
# Check session state
cat logs/state/session-reindex-tracking.json | python3 -m json.tool

# Expected:
# {
#   "session_id": "session_20251212_154827",
#   "first_semantic_search_shown": true
# }

# If JSON error or missing fields, corrupted
```

### Recovery Steps

**Step 1: Backup corrupted file**
```bash
cp logs/state/session-reindex-tracking.json logs/state/session-reindex-tracking.json.corrupted.$(date +%s)
```

**Step 2: Reset session state**
```bash
# Get current session ID
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '.claude/utils')
import session_logger
print(session_logger.get_session_id())
"

# Create fresh state file
cat > logs/state/session-reindex-tracking.json <<EOF
{
  "session_id": "$(python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, ".claude/utils"); import session_logger; print(session_logger.get_session_id())')",
  "first_semantic_search_shown": false
}
EOF
```

**Step 3: Verify**
```bash
cat logs/state/session-reindex-tracking.json | python3 -m json.tool
```

**Step 4: Restart Claude Code**
- First-prompt will trigger normally

---

## 5. Index Corruption

### Symptoms
- Search returns no results
- Reindex completes but index empty
- FAISS errors in logs

### Diagnosis
```bash
# Check index files exist
ls -lh ~/.claude_code_search/projects/$(basename $(pwd))_*/index/

# Expected files:
# - code.index (FAISS index, >100KB)
# - metadata.db (SQLite database)
# - chunk_ids.pkl (Pickle file)
# - stats.json (JSON metadata)

# Check stats
cat ~/.claude_code_search/projects/$(basename $(pwd))_*/index/stats.json | python3 -m json.tool
```

### Recovery Steps

**Step 1: Backup corrupted index**
```bash
mv ~/.claude_code_search/projects/$(basename $(pwd))_*/index \
   ~/.claude_code_search/projects/$(basename $(pwd))_*/index.corrupted.$(date +%s)
```

**Step 2: Force full reindex**
```bash
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd) --full
```

**Step 3: Verify rebuild**
```bash
# Check stats
cat ~/.claude_code_search/projects/$(basename $(pwd))_*/index/stats.json | python3 -m json.tool

# Should show:
# - total_chunks > 0
# - total_files > 0
# - embedding_dimension: 768
```

**Step 4: Test search**
```bash
.claude/skills/semantic-search/scripts/search \
  --query "test query" \
  --project $(pwd) \
  --k 5
```

---

## 6. Cooldown Not Expiring

### Symptoms
- Stop-hook perpetually skips reindex ("cooldown_active")
- Last reindex was >5 minutes ago
- Expected cooldown should have expired

### Diagnosis
```bash
# Check timing analysis
python3 <<'EOF'
from pathlib import Path
import sys
sys.path.insert(0, '.claude/utils')
import reindex_manager

timing = reindex_manager.get_reindex_timing_analysis(Path.cwd())
print(f"Last reindex UTC: {timing['last_reindex_utc']}")
print(f"Last reindex local: {timing['last_reindex_local']}")
print(f"Current UTC: {timing['current_utc']}")
print(f"Current local: {timing['current_local']}")
print(f"Elapsed: {timing['elapsed_display']}")
print(f"Cooldown: {timing['cooldown_seconds']}s")
print(f"Status: {timing['cooldown_status']}")
print(f"Expired: {timing['cooldown_expired']}")
EOF
```

### Recovery Steps

**If clock changed:**
```bash
# Force reindex (ignores cooldown)
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd) --full
```

**If state file corrupted:**
```bash
# Reset index state
rm ~/.claude_code_search/projects/$(basename $(pwd))_*/index/index_state.json

# Next reindex will create fresh state
```

---

## 7. First-Prompt Not Triggering

### Symptoms
- Session starts but no "🔄 Checking for index updates" message
- First prompt doesn't spawn background reindex
- `first_semantic_search_shown` stuck at `true`

### Diagnosis
```bash
# Check session state
cat logs/state/session-reindex-tracking.json

# Check if flag stuck
python3 -c "
import sys, json
from pathlib import Path
sys.path.insert(0, '.claude/utils')
import session_logger, reindex_manager

state_file = Path('logs/state/session-reindex-tracking.json')
if state_file.exists():
    state = json.loads(state_file.read_text())
    current_session = session_logger.get_session_id()
    print(f'Stored session: {state.get(\"session_id\")}')
    print(f'Current session: {current_session}')
    print(f'Sessions match: {state.get(\"session_id\") == current_session}')
    print(f'Flag value: {state.get(\"first_semantic_search_shown\")}')
    print(f'Should trigger: {reindex_manager.should_show_first_prompt_status()}')
"
```

### Recovery Steps

**Step 1: Reset session state**
```bash
rm logs/state/session-reindex-tracking.json
```

**Step 2: Restart Claude Code**
- Session-start will create fresh state
- First-prompt will trigger

**Step 3: Verify**
- Should see "🔄 Checking for index updates" on first prompt

---

## 8. Background Process Crashes

### Symptoms
- Background reindex started but claim file leaked
- No completion notification
- Index not updated

### Diagnosis
```bash
# Check reindex operations log
tail -20 logs/reindex-operations.jsonl

# Look for START without matching FINISH
# Example:
# {"event":"START", "operation_id":"fp_12345", ...}
# (no FINISH event)
```

### Recovery Steps

**Step 1: Check for crash logs**
```bash
# Check stderr if captured
cat logs/reindex-stderr.log 2>/dev/null

# Check system logs
dmesg | grep -i python
```

**Step 2: Remove leaked claim**
```bash
rm ~/.claude_code_search/projects/$(basename $(pwd))_*/.reindex_claim
```

**Step 3: Manual reindex**
```bash
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd) --full
```

**Step 4: Monitor**
```bash
# Watch for completion
tail -f logs/reindex-operations.jsonl
# Should see FINISH event
```

---

## 9. Disk Full Errors

### Symptoms
- Reindex fails with "No space left on device"
- Claim file creation fails
- Index writes fail

### Diagnosis
```bash
# Check disk space
df -h ~/.claude_code_search
df -h $(pwd)

# Check index size
du -sh ~/.claude_code_search/projects/$(basename $(pwd))_*/
```

### Recovery Steps

**Step 1: Free up space**
```bash
# Remove old indexes (if multiple projects)
du -sh ~/.claude_code_search/projects/*/ | sort -h

# Remove oldest/largest if needed
# rm -rf ~/.claude_code_search/projects/old_project_*/
```

**Step 2: Clean up logs**
```bash
# Archive old session logs
tar -czf logs/archive_$(date +%Y%m%d).tar.gz logs/session_*
rm logs/session_*_transcript.txt logs/session_*_tool_calls.jsonl
```

**Step 3: Retry reindex**
```bash
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd) --full
```

---

## 10. Clock Change Issues

### Symptoms
- Cooldown behaves strangely after changing system time
- Negative elapsed time in logs
- Timestamps don't make sense

### Diagnosis
```bash
# Check for negative elapsed
python3 <<'EOF'
from pathlib import Path
import sys
sys.path.insert(0, '.claude/utils')
import reindex_manager

timing = reindex_manager.get_reindex_timing_analysis(Path.cwd())
print(f"Last reindex: {timing['last_reindex_utc']}")
print(f"Current time: {timing['current_utc']}")
print(f"Elapsed seconds: {timing['elapsed_seconds']}")

if timing['elapsed_seconds'] < 0:
    print("⚠️  NEGATIVE ELAPSED TIME - Clock changed backward")
EOF
```

### Recovery Steps

**Step 1: Reset index state**
```bash
# Remove state file with bad timestamp
rm ~/.claude_code_search/projects/$(basename $(pwd))_*/index/index_state.json
```

**Step 2: Force reindex**
```bash
# Recreate state with current time
.claude/skills/semantic-search/scripts/incremental-reindex $(pwd) --full
```

**Step 3: Verify timestamps**
```bash
# Check new state
cat ~/.claude_code_search/projects/$(basename $(pwd))_*/index/index_state.json | python3 -m json.tool

# Timestamps should be current
```

---

## Emergency Reset (Nuclear Option)

**When:** None of the above work, system completely broken

**Warning:** This deletes ALL state - use as last resort

```bash
# Backup everything
tar -czf backup_$(date +%s).tar.gz \
  ~/.claude_code_search/projects/$(basename $(pwd))_*/ \
  logs/state/ \
  logs/reindex-operations.jsonl

# Remove all state
rm -rf ~/.claude_code_search/projects/$(basename $(pwd))_*/
rm -f logs/state/session-reindex-tracking.json
rm -f logs/state/semantic-search-prerequisites.json

# Restart Claude Code
# First-prompt will rebuild everything from scratch
```

---

## Prevention Best Practices

1. **Monitor disk space** - Keep >500MB free
2. **Regular cleanup** - Archive old session logs weekly
3. **Avoid clock changes** - Use NTP
4. **Check logs** - Review `logs/reindex-operations.jsonl` for orphaned events
5. **Test prerequisites** - Run `.claude/skills/semantic-search/scripts/check-prerequisites`

---

## Getting Help

**If recovery fails:**
1. Capture logs: `tar -czf debug_$(date +%s).tar.gz logs/`
2. Capture state: `tar -czf state_$(date +%s).tar.gz ~/.claude_code_search/`
3. Report issue: https://github.com/anthropics/claude-code/issues
4. Include: Recovery procedure tried, symptoms, error messages

---

**Last Updated:** 2025-12-12
**Version:** 1.0
**Status:** Production
