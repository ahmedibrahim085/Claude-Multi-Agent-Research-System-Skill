# Project Instructions for anthropic_research

@import ~/.claude/CLAUDE.md

---

## CRITICAL: Response Timestamp Requirement

**For all prompts, as a first and final hook, remember to include a date/time stamp your response, as well as the execution time from start to finish.**

---

@import ../docs/workflows/research-workflow.md
@import ../docs/workflows/planning-workflow.md
@import ../docs/workflows/compound-request-handling.md
@import ../docs/workflows/semantic-search-hierarchy.md
@import ../docs/configuration/configuration-guide.md
@import ../docs/guides/token-savings-guide.md

---

## CRITICAL: Universal Orchestration Rules

This project uses **3 specialized skills** with **hook-based auto-activation**. The imported workflows above contain detailed trigger keywords, examples, and step-by-step instructions. These critical rules are high-level decision gates to ensure you use the orchestration system correctly.

### Research Tasks: multi-agent-researcher Skill

**ALWAYS use when:**
- Multi-source research (2+ sources)
- Topic investigation requiring synthesis
- Comparative analysis, literature reviews, market research

**NEVER:**
- Use WebSearch/WebFetch directly for research tasks
- Write synthesis reports yourself (Write tool excluded when skill active)

**MANDATORY:**
- Delegate synthesis to report-writer agent (reads research_notes/, writes to reports/)
- Verify all research notes exist before synthesis

**Self-check:** Multi-source? Synthesis needed? >3 searches? → Use skill

### Planning Tasks: spec-workflow-orchestrator Skill

**ALWAYS use when:**
- New features or systems (non-trivial additions)
- Architecture changes, multi-component work (>3 files)
- Requirements gathering, formal specifications, ADRs

**NEVER:**
- Manual planning with TodoWrite for non-trivial work
- Start planning without invoking skill first

**MANDATORY:**
- Quality gate enforced: 85% threshold (100 points, 4 criteria, 3 max iterations)
- 3-agent workflow: spec-analyst → spec-architect → spec-planner

**Self-check:** New feature? Specs needed? >3 files? → Use skill

### Content Search: semantic-search Skill

**ALWAYS use FIRST when:**
- Searching for functionality/content by describing WHAT it does
- Finding patterns, similar implementations, documentation
- Exploring unfamiliar codebase

**NEVER:**
- Use Grep/Glob as first attempt for functionality searches
- Skip semantic search and go directly to keyword searches

**VALUE PROPOSITION:**
- Saves 5,000-10,000 tokens vs traditional Grep exploration (~90% reduction)
- Example: "user authentication logic" → 1 search, 2 file reads vs 15+ Grep attempts, 26 file reads

**Self-check:** Searching for functionality? → Semantic search first, Grep as fallback

### Compound Requests

**When BOTH research AND planning triggered simultaneously:**
- Hook message: "COMPOUND REQUEST DETECTED"
- **MUST** use AskUserQuestion with standard options
- Wait for user response before invoking any skill
- **NEVER** assume user intent or skip clarification

---

## System Architecture

**Hooks** (`user-prompt-submit.py`): Auto-detect trigger keywords → suggest/activate skills
**Skills**: Orchestrate specialized agents in parallel/sequential workflows
**Agents**: Execute research, planning, synthesis, semantic search operations
**Progressive Disclosure**: @import loads detailed workflows on-demand, keeping core context focused

For detailed workflows, trigger keywords, examples, configuration reference, and token economics, see imported documentation above.

---

## CRITICAL: Timestamp Analysis Rules

**MANDATORY for ALL timestamp operations to prevent timezone confusion errors.**

### NEVER Do Mental Math on Timestamps

❌ **WRONG**: "Last index 11:10, now 12:18, so ~68 minutes"
✅ **CORRECT**: Use utility script or code function

### Three-Layer Prevention System

**Layer 1: Use Utility Script for Ad-Hoc Analysis**
```bash
python .claude/utils/verify_timestamp.py <file_path> <field_name>
python .claude/utils/verify_timestamp.py --raw "2025-12-11T11:10:21+00:00" "Event"
```

**Layer 2: Use Built-In Function for Code Analysis**
```python
from reindex_manager import get_reindex_timing_analysis

timing = get_reindex_timing_analysis(project_path)
print(f"Last reindex: {timing['last_reindex_utc']} ({timing['last_reindex_local']})")
print(f"Current time: {timing['current_utc']} ({timing['current_local']})")
print(f"Elapsed: {timing['elapsed_display']}")
print(f"Status: {timing['cooldown_status']}")
```

**Layer 3: Always Label Timezones Explicitly**
- ✅ "11:10 UTC (12:10 CET)"
- ✅ "Current: 12:18 CET (11:18 UTC)"
- ❌ "11:10" (missing timezone)
- ❌ "now 12:18" (which timezone?)

### Mandatory Rules

1. **NEVER calculate elapsed time mentally** - Always use Python code
2. **ALWAYS show both UTC and local** when reporting times
3. **ALWAYS label timezone** - Never write time without UTC/CET/local annotation
4. **USE utility script** for any ad-hoc timestamp analysis
5. **USE get_reindex_timing_analysis()** for reindex timing in code

### Why This Matters

**Past Error**: Reported "~68 minutes elapsed" when actual elapsed was 8 minutes
**Root Cause**: Mixed UTC timestamp (11:10) with local time (12:18) in mental calculation
**Prevention**: These mandatory rules + utility tools

---

## Architecture Decision Records

**Auto-Reindex Design**: Direct Script vs Agent
- **Decision**: Use direct bash scripts for automatic reindex (session start, post-write hooks)
- **Rationale**: 5x faster (2.7s vs 14.6s), $0 cost vs $144/year per 10 developers, works offline, predictable
- **Agent Use**: Reserved for manual operations where intelligence and rich output add value
- **Full ADR**: `docs/architecture/ADR-001-direct-script-vs-agent-for-auto-reindex.md`
- **Quick Reference**: `docs/architecture/auto-reindex-design-quick-reference.md`
