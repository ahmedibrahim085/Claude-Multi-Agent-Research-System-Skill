# Plugin Usage Guide

## Quick Start

The Multi-Agent Research plugin automatically activates when you use research-related keywords or slash commands.

### Slash Commands

| Command | Subtopics | Time | Use Case |
|---------|-----------|------|----------|
| `/research <topic>` | 3 | ~15-20min | Standard comprehensive research |
| `/research-quick <topic>` | 2 | ~10min | Quick overviews, time-sensitive |
| `/research-deep <topic>` | 4 | ~25-30min | Complex topics, strategic analysis |

### Natural Language Triggers

The skill auto-activates when your prompt contains:

**Research Keywords**: research, investigate, analyze, study, explore, examine, survey, assess, evaluate, review

**Discovery Keywords**: search, find, discover, uncover, learn about, dig into

**Context Keywords**: comprehensive, deep dive, thorough, in-depth, detailed overview, latest developments, best practices

---

## How It Works

### The Orchestration Workflow

```
1. Adaptive Decomposition
   └─→ AI selects optimal pattern based on topic type
   
2. Parallel Researchers
   └─→ 2-4 specialized agents spawned simultaneously
   
3. Multi-Tool Search (v2.5.0)
   └─→ Each researcher queries multiple MCP tools
   
4. Incremental Synthesis (v2.5.0 - optional)
   └─→ Progressive report building
   
5. Final Synthesis
   └─→ Report-writer creates comprehensive report
```

### File Organization

```
files/
├── research_notes/        # Individual researcher findings
│   ├── subtopic-1.md
│   ├── subtopic-2.md
│   └── subtopic-3.md
│
└── reports/              # Synthesized reports
    └── topic-name_20251125-001234.md
```

---

## When to Use the Skill

### ✅ Use Skill For

- **Multi-source research** (needs 2+ sources)
- **Comprehensive investigations** (multiple angles)
- **Comparative analysis** (comparing alternatives)
- **Literature reviews** (academic/technical)
- **Market research** (trends, landscape)
- **Technology surveys** (tool comparisons)
- **ANY task requiring synthesis** across sources

### ❌ Don't Use Skill For

- **Single fact lookups** ("What is X?")
- **Specific URL fetches** ("Fetch this README")
- **Quick documentation** ("How to use Array.map?")
- **Simple questions** (1 source sufficient)

---

## Decision Tree

```
User Request
     │
     ▼
Contains research keywords?
     │
     ├─YES─→ Multiple sources needed?
     │           │
     │           ├─YES─→ USE SKILL ✅
     │           │
     │           └─NO──→ >3 searches needed?
     │                       │
     │                       ├─YES─→ USE SKILL ✅
     │                       └─NO──→ Direct tools OK
     │
     └─NO──→ Single factual lookup?
                 │
                 └─YES─→ Direct tools OK
```

### Quick Checklist

**Before using direct tools, ALL must be true**:
- [ ] Single factual question (not research)
- [ ] Need ONLY 1 source
- [ ] No synthesis needed
- [ ] User didn't say: research, investigate, analyze

**If ANY is false** → Use the skill

---

## Examples

### ✅ Skill Activates

```
"Research MCP servers for web search"
"Investigate notification system patterns"
"Analyze quantum computing impact on cryptography"
"What are the latest AI developments?"
"Comprehensive analysis of mini-app architectures"
"Study framework effectiveness"
```

### ❌ Direct Tools OK

```
"What is the capital of France?"
"Fetch https://example.com/readme"
"How do I use Array.map?"
"What version of Node.js is current?"
```

---

## Advanced Features (v2.5.0)

### Multi-Tool Parallel Search

Researchers can query all 4 MCP tools simultaneously:

**Benefits**:
- 30-50% more sources
- Cross-validation (sources in 2+ engines = higher confidence)
- Redundancy (survives individual tool failures)

**Coverage Summary**:
```
Total Unique Sources: 11
Cross-Validated: 4 sources (HIGH CONFIDENCE)
- Source A (found in: Exa, Tavily)
- Source B (found in: All 4 engines)
```

### Adaptive Decomposition

AI automatically selects the best decomposition pattern:

| Pattern | When Used | Example |
|---------|-----------|---------|
| **Temporal** | History, evolution, timeline | Past → Present → Future |
| **Categorical** | Types, categories | Type A, B, C |
| **Stakeholder** | Multiple perspectives | Technical, Business, Policy |
| **Problem-Solution** | Challenges, issues | Threats → Defenses → Gaps |
| **Geographic** | Regional topics | US, Europe, Asia |
| **Hierarchical** | Layers, levels | Infrastructure, Platform, Software |

### Incremental Synthesis

Get insights faster with progressive reporting:

```
Standard:    ░░░░░░░░░░░░░░░░░░░░ 100% @ 20 min
Incremental: ██████░░░░░░░░░░░░░░  33% @ 7 min
             ████████████░░░░░░░░  66% @ 14 min
             ████████████████████ 100% @ 20 min
```

**Benefits**: 13 minutes earlier access to first insights

---

## Architecture Enforcement

### Synthesis Phase

The skill uses **architectural constraints** to ensure quality:

**What This Means**:
- Orchestrator lacks Write tool access (by design)
- Must delegate synthesis to report-writer agent
- Cannot bypass proper workflow

**Why**:
- Ensures comprehensive synthesis
- Prevents premature conclusions
- Maintains separation of concerns

**Your Experience**:
- Fully automatic
- No action needed
- Just trust the process

---

## Red Flags (You're Not Using It Correctly)

If you notice these, stop and use the skill:

1. ❌ Making 5+ sequential searches manually
2. ❌ Fetching multiple pages and synthesizing yourself
3. ❌ Creating comprehensive reports manually
4. ❌ User said "investigate" but you used direct tools
5. ❌ Spawning agents manually instead of via skill

**Recovery**: Stop, invoke the skill, let it orchestrate

---

## Configuration Defaults

The plugin uses these optimal defaults:

- **Max Parallel Researchers**: 4
- **Default Model**: Claude Sonnet
- **File Naming**: 
  - Research notes: `{subtopic-slug}.md`
  - Reports: `{topic-slug}_{timestamp}.md`
- **Synthesis**: Mandatory delegation to report-writer
- **Quality Gates**: Enabled

---

## Tips for Best Results

1. **Be specific in your topic** - Clear topics get better decomposition
2. **Use slash commands** for control over research depth
3. **Trust the process** - Let parallel researchers work
4. **Review interim reports** (if incremental synthesis enabled)
5. **Check cross-validated sources** - Highest confidence data

---

## Troubleshooting

### Skill Doesn't Activate

- Check your keywords (use "research", "investigate", etc.)
- Or use slash commands explicitly
- Verify plugin is enabled: `/plugin list`

### Researchers Taking Long

- Expected: 5-10 min per researcher
- MCP tools may need time (especially first use)
- Check internet connection

### No Final Report

- Verify all researchers completed
- Check `files/research_notes/` for all files
- Report-writer needs all notes present

---

**Remember**: The skill exists to orchestrate high-quality research efficiently. When criteria match, using it is the correct architecture, not optional.
