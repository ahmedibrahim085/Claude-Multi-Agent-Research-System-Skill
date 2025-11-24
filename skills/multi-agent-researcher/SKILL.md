---
name: multi-agent-researcher
description: Conduct comprehensive research on any topic by coordinating 2-4 specialized researcher agents in parallel, then synthesizing findings into a detailed report via mandatory report-writer agent delegation
allowed-tools: Task, Read, Glob, TodoWrite
version: 2.1.2
---

# Multi-Agent Research Coordinator

## Purpose

Transform complex research questions into comprehensive reports by:
1. Decomposing broad topics into 2-4 focused subtopics
2. Spawning specialized researcher agents in parallel
3. Synthesizing findings into cohesive final report
4. Saving structured outputs for reference

## Search Tool Availability

This plugin provides **4 MCP search servers** to enhance research quality:

| Server | Type | Best For |
|--------|------|----------|
| **Exa** | Remote HTTP | Academic/technical research |
| **Tavily** | Remote HTTP | Current events, news |
| **Brave** | Local (npx) | Privacy-focused search |
| **Perplexity** | Local (npx) | AI-powered synthesis |

**First-Time Setup**: Brave and Perplexity auto-install on first use (~30s delay).

Researchers have automatic access to these tools without explicit declaration.


## When to Use

Auto-invoke when user asks:
- **Search/Discovery**: "Search what is [topic]", "Find information about [subject]", "Look up [technology]", "Discover [patterns]"
- **Investigation**: "Research [topic]", "Investigate [subject]", "Analyze [phenomenon]", "Study [field]", "Explore [domain]"
- **Collection**: "Gather information about [subject]", "Collect data on [topic]", "Compile resources for [area]"
- **Learning**: "Learn about [subject]", "Tell me about [topic]", "Dig into [technology]", "Delve into [concept]"
- **Contextual**: "What are the latest developments in [field]?", "Comprehensive analysis of [topic]", "Deep dive into [subject]", "State of the art in [domain]", "Best practices for [area]"

Do NOT invoke for:
- Simple factual questions ("What is the capital of France?")
- Decision evaluation ("Should I use X or Y?")
- Code-related tasks ("Debug this function", "Write a script")

## Orchestration Workflow

### Phase 1: Query Analysis & Decomposition

**Step 1.1: Understand the Research Question**
Analyze user's query to identify core topic, scope, and intent.

**Step 1.2: Adaptive Decomposition**

Use AI-powered pattern selection for optimal subtopic breakdown.

**Sub-step A: Analyze Topic Characteristics**

Identify the topic type to select the best decomposition pattern:

| Topic Type | Indicators | Example | Pattern |
|------------|-----------|---------|---------|
| **Temporal** | Time progression keywords (history, evolution, future) | "Evolution of AI" | Past → Present → Future |
| **Categorical** | Natural category divisions | "Programming languages" | Compiled, Interpreted, Hybrid |
| **Stakeholder** | Multiple perspectives/groups | "Climate policy" | Scientific, Economic, Political, Social |
| **Problem-Solution** | Issue-focused, challenges | "Cybersecurity threats" | Threats → Defenses → Gaps → Future |
| **Geographic** | Location-based, regional | "Healthcare systems" | US, Europe, Asia, Global |
| **Hierarchical** | Layers/levels | "Cloud computing" | Infrastructure, Platform, Software |

**Sub-step B: Select Optimal Pattern**

Decision logic:
```
IF topic contains {history, evolution, timeline, past, future} 
  → Use Temporal pattern

ELSE IF topic has {types, categories, kinds, classifications}
  → Use Categorical pattern

ELSE IF topic involves {stakeholders, perspectives, groups, actors}
  → Use Stakeholder pattern

ELSE IF topic mentions {problem, challenge, issue, threat}
  → Use Problem-Solution pattern

ELSE IF topic spans {regions, countries, global, international}
  → Use Geographic pattern

ELSE IF topic has {layers, levels, hierarchy, stack}
  → Use Hierarchical pattern

ELSE
  → Use Categorical (default)
```

**Sub-step C: Generate Subtopics**

Apply selected pattern to create 2-4 well-balanced subtopics.

**Example 1: Temporal**
```
Topic: "Quantum Error Correction Development"
Pattern: Temporal (contains "development" = progression)
Subtopics:
1. Historical Foundations (1990s-2010)
2. Current State-of-Art (2020-2025)
3. Future Directions (2025+)
```

