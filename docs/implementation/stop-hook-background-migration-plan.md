# Stop-Hook Background Migration - Implementation Plan

**Objective:** Migrate stop-hook from synchronous (50s timeout) to background pattern (no timeout), following first-prompt's proven architecture.

**Status:** Ready for Implementation
**Risk Level:** MEDIUM (touches critical auto-reindex path, but has proven pattern to copy)
**Estimated Complexity:** 7/10 (architectural change with multiple files)

---

## Executive Summary

### Problem
Stop-hook uses synchronous `run_incremental_reindex_sync()` with 50-second timeout, causing failures for reindexes that take 200-350 seconds (evidence: logs/stop-hook-debug.log showing timeout failures).

### Solution
Replace synchronous pattern with background spawn pattern (proven by first-prompt hook's success), while preserving stop-hook's unique business logic (prerequisites, cooldown, concurrent PID checks).

### Key Changes
1. **NEW FUNCTION:** `reindex_on_stop_background()` - replaces `reindex_on_stop()`
2. **ARCHITECTURE:** Synchronous → Background (copy first-prompt pattern)
3. **REMOVE:** Index exists check (TRUE redundancy)
4. **ADD:** Concurrent PID check at parent level (FALSE redundancy - prevents orphaned START events)
5. **MODIFY:** Decision codes (reindex_spawned vs reindex_success/failed)

---

## Pre-Implementation Verification

**CRITICAL: Complete ALL checks before starting implementation**

### ✅ Checklist

- [ ] **Current code reading:** Read current `reindex_on_stop()` (lines 1623-1750)
- [ ] **Pattern verification:** Read `spawn_background_reindex()` (lines 1093-1157)
- [ ] **Hook integration:** Read `.claude/hooks/stop.py` (lines 116-141)
- [ ] **Script architecture:** Read `.claude/skills/semantic-search/scripts/incremental_reindex.py` (lines 679-754)
- [ ] **Backup verification:** Confirm git status is clean (can rollback easily)
- [ ] **Test baseline:** Run stop hook once, verify current behavior in logs/stop-hook-debug.log

### 📋 Expected Baseline State

```bash
# Git status should show only merged plan changes
git status

# Stop hook should currently fail on long reindexes
tail -20 logs/stop-hook-debug.log
# Should see: "reindex_on_stop() returned: run - reindex_failed" after ~50s
```

---

## Implementation Steps

### STEP 1: Create New Background Function

**File:** `.claude/utils/reindex_manager.py`
**Location:** Insert after `spawn_background_reindex()` (after line 1167)
**Risk:** LOW (new function, doesn't break existing code)

#### Task 1.1: Add Function Signature and Docstring

**Action:** Add complete function with docstring

**Code to Add:**
```python
def reindex_on_stop_background(cooldown_seconds: Optional[int] = None) -> dict:
    """Auto-reindex on stop hook using background pattern (follows first-prompt architecture)

    NEW Architecture: Background spawn (no timeout) instead of synchronous (50s timeout)
    - OLD: Synchronous with 50s timeout → fails for reindexes > 50s
    - NEW: Background spawn → completes 200-350s reindexes successfully
    - BENEFIT: No timeout failures, matches first-prompt's proven pattern

    Trigger Behavior (from official docs at code.claude.com/docs/en/hooks):
    - Fires when "main Claude Code agent has finished responding"
    - Does NOT fire "if stoppage occurred due to a user interrupt"
    - Fires ONCE per conversation turn (NOT after each spawned agent)

    Business Logic (Gate Checks):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Prerequisites FALSE → Skip (manual setup not done yet)
    2. Cooldown active → Skip (prevents spam on rapid conversation turns)
    3. Concurrent reindex running → Skip (prevents orphaned START events)
    4. All checks pass → Spawn background reindex

    Differences from First-Prompt:
    - ADDS prerequisites check (first-prompt has no prerequisites gate)
    - ADDS cooldown check (first-prompt has one-time gate instead)
    - ADDS concurrent PID check (prevents orphaned START events in forensic logs)
    - KEEPS decision dict return (stop.py needs it for session logging)

    Differences from Old reindex_on_stop():
    - REMOVES index exists check (script creates index if missing - TRUE redundancy)
    - REPLACES synchronous call with background spawn
    - REMOVES 50s timeout (background mode has no timeout)
    - CHANGES decision codes (reindex_spawned vs reindex_success/failed)

    Args:
        cooldown_seconds: Optional cooldown override (None = use config, default 300s)

    Returns:
        dict: Decision data with keys:
            - decision: "skip" or "run"
            - reason: Human-readable reason code
            - details: Additional context (structured dict)
            - timestamp: ISO timestamp of decision
    """
```

**Verification:**
- [ ] Docstring explains NEW vs OLD architecture
- [ ] All 4 business logic steps documented
- [ ] Return dict structure documented
- [ ] No syntax errors

---

#### Task 1.2: Section 1 - Initialize Timestamp

**Action:** Add timestamp initialization outside try block

**Code to Add:**
```python
    # ═══════════════════════════════════════════════════════════════════
    # SECTION 1: Initialize (KEEP - stop.py needs timestamp in dict)
    # ═══════════════════════════════════════════════════════════════════
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
```

**Source:** Current `reindex_on_stop()` line 1659 (EXACT)

**Reason:** Decision dict requires timestamp field for stop.py session logging. Must be outside try block so exception handler can access it.

**Verification:**
- [ ] Uses `datetime.now(timezone.utc).isoformat()` (not datetime.now())
- [ ] Variable named `timestamp` (matches exception handler)
- [ ] Placed BEFORE try block

---

#### Task 1.3: Section 2 - Prerequisites Check

**Action:** Add prerequisites gate check

**Code to Add:**
```python
        # ═══════════════════════════════════════════════════════════════
        # SECTION 2: Gate Check - Prerequisites (KEEP - unique to stop-hook)
        # ═══════════════════════════════════════════════════════════════
        # REASON: Prevents spawning doomed reindex when skill not installed
        if not read_prerequisites_state():
            return {
                "decision": "skip",
                "reason": "prerequisites_not_ready",
                "details": {
                    "trigger": "stop_hook",
                    "state_file": "logs/state/semantic-search-prerequisites.json"
                },
                "timestamp": timestamp
            }
```

**Source:** Current `reindex_on_stop()` lines 1662-1672 (EXACT)

**Reason:** Stop-hook specific. Prevents spawning when semantic-search skill not installed (would fail immediately).

**Verification:**
- [ ] Uses `read_prerequisites_state()` function (exists in reindex_manager.py)
- [ ] Returns structured dict (not plain string in details)
- [ ] Dict has all 4 fields: decision, reason, details, timestamp
- [ ] Details has "trigger": "stop_hook" and "state_file" keys

---

#### Task 1.4: Section 3 - Cooldown Check

**Action:** Add cooldown gate check with elapsed/remaining calculations

**Code to Add:**
```python
        # ═══════════════════════════════════════════════════════════════
        # SECTION 3: Gate Check - Cooldown (KEEP - unique to stop-hook)
        # ═══════════════════════════════════════════════════════════════
        # REASON: Prevents spam spawning on rapid session restarts
        project_path = get_project_root()
        config = get_reindex_config()
        cooldown = cooldown_seconds if cooldown_seconds is not None else config['cooldown_seconds']

        if not should_reindex_after_cooldown(project_path, cooldown):
            last_reindex = get_last_reindex_time(project_path)
            elapsed = 0
            if last_reindex:
                now = datetime.now(timezone.utc)
                if last_reindex.tzinfo is None:
                    last_reindex = last_reindex.replace(tzinfo=timezone.utc)
                elapsed = (now - last_reindex).total_seconds()

            return {
                "decision": "skip",
                "reason": "cooldown_active",
                "details": {
                    "trigger": "stop_hook",
                    "cooldown_seconds": cooldown,
                    "elapsed_seconds": int(elapsed),
                    "remaining_seconds": int(cooldown - elapsed)
                },
                "timestamp": timestamp
            }
```

**Source:** Current `reindex_on_stop()` lines 1674-1698 (EXACT)

**Critical Implementation Fidelity:**
- ✅ Uses `get_project_root()` NOT `Path.cwd()` (line 1675)
- ✅ Uses `get_reindex_config()` NOT hardcoded `300` (line 1676)
- ✅ Calculates `elapsed_seconds` and `remaining_seconds` (lines 1681-1686, 1694-1695)
- ✅ Returns structured details dict with all fields (lines 1691-1696)

**Verification:**
- [ ] Uses `get_project_root()` (not Path.cwd())
- [ ] Uses `get_reindex_config()` (not hardcoded 300)
- [ ] Calculates elapsed time correctly (handles timezone awareness)
- [ ] Returns dict with elapsed_seconds and remaining_seconds
- [ ] All helper functions exist: should_reindex_after_cooldown, get_last_reindex_time

---

#### Task 1.5: Section 4 - Concurrent PID Verification

**Action:** Add concurrent PID check to prevent orphaned START events

**Code to Add:**
```python
        # ═══════════════════════════════════════════════════════════════
        # SECTION 4: Gate Check - Concurrent PID (ADD - prevents orphaned events)
        # ═══════════════════════════════════════════════════════════════
        # CRITICAL: Script exits at line 690 BEFORE finally block at line 703
        # If script detects concurrent, NO END event logged (orphaned START)
        # Parent check logs START with skipped=True, preventing orphaned events
        claim_file = project_path / '.claude' / 'skills' / 'semantic-search' / '.reindex-claim'

        if claim_file.exists():
            try:
                # Parse PID from claim file
                claim_content = claim_file.read_text().strip()
                pid = int(claim_content.split(':')[0])

                # Verify process exists and is incremental-reindex
                result = subprocess.run(
                    ['ps', '-p', str(pid), '-o', 'command='],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    # PID exists - verify it's our process
                    command = result.stdout.strip()
                    if 'incremental-reindex' in command or 'incremental_reindex.py' in command:
                        # Process verified - truly concurrent reindex running
                        # Log START event with skipped=True (prevents orphaned event)
                        log_reindex_start(
                            trigger='stop-hook',
                            mode='background',
                            pid=None,
                            skipped=True,
                            skip_reason='concurrent_reindex'
                        )
                        return {
                            "decision": "skip",
                            "reason": "concurrent_reindex",
                            "details": {
                                "trigger": "stop_hook",
                                "concurrent_pid": pid
                            },
                            "timestamp": timestamp
                        }
                    else:
                        # PID alive but wrong process - orphaned claim
                        claim_file.unlink()
                else:
                    # PID dead - orphaned claim from crash/kill
                    claim_file.unlink()

            except (ValueError, IndexError, FileNotFoundError, OSError):
                # Corrupted/invalid claim - remove and continue
                try:
                    claim_file.unlink()
                except FileNotFoundError:
                    pass
```

**Source:** Phase 1 fix `_acquire_reindex_lock()` lines 893-919 (adapted for parent-level check)

**Reason:** **FALSE REDUNDANCY** - Script exits BEFORE finally block (line 690 vs 703), so NO END event if concurrent detected by script. Parent check prevents orphaned START events.

**Critical Evidence:**
- Script `incremental_reindex.py` line 690: `sys.exit(0)` when lock not acquired
- try/finally block starts line 703 (AFTER exit)
- END event only logged in finally block (lines 735-754)

**Verification:**
- [ ] Claim file path uses `project_path` (from Section 3)
- [ ] PID verification uses `ps -p` command
- [ ] Checks for 'incremental-reindex' OR 'incremental_reindex.py' in command
- [ ] Calls `log_reindex_start()` with skipped=True when concurrent detected
- [ ] Orphaned claims removed (unlink on PID mismatch)
- [ ] Exception handling covers all cases: ValueError, IndexError, FileNotFoundError, OSError

---

#### Task 1.6: Section 5 - Show Message Before Spawn

**Action:** Add message BEFORE spawn (first-prompt pattern)

**Code to Add:**
```python
        # ═══════════════════════════════════════════════════════════════
        # SECTION 5: Show Message (COPY from first-prompt)
        # ═══════════════════════════════════════════════════════════════
        # REASON: User wants visibility, message shows even if spawn fails
        print("🔄 Checking for index updates in background...", flush=True)
```

**Source:** First-prompt `first-prompt-reindex.py` line 70 (adapted)

**Reason:** User requirement #2: "I prefer stop-hook to show messages if possible." First-prompt shows message BEFORE checking spawn result.

**Verification:**
- [ ] Uses `flush=True` for immediate display
- [ ] Message appropriate for stop-hook context
- [ ] Placed BEFORE spawn call (not conditional on result)

---

#### Task 1.7: Section 6 - Spawn Background Reindex

**Action:** Add direct spawn call (NO index exists check)

**Code to Add:**
```python
        # ═══════════════════════════════════════════════════════════════
        # SECTION 6: Spawn Background (COPY from first-prompt)
        # ═══════════════════════════════════════════════════════════════
        # NO index exists check - script handles missing index (TRUE redundancy)
        # Script creates empty index (line 88), loads existing (line 103),
        # populates via full reindex (line 548)
        spawned = spawn_background_reindex(project_path, trigger='stop-hook')
```

**Source:** First-prompt `first-prompt-reindex.py` line 62 + `spawn_background_reindex()` lines 1093-1157

**Reason:** Proven pattern - direct spawn, no timeout, completes 200-350s successfully.

**REMOVED:** Index exists check (TRUE redundancy - script handles missing index gracefully)

**Evidence:**
- Script line 88: Creates empty `IndexFlatIP` on init
- Script line 103-124: Loads existing if available, otherwise continues with empty
- Script line 548-549: Full reindex populates empty index

**Verification:**
- [ ] Direct call to `spawn_background_reindex()` (function exists)
- [ ] Uses `project_path` from Section 3
- [ ] Trigger is 'stop-hook' (for forensic logging)
- [ ] NO index exists check before spawn (removed)
- [ ] NO additional checks here (script handles lock/concurrent/age)

---

#### Task 1.8: Section 7 - Return Decision Dict

**Action:** Add decision dict return with MODIFIED codes for background mode

**Code to Add:**
```python
        # ═══════════════════════════════════════════════════════════════
        # SECTION 7: Return Decision Dict (KEEP structure, MODIFY codes)
        # ═══════════════════════════════════════════════════════════════
        # REASON: stop.py session logging needs dict (lines 119-141)
        # MODIFIED: Decision codes for background mode (can't know success/failure)

        if spawned:
            # Process spawned successfully
            # ✅ FORENSIC LOGGING: spawn_background_reindex already logged START event (line 1149-1155)
            # ⏳ END EVENT: Will be logged by script's finally block when done (line 735-754)
            return {
                "decision": "run",
                "reason": "reindex_spawned",  # MODIFIED: was reindex_success/failed
                "details": {"trigger": "stop_hook"},
                "timestamp": timestamp
            }
        else:
            # Script not found (rare - installation issue)
            return {
                "decision": "skip",
                "reason": "script_not_found",
                "details": {"trigger": "stop_hook"},
                "timestamp": timestamp
            }
```

**Source:** Current `reindex_on_stop()` lines 1717-1740 (MODIFIED decision codes)

**Reason:** Background spawn can't report success/failure (detached process), so update codes accordingly.

**Critical Change:**
- OLD: "reindex_success" / "reindex_failed" (synchronous results)
- NEW: "reindex_spawned" / "script_not_found" (background - outcome unknown)

**Verification:**
- [ ] Returns dict (not boolean or None)
- [ ] Dict has all 4 fields: decision, reason, details, timestamp
- [ ] Uses "reindex_spawned" (not "reindex_success")
- [ ] Details is structured dict {"trigger": "stop_hook"} (not plain string)
- [ ] Comments explain forensic logging (START already logged, END will be logged later)

---

#### Task 1.9: Section 8 - Exception Handling

**Action:** Add exception handler that returns dict and prints error

**Code to Add:**
```python
    except Exception as e:
        # ═══════════════════════════════════════════════════════════════
        # SECTION 8: Exception Handling (KEEP - stop.py expects dict)
        # ═══════════════════════════════════════════════════════════════
        # REASON: Hook must not crash, stop.py expects dict return
        print(f"⚠️  Auto-indexing error: {e}\n", file=sys.stderr)
        return {
            "decision": "skip",
            "reason": "exception",
            "details": {"trigger": "stop_hook", "error": str(e)},
            "timestamp": timestamp
        }
```

**Source:** Current `reindex_on_stop()` lines 1742-1750 (EXACT)

**Reason:** stop.py expects dict return (not exception propagation). User needs to see error message.

**Critical Implementation Fidelity:**
- ✅ Includes `print()` to stderr (line 1744)
- ✅ Returns structured details dict with error field (line 1748)

**Verification:**
- [ ] Prints error to stderr (not stdout)
- [ ] Error message includes emoji "⚠️"
- [ ] Returns dict (not raising exception)
- [ ] Dict has error in details field
- [ ] Uses `timestamp` variable (defined outside try block)

---

#### Task 1.10: Verify Complete Function

**Action:** Review entire function for correctness

**Verification Checklist:**
- [ ] All 8 sections present in order
- [ ] No syntax errors (matching parentheses, colons, indentation)
- [ ] All functions called exist in reindex_manager.py: read_prerequisites_state, get_project_root, get_reindex_config, should_reindex_after_cooldown, get_last_reindex_time, log_reindex_start, spawn_background_reindex
- [ ] All imports available: datetime, timezone, subprocess
- [ ] Return dict structure consistent across all returns
- [ ] Comments explain rationale for each section
- [ ] Function placed after spawn_background_reindex() (line 1167)

**Expected Line Count:** ~120 lines (function signature to final return)

---

### STEP 2: Update stop.py Hook

**File:** `.claude/hooks/stop.py`
**Risk:** MEDIUM (changes existing hook behavior)

#### Task 2.1: Update Function Call

**Action:** Change `reindex_on_stop()` to `reindex_on_stop_background()`

**Current Code (line 116):**
```python
decision = reindex_manager.reindex_on_stop()
```

**New Code:**
```python
decision = reindex_manager.reindex_on_stop_background()
```

**Verification:**
- [ ] Function name changed to `reindex_on_stop_background`
- [ ] No arguments passed (uses config default for cooldown)
- [ ] Variable name still `decision` (used in lines 119-141)

---

#### Task 2.2: Update Message Handling for New Decision Codes

**Action:** Update decision code handling to recognize "reindex_spawned"

**Current Code (lines 125-141):**
```python
# Human-readable output
if decision.get('decision') == 'run':
    print(f"✅ Stop hook: Auto-reindex completed", flush=True)
elif decision.get('decision') == 'skip':
    reason = decision.get('reason', 'unknown')
    if reason not in ['cooldown_active', 'no_changes']:
        print(f"⏭️  Stop hook: Auto-reindex skipped ({reason})", flush=True)
```

**New Code:**
```python
# Human-readable output
if decision.get('decision') == 'run':
    reason = decision.get('reason', 'unknown')
    if reason == 'reindex_spawned':
        # Background mode - process spawned but outcome unknown
        print(f"✅ Stop hook: Index update spawned in background", flush=True)
    else:
        # Unexpected reason for 'run' decision
        print(f"✅ Stop hook: Auto-reindex {reason}", flush=True)
elif decision.get('decision') == 'skip':
    reason = decision.get('reason', 'unknown')
    if reason not in ['cooldown_active', 'no_changes']:
        print(f"⏭️  Stop hook: Auto-reindex skipped ({reason})", flush=True)
```

**Reason:** Background mode uses "reindex_spawned" instead of "reindex_success". Message should reflect that outcome is unknown.

**Verification:**
- [ ] Checks for reason == 'reindex_spawned'
- [ ] Message says "spawned in background" (not "completed")
- [ ] Fallback for unexpected 'run' reasons
- [ ] Skip handling unchanged
- [ ] Uses `flush=True` for immediate display

---

### STEP 3: Test New Implementation

**Risk:** LOW (testing doesn't break anything)

#### Task 3.1: Manual Test - Background Spawn Works

**Action:** Trigger stop hook and verify background spawn

**Test Steps:**
1. Start Claude Code session
2. Make a trivial change (e.g., add comment to test file)
3. Stop Claude Code (triggers stop hook)
4. Check logs immediately

**Expected Results:**
```bash
# logs/stop-hook-debug.log
[timestamp] Stop hook STARTED
[timestamp] reindex_on_stop_background() returned: run - reindex_spawned
[timestamp] Stop hook COMPLETED

# Console output
✅ Stop hook: Index update spawned in background
```

**Verification:**
- [ ] Stop hook returns immediately (<5 seconds)
- [ ] Decision is "run - reindex_spawned"
- [ ] Message shows "spawned in background"
- [ ] No timeout after 50 seconds
- [ ] Background process appears in logs/reindex-operations.jsonl with START event

---

#### Task 3.2: Manual Test - Concurrent Detection Works

**Action:** Trigger stop hook while reindex running

**Test Steps:**
1. Start long-running reindex manually: `bash .claude/skills/semantic-search/scripts/incremental-reindex .`
2. While running, trigger stop hook (stop Claude Code)
3. Check logs

**Expected Results:**
```bash
# logs/stop-hook-debug.log
[timestamp] reindex_on_stop_background() returned: skip - concurrent_reindex

# logs/reindex-operations.jsonl
{"event": "start", "trigger": "stop-hook", "skipped": true, "skip_reason": "concurrent_reindex"}
```

**Verification:**
- [ ] Decision is "skip - concurrent_reindex"
- [ ] START event logged with skipped=True
- [ ] NO orphaned START event (has matching skip entry)
- [ ] Concurrent reindex continues uninterrupted

---

#### Task 3.3: Manual Test - Cooldown Works

**Action:** Trigger stop hook twice in rapid succession

**Test Steps:**
1. Trigger stop hook (stop Claude Code)
2. Wait 10 seconds (< 300s cooldown)
3. Restart and immediately stop Claude Code again
4. Check logs

**Expected Results:**
```bash
# logs/stop-hook-debug.log
[timestamp] First call: run - reindex_spawned
[timestamp] Second call: skip - cooldown_active

# Second call details should show:
"cooldown_seconds": 300,
"elapsed_seconds": 10,
"remaining_seconds": 290
```

**Verification:**
- [ ] First call spawns successfully
- [ ] Second call skips with cooldown_active
- [ ] elapsed_seconds and remaining_seconds calculated correctly
- [ ] No second reindex spawned

---

#### Task 3.4: Manual Test - Prerequisites Check Works

**Action:** Simulate missing prerequisites

**Test Steps:**
1. Temporarily rename prerequisites state file:
   ```bash
   mv logs/state/semantic-search-prerequisites.json logs/state/semantic-search-prerequisites.json.bak
   ```
2. Trigger stop hook
3. Check logs
4. Restore file:
   ```bash
   mv logs/state/semantic-search-prerequisites.json.bak logs/state/semantic-search-prerequisites.json
   ```

**Expected Results:**
```bash
# logs/stop-hook-debug.log
[timestamp] reindex_on_stop_background() returned: skip - prerequisites_not_ready
```

**Verification:**
- [ ] Decision is "skip - prerequisites_not_ready"
- [ ] No spawn attempted
- [ ] Details includes state_file path
- [ ] File restored successfully

---

#### Task 3.5: Verify Background Completion

**Action:** Confirm background reindex completes successfully

**Test Steps:**
1. Trigger stop hook (spawns background reindex)
2. Wait 5 minutes (allow completion)
3. Check forensic logs

**Expected Results:**
```bash
# logs/reindex-operations.jsonl
{"event": "start", "trigger": "stop-hook", "mode": "background", "pid": XXXXX}
# ... 200-350 seconds later ...
{"event": "end", "operation_id": "reindex_..._XXXXX", "status": "completed", "duration_seconds": 210.5}
```

**Verification:**
- [ ] START event logged with mode=background
- [ ] END event logged after 200-350 seconds
- [ ] Status is "completed" (not failed)
- [ ] No timeout at 50 seconds
- [ ] Duration matches expected range

---

### STEP 4: Remove Old Code

**Risk:** LOW (old code no longer called)

#### Task 4.1: Remove Old reindex_on_stop() Function

**File:** `.claude/utils/reindex_manager.py`
**Lines to Remove:** 1623-1750 (old synchronous version)

**Action:** Delete entire function

**Verification:**
- [ ] Function `reindex_on_stop()` no longer exists
- [ ] Function `reindex_on_stop_background()` exists
- [ ] No references to old function remain (grep for "reindex_on_stop()")
- [ ] stop.py calls `reindex_on_stop_background()` only

---

#### Task 4.2: Remove Dead Code - auto_reindex_on_session_start()

**File:** `.claude/utils/reindex_manager.py`
**Lines to Remove:** 1441-1524 (approximately, verify exact range)

**Context:** User asked: "Did you remove the onsession start index hook, or it is a dead code now?"

**Action:** Find and remove `auto_reindex_on_session_start()` function

**Verification:**
- [ ] Function removed completely
- [ ] No references remain (grep for "auto_reindex_on_session_start")
- [ ] First-prompt hook uses `spawn_background_reindex()` directly

---

#### Task 4.3: Remove Dead Code - _reindex_on_session_start_core()

**File:** `.claude/utils/reindex_manager.py`
**Lines to Remove:** 1757-1820+ (approximately, verify exact range)

**Action:** Find and remove `_reindex_on_session_start_core()` function

**Verification:**
- [ ] Function removed completely
- [ ] No references remain (grep for "_reindex_on_session_start_core")
- [ ] No other code depends on this function

---

### STEP 5: Final Verification

**Risk:** LOW (verification only)

#### Task 5.1: Code Review Checklist

**Action:** Complete code review

**Checklist:**
- [ ] **New function complete:** `reindex_on_stop_background()` has all 8 sections
- [ ] **stop.py updated:** Calls new function, handles new decision codes
- [ ] **Old code removed:** No `reindex_on_stop()`, `auto_reindex_on_session_start()`, `_reindex_on_session_start_core()`
- [ ] **No duplicated code:** Reused existing functions, no copy-paste
- [ ] **Imports present:** subprocess, datetime, timezone
- [ ] **All helper functions exist:** Verified in reindex_manager.py
- [ ] **Decision dict structure consistent:** All returns have 4 fields
- [ ] **Comments accurate:** Explain rationale for each section

---

#### Task 5.2: End-to-End Integration Test

**Action:** Full workflow test

**Test Scenario:**
1. Start fresh Claude Code session
2. First-prompt triggers background reindex (verify in logs)
3. Make file changes during first-prompt reindex
4. Stop Claude Code (triggers stop hook)
5. Verify stop hook detects concurrent reindex
6. Wait for first-prompt reindex to complete
7. Restart Claude Code, stop immediately
8. Verify stop hook spawns successfully
9. Wait 5 minutes, verify completion

**Expected Flow:**
```
Session Start → First-prompt reindex (START event)
  ↓
Stop hook triggered while first-prompt running
  ↓
Stop hook: skip - concurrent_reindex (no orphaned START)
  ↓
First-prompt reindex completes (END event)
  ↓
Restart/Stop → Stop hook spawns (START event, decision: reindex_spawned)
  ↓
Background reindex completes (END event, status: completed)
```

**Verification:**
- [ ] First-prompt reindex completes (200-350s)
- [ ] Stop hook during concurrent shows skip - concurrent_reindex
- [ ] No orphaned START events in logs/reindex-operations.jsonl
- [ ] Stop hook after completion spawns successfully
- [ ] Background reindex completes without timeout
- [ ] All forensic logs show matching START/END events

---

#### Task 5.3: Performance Verification

**Action:** Verify no performance regression

**Metrics to Check:**
```bash
# Hook execution time (should be <5s)
grep "Stop hook STARTED" logs/stop-hook-debug.log -A 2

# Background reindex completion time (should be 200-350s)
grep "event.*end.*stop-hook" logs/reindex-operations.jsonl
```

**Expected Results:**
- [ ] Stop hook returns in <5 seconds (not 50 seconds)
- [ ] Background reindex completes in 200-350 seconds
- [ ] No timeout failures
- [ ] User sees "spawned in background" message immediately

---

## Success Criteria

### ✅ Must Have (All Required)

1. **No Timeout Failures**
   - Stop hook returns in <5 seconds
   - Background reindex completes successfully (no 50s timeout)

2. **Forensic Logging Integrity**
   - Every START event has matching END event (no orphans)
   - Concurrent detection logs START with skipped=True

3. **Business Logic Preserved**
   - Prerequisites check prevents doomed spawns
   - Cooldown prevents spam on rapid restarts
   - Decision dict structure compatible with stop.py

4. **Architecture Matches First-Prompt**
   - Direct spawn_background_reindex() call
   - Message shown before spawn
   - No index exists check (script handles it)

5. **Dead Code Removed**
   - No old reindex_on_stop()
   - No auto_reindex_on_session_start()
   - No _reindex_on_session_start_core()

### 🎯 Nice to Have (Optional)

1. **Performance Improvement**
   - Hook execution time <2 seconds (vs current 50s timeout)
   - User sees immediate feedback

2. **Code Quality**
   - Clear comments explaining each section
   - Evidence-based rationale in docstring
   - No code duplication

---

## Rollback Plan

### If Implementation Fails

**Immediate Actions:**
1. `git checkout .` - Revert all changes
2. Verify stop.py calls old `reindex_on_stop()`
3. Test old synchronous pattern still works
4. Investigate failure root cause

**Partial Rollback:**
If new function has bugs but old code removed:
1. Restore old `reindex_on_stop()` from git history
2. Update stop.py to call old function
3. Fix bugs in new function offline
4. Re-test and re-deploy

**Common Issues:**
- **Import errors:** Verify subprocess imported
- **Function not found:** Check function name spelling
- **Decision dict errors:** Verify all 4 fields present
- **Concurrent detection false positives:** Check PID parsing logic

---

## Risk Assessment

### LOW RISK ✅
- Creating new function (doesn't break existing code)
- Testing (read-only verification)
- Removing dead code (not called anywhere)

### MEDIUM RISK ⚠️
- Updating stop.py (changes hook behavior)
- Removing old reindex_on_stop() (can't rollback easily)

### MITIGATION ✅
- Git clean status (easy rollback)
- Incremental testing (catch bugs early)
- Proven pattern (copy from first-prompt)
- Comprehensive verification (end-to-end test)

---

## Implementation Timeline

**Estimated Time:** 2-3 hours

1. **Step 1 (Create Function):** 45-60 minutes
   - Ultra-careful implementation of 8 sections
   - Line-by-line verification

2. **Step 2 (Update stop.py):** 15-20 minutes
   - Function call change
   - Message handling update

3. **Step 3 (Testing):** 60-90 minutes
   - 5 manual tests
   - Wait for background completion
   - Verify all scenarios

4. **Step 4 (Remove Old Code):** 10-15 minutes
   - Delete 3 functions
   - Verify no references

5. **Step 5 (Final Verification):** 20-30 minutes
   - Code review
   - End-to-end test
   - Performance verification

**Total:** ~150-215 minutes (2.5-3.5 hours)

---

## Conclusion

This implementation plan provides ultra-detailed, step-by-step guidance for migrating stop-hook from synchronous to background pattern. Every step includes:

- Clear action description
- Source code references
- Verification criteria
- Expected outcomes
- Risk assessment

The merged plan combines:
- **NEW plan's structure:** 8 clear sections, concurrent PID check from start
- **OLD plan's fidelity:** Exact implementation details from current code

Following this plan ensures correct implementation while preserving all business logic and fixing the 50-second timeout bug.
