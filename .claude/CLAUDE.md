# Project Instructions for anthropic_research

## CRITICAL: Research Orchestration Rules

### ALWAYS Use multi-agent-researcher Skill When:

**Trigger Keywords in User Prompt**:
- **Search/Discovery**: "search", "find", "find out", "look up", "look into", "discover", "uncover"
- **Investigation**: "research", "investigate", "analyze", "study", "explore", "examine", "survey", "assess", "evaluate", "review", "inspect", "probe", "scrutinize"
- **Collection**: "gather", "collect", "compile"
- **Learning**: "learn about", "tell me about", "dig into", "delve into"
- **Contextual**: "what are the latest", "comprehensive", "deep dive", "thorough investigation", "in-depth", "detailed overview", "landscape of", "state of the art", "best practices"

**MANDATORY Workflow**:
1. **STOP** - Do NOT use WebSearch/WebFetch directly for research tasks
2. **INVOKE**: Use `/skill multi-agent-researcher` or let it auto-activate
3. **DECOMPOSE**: Break topic into 2-4 focused subtopics
4. **PARALLEL**: Spawn researcher agents simultaneously (NOT sequentially)
5. **SYNTHESIZE**: Aggregate findings into comprehensive report

### Direct Tool Use vs Skill Orchestration

**Use WebSearch/WebFetch directly ONLY for**:
- Single factual lookups (e.g., "What is the capital of France?")
- Quick documentation checks (e.g., "How to use Array.map in JavaScript?")
- Specific URL fetches (e.g., "Fetch this exact GitHub README")

**Use multi-agent-researcher Skill for**:
- Multi-source research (2+ sources)
- Comprehensive topic investigation
- Comparative analysis
- Literature reviews
- Market research
- Technology surveys
- ANY task requiring synthesis across multiple sources

### Example Violations to AVOID

❌ **WRONG**: User asks "investigate MCP servers for research"
   → I do 15 sequential WebSearch calls myself

✅ **CORRECT**: User asks "investigate MCP servers for research"
   → I invoke multi-agent-researcher skill
   → Skill spawns 3 parallel researchers
   → Each researcher investigates subtopic
   → I spawn report-writer agent for synthesis
   → Report-writer agent creates final report

### Self-Check Before Acting

**Before using WebSearch/WebFetch, ask yourself**:
1. Is this a research task requiring multiple sources? → Use Skill
2. Will I need to synthesize information? → Use Skill
3. Am I about to do >3 searches on related topics? → Use Skill
4. Did user say "research", "investigate", "analyze"? → Use Skill

## CRITICAL: Synthesis Phase Enforcement

### ⚠️ ARCHITECTURAL CONSTRAINT ACTIVE

When multi-agent-researcher skill is active, you **DO NOT HAVE WRITE TOOL ACCESS**. The skill's `allowed-tools` frontmatter EXCLUDES the Write tool to enforce proper workflow delegation.

### Synthesis Phase Requirements

**ABSOLUTE PROHIBITION**:
- ❌ Orchestrator writing synthesis reports directly
- ❌ Creating files in files/reports/ yourself
- ❌ Using "direct synthesis" approach
- ❌ Bypassing report-writer agent
- ❌ Attempting to write reports when skill is active

**MANDATORY WORKFLOW**:
- ✅ Spawn report-writer agent via Task tool
- ✅ Agent reads ALL files/research_notes/*.md files
- ✅ Agent synthesizes findings into comprehensive report
- ✅ Agent writes to files/reports/{topic}_{timestamp}.md
- ✅ Orchestrator reads final report and delivers to user

### Self-Check Before Synthesis

**Before attempting synthesis, ask yourself**:
1. Am I the orchestrator with multi-agent-researcher skill active? → MUST use report-writer agent
2. Do I have Write tool access? → If NO, spawn report-writer agent
3. Have all research notes been completed? → Verify with Glob before synthesis
4. Am I about to write to files/reports/? → STOP, delegate to report-writer agent

### Why This Enforcement Exists

**Problem Identified**: Orchestrator was doing synthesis directly, bypassing the report-writer agent's specialized synthesis capabilities.

**Solution**: Architectural constraint - orchestrator lacks Write tool when skill is active, making it physically impossible to write reports. This forces proper delegation.

**Reliability**: ~95% enforcement (cannot be bypassed through prompt injection)

### Example Violation and Correction

❌ **WRONG**: After researchers complete
   → I read the research notes
   → I write synthesis report myself
   → Result: Tool permission error (Write not in allowed-tools)

✅ **CORRECT**: After researchers complete
   → I verify all notes exist with Glob
   → I spawn report-writer agent via Task tool
   → Agent reads notes and writes comprehensive report
   → I read final report and deliver to user

---

## Available Skills

- **multi-agent-researcher**: Orchestrates 2-4 parallel researchers for comprehensive topic investigation

## Available Agents

- **researcher**: Web research agent (WebSearch, Write, Read) - DO NOT invoke directly, use via skill
- **report-writer**: Synthesis agent (Read, Glob, Write)

## File Organization

- `files/research_notes/`: Individual researcher outputs (one file per subtopic)
- `files/reports/`: Comprehensive synthesis reports (timestamped)
- Name format: `topic-slug_YYYYMMDD-HHMMSS.md`

## Commit Standards

When committing research work:
- Separate commits for: infrastructure, individual research notes, synthesis reports
- Include key statistics in commit messages
- Tag with source counts and confidence levels
- Co-author attribution to Claude

---

**REMEMBER**: You built the orchestrator - USE IT! Don't play all the instruments yourself when you have an orchestra.