**Example 2: Problem-Solution**
```
Topic: "AI Safety Challenges"
Pattern: Problem-Solution (contains "challenges")
Subtopics:
1. Current AI Safety Threats
2. Existing Mitigation Strategies
3. Research Gaps & Future Work
```

**Example 3: Stakeholder**
```
Topic: "Cryptocurrency Regulation"
Pattern: Stakeholder (involves governments, users, industry)
Subtopics:
1. Government/Regulatory Perspective
2. Industry/Exchange Perspective
3. User/Consumer Perspective
4. Technical/Developer Perspective
```

**Step 1.3: Create Research Plan**
Use TodoWrite to track:
```
- [ ] Decompose query into subtopics
- [ ] Spawn researcher 1: [subtopic]
- [ ] Spawn researcher 2: [subtopic]
- [ ] Spawn researcher 3: [subtopic]
- [ ] Synthesize findings
- [ ] Save final report
```

---

### Phase 2: Parallel Research Execution

**Step 2.1: Spawn Researcher Agents in Parallel**

For each subtopic, create a Task tool call with:
```
subagent_type: "researcher"
description: "Research {subtopic name}"
prompt: "Research the following subtopic in depth:

**Subtopic**: {Subtopic name}
**Context**: Part of research on '{original topic}'
**Focus**: {Specific guidance}

Conduct thorough web research, gather authoritative sources, extract key findings, and save results to files/research_notes/{subtopic-slug}.md"
```

**Critical**: Spawn ALL researchers in parallel (multiple Task calls in same message), not sequentially.

**After spawning, notify user of progress**:
```
✅ Research initiated: {N} parallel researchers spawned
- Researcher 1: {subtopic name}
- Researcher 2: {subtopic name}
- Researcher 3: {subtopic name}

⏱️ Estimated completion: ~15-20 minutes
🔍 MCP tools available: Exa, Tavily, Brave, Perplexity
```

**Step 2.2: Monitor Completion**
Update TodoWrite as researchers complete.

**Step 2.3: Verify All Complete**
Use Glob to confirm all files exist: `files/research_notes/*.md`

---

### Phase 3: Synthesis & Report Generation

**Standard Path**: See below for mandatory report-writer delegation.

**Incremental Path** (Optional): See Phase 3A for progressive synthesis.

---

### Phase 3A: Incremental Synthesis (Optional - v2.5.0)

> **Use when**: Speed is priority, user wants early insights

**Process Overview**:
Instead of waiting for all researchers to complete, begin synthesis progressively as each finishes.

**Step 3A.1: First Researcher Complete**
When FIRST researcher finishes:
```
Task:
subagent_type: "incremental-synthesizer"
description: "Start progressive report building"
prompt: "Initialize report framework:
- Create draft report structure
- Add findings from completed researcher
- Mark pending sections as IN PROGRESS
- Save as files/reports/{topic}_draft_v1.md"
```

**Step 3A.2: Progressive Updates**
For EACH additional completing researcher:
- increm ental-synthesizer updates draft report
- Adds new findings
- Updates cross-cutting insights
- Publishes new version (v2, v3...)

**Step 3A.3: Final Synthesis**
When ALL researchers complete:
- incremental-synthesizer finalizes report
- Comprehensive cross-analysis
- Removes [DRAFT] label
- Publishes final version

**Benefits**:
- ✅ Faster time-to-first-insight (~7 min vs ~20 min)
- ✅ Progressive value delivery
- ✅ Early feedback opportunity

**Trade-offs**:
- ⚠️ Multiple report revisions
- ⚠️ Additional agent overhead
- ⚠️ Preliminary insights may change

**Timeline**:
```
Standard: ░░░░░░░░░░░░░░░░░░░░ 100% @ 20 min
Incremental: ██████░░░░░░░░░░░░░░ 33% @ 7 min
             ████████████░░░░░░░░ 66% @ 14 min
             ████████████████████ 100% @ 20 min
```

---

### Phase 3: Synthesis & Report Generation (Standard)

**⚠️ CRITICAL: ARCHITECTURAL ENFORCEMENT ACTIVE ⚠️**

**YOU DO NOT HAVE WRITE TOOL ACCESS** when this skill is active. The `allowed-tools` frontmatter explicitly EXCLUDES the Write tool to enforce proper workflow delegation.

