# Auto-Reindex Design: Quick Reference

**Last Updated**: 2025-12-03
**Full ADR**: [ADR-001: Direct Script vs Agent](./ADR-001-direct-script-vs-agent-for-auto-reindex.md)

---

## TL;DR

**Automatic reindex uses direct bash scripts (fast, free, reliable)**
**Manual reindex uses semantic-search-indexer agent (intelligent, interactive)**

---

## When to Use What

### ✅ Use Direct Script (Current Implementation)

**Automatic Operations:**
- Session start reindex
- Post-file-modification reindex (Write/Edit/NotebookEdit tools)
- Any hook-based operation
- Background maintenance

**Why:**
- **5x faster** (2.7s vs 14.6s)
- **$0 cost** (vs $144/year per 10 devs)
- **Works offline**
- **Predictable** (same behavior every time)
- **Safe** (won't timeout hooks)

---

### ✅ Use Agent (semantic-search-indexer)

**Manual Operations:**
- User explicitly requests reindex
- First-time setup
- Troubleshooting index issues
- Manual full reindex
- Index diagnostics

**Why:**
- **Intelligent** (adaptive decisions)
- **Interactive** (can ask questions)
- **Rich output** (progress, stats, guidance)
- **User-friendly** (explains what happened)

---

## Performance Comparison

| Metric | Direct Script | Agent | Winner |
|--------|---------------|-------|--------|
| **Speed** | 2.7s | 14.6s | Script (5.4x) |
| **Cost** | $0.00 | $0.02/run | Script ($144/yr savings) |
| **Offline** | ✅ Yes | ❌ No | Script |
| **Predictable** | ✅ Yes | ⚠️ Variable | Script |
| **Timeout Risk** | ✅ Low | ⚠️ Medium | Script |
| **Intelligence** | ❌ Low | ✅ High | Agent |
| **Rich Output** | ❌ Minimal | ✅ Detailed | Agent |

---

## Code Examples

### Auto-Reindex (Direct Script) ✓

```python
# .claude/utils/reindex_manager.py
def run_incremental_reindex_sync(project_path: Path) -> Optional[bool]:
    """Fast, direct execution for automatic operations"""
    script = project_root / '.claude' / 'skills' / 'semantic-search' / 'scripts' / 'incremental-reindex'

    result = subprocess.run(
        [str(script), str(project_path)],
        timeout=50,
        capture_output=True,
        text=True
    )

    return result.returncode == 0
```

**Output:**
```
🔄 Updating semantic search index...
✅ Semantic search index updated
```

---

### Manual Reindex (Agent) ✓

```python
# User types: "reindex my project"
# semantic-search-indexer agent spawned
# Agent runs scripts and provides rich output
```

**Output:**
```
✅ Successfully indexed the project!

Indexing Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project: my-web-app
Files Processed: 342 files
Chunks Created: 2,348 semantic content chunks
Time taken: 156.3 seconds (~2.6 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The semantic index is ready! You can now:
1. Search for code by describing what it does...
```

---

## Cost Analysis

### Annual Cost (10 Developers)

**Scenario:** 2 auto-reindexes per developer per day

| Approach | Cost |
|----------|------|
| Direct Script | **$0.00** ✓ |
| Agent | **$144.00** ❌ |

**Savings: $144/year per 10 developers**

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  AUTOMATIC (Background)                 │
│  ├─ Session start hook                  │
│  └─ Post-write hook                     │
│     └─> DIRECT SCRIPT                   │
│         ├─ 2.7 seconds                  │
│         ├─ $0 cost                      │
│         └─ Works offline                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  MANUAL (User-invoked)                  │
│  └─ User command                        │
│      └─> AGENT                          │
│          ├─ 10-20 seconds               │
│          ├─ $0.02 cost                  │
│          ├─ Rich output                 │
│          └─ Intelligence                │
└─────────────────────────────────────────┘
```

---

## Decision Criteria

### Choose Direct Script If:

- ✅ Speed critical (< 5s needed)
- ✅ High frequency (> 5 times/day)
- ✅ User not watching
- ✅ Background operation
- ✅ Hook execution (timeout constraints)
- ✅ Offline support needed
- ✅ Predictable behavior required
- ✅ Cost sensitive

### Choose Agent If:

- ✅ User explicitly invoked
- ✅ User is waiting (can take 10-20s)
- ✅ Complex decisions needed
- ✅ User interaction valuable
- ✅ Rich output helpful
- ✅ Intelligence adds value
- ✅ Error diagnosis needed
- ✅ One-time operation

---

## Common Scenarios

### Scenario 1: Session Start ✓ Direct Script

**User opens Claude Code**
→ Session start hook fires
→ Direct script: 2.7s
→ ✅ Index updated silently
→ User starts working immediately

---

### Scenario 2: File Save ✓ Direct Script

**User saves file**
→ Post-write hook fires
→ Cooldown check (skip if recent)
→ If needed: Direct script 2.7s
→ ✅ Index updated in background
→ User continues working

---

### Scenario 3: Manual Full Reindex ✓ Agent

**User types: "reindex with full rebuild"**
→ semantic-search-indexer agent spawns
→ Agent runs full reindex: 2-3 minutes
→ Agent provides detailed progress
→ ✅ User sees statistics, guidance
→ Agent explains next steps

---

### Scenario 4: Index Corruption ✓ Agent

**User: "Search isn't working"**
→ User manually investigates
→ Spawns agent for diagnosis
→ Agent detects corruption
→ Agent recommends full reindex
→ Agent executes with explanation
→ ✅ Problem resolved with context

---

## Key Metrics

### Performance Benchmarks

```
Direct Script (Auto):
├─ Average time: 2.71s
├─ Variance: ±0.03s
└─ Consistency: Very high ✓

Agent Approach (Manual):
├─ Average time: 14.6s
├─ Variance: ±2.0s
└─ Consistency: Variable
```

### Hook Timeout Safety

```
Direct Script:
├─ Max execution: 50s (script timeout)
├─ Hook timeout: 60s
└─ Safety buffer: 10s ✓ SAFE

Agent:
├─ Typical: 14.6s
├─ Worst case: 60s+ (if retries/full reindex)
└─ Safety buffer: Variable ⚠️ RISKY
```

---

## FAQs

### Q: Why not use agent for everything?

**A:** Agent adds 5x overhead (14.6s vs 2.7s), costs $144/year per 10 developers, and risks hook timeout. For background operations, speed and reliability trump intelligence.

---

### Q: When would agent approach make sense for auto-reindex?

**A:** Never. Background operations need:
- Speed (user not waiting)
- Predictability (same every time)
- Zero cost (high frequency)
- Offline support (plane, no internet)

Agent provides: Intelligence, rich output, interaction
→ **Wrong tool for background automation**

---

### Q: Can we make the script smarter?

**A:** Yes! Add lightweight bash checks:
```bash
if corruption_detected; then
    echo "⚠️ Manual full reindex needed"
    exit 1
fi
```

**Benefits:**
- Still fast (bash logic instant)
- Still free ($0 cost)
- Adds helpful guidance

**This is future enhancement direction** ✓

---

### Q: What if script fails?

**A:** Fails fast with clear error:
```
⚠️ Index update failed: Permission denied
```

User can:
1. Check error message
2. Fix issue (permissions, disk space, etc.)
3. Manually run full reindex if needed
4. Use agent for diagnosis if complex

**Better than agent masking error with retry attempts that timeout**

---

## References

**Full Documentation:**
- [ADR-001: Direct Script vs Agent for Auto-Reindex](./ADR-001-direct-script-vs-agent-for-auto-reindex.md)

**Implementation:**
- `.claude/utils/reindex_manager.py` - Direct script execution
- `.claude/agents/semantic-search-indexer.md` - Agent definition
- `.claude/hooks/session-start-index.py` - Session start hook
- `.claude/hooks/post-tool-use-track-research.py` - Post-write hook

**Testing:**
- `docs/guides/incremental-reindex-validation.md` - Test results
- `docs/testing/incremental-reindex-agent-test.md` - Agent testing

---

## Decision Summary

✅ **CORRECT CHOICE**: Direct script for auto-reindex
- Proven by: Performance (5x faster), Cost ($144/yr savings), Reliability (deterministic)
- Use case: Background automation with strict constraints

✅ **COMPLEMENTARY**: Agent for manual operations
- Value add: Intelligence, rich output, user interaction
- Use case: User-invoked operations where time and cost acceptable

**This is optimal hybrid architecture** 🎯