**YOU CANNOT**:
- ❌ Write synthesis reports yourself
- ❌ Create files in files/reports/ directory
- ❌ Bypass the report-writer agent

**YOU MUST**:
- ✅ Spawn report-writer agent via Task tool
- ✅ Delegate all synthesis and report writing to the agent
- ✅ Read the completed report and deliver to user

---

**Step 3.1: Verify Research Completion**

1. Use Glob to confirm all research notes exist: `files/research_notes/*.md`
2. Verify count matches number of spawned researchers
3. If any missing: investigate and complete before synthesis

**Step 3.2: Spawn Report-Writer Agent (MANDATORY)**

**This is the ONLY synthesis approach** - there is no "Option A" or "Option B". You MUST use the report-writer agent because you lack Write tool permissions.

```
Task:
subagent_type: "report-writer"
description: "Synthesize research findings into comprehensive report"
prompt: "Synthesize research into comprehensive report:

**Original Question**: {user query}
**Subtopics Researched**: {list all subtopics}
**Notes Location**: files/research_notes/

## Your Tasks:
1. Read ALL research notes from files/research_notes/
2. Identify themes, patterns, and contradictions across notes
3. Synthesize findings into cohesive narrative
4. Cite sources from research notes
5. Add cross-cutting insights beyond individual notes
6. Save comprehensive report to files/reports/{topic-slug}_{timestamp}.md

## Report Structure:
- Executive Summary
- Key Findings (with evidence from research notes)
- Detailed Analysis by subtopic
- Cross-Cutting Themes
- Contradictions and Debates
- Gaps and Limitations
- Source Bibliography

Use the timestamp format: $(date +\"%Y%m%d-%H%M%S\") for the filename."
```

**Step 3.3: Monitor Agent Completion**

After spawning report-writer agent, wait for completion. The agent will:
- Read all research notes
- Synthesize findings
- Write comprehensive report to files/reports/
- Return completion message with file path

---

### Phase 4: Deliver Results

**Step 4.1: Create User Summary**
```markdown
# ✅ Research Complete: {Topic}

Comprehensive research completed with {N} specialized researchers.

## 🔑 Key Findings
1. {Finding 1}
2. {Finding 2}
3. {Finding 3}

## 🔬 Research Scope
{N} subtopics investigated:
- {Subtopic 1}
- {Subtopic 2}
- {Subtopic 3}

## 📁 Files Generated
**Research Notes**: `files/research_notes/`
- {file1}.md
- {file2}.md
- {file3}.md

**Final Report**: `files/reports/{filename}.md`

## 🎯 Next Steps
{Optional suggestions}

---

**💡 Tip**: Use `/research-quick` for faster results or `/research-deep` for comprehensive analysis.
```

**Step 4.2: Update TodoWrite**
Mark all items complete.

---

## Best Practices

### Good Decomposition
✅ 2-4 subtopics (sweet spot: 3)
✅ Distinct but related
✅ Comprehensive coverage
✅ Independently researchable

❌ Too many (>5)
❌ Too few (1)
❌ Significant overlap
❌ Too narrow or too broad

### Parallel Execution
- Always spawn researchers simultaneously
- Never sequential unless dependent
- Provide context to each researcher
- Reasonable scope (10-15 min each)

### Synthesis Quality
- Read ALL notes
- Find connections across subtopics
- Note contradictions explicitly
- Cite sources
- Add insights beyond individual notes

---

## Error Handling

**Researcher Fails**: Try replacement, proceed with others, note gap
**No Results Found**: Accept partial, note limitation
**Contradictory Findings**: Document all perspectives explicitly
**Unclear Query**: Ask clarifying questions first

---

## Examples

**Query**: "Research quantum error correction"
**Decomposition**:
1. Theoretical foundations
2. Hardware implementations
3. Commercial viability
**Researchers**: 3 parallel
**Synthesis**: report-writer agent (MANDATORY)

**Query**: "Investigate cryptocurrency market 2025"
**Decomposition**:
1. Market metrics & players
2. Regulatory landscape
3. Technology evolution
4. Institutional trends
**Researchers**: 4 parallel
**Synthesis**: report-writer agent (MANDATORY)

---

**Remember**: Quality depends on good decomposition, thorough researchers, insightful synthesis, and clear user communication.
