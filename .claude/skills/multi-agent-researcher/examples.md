# Multi-Agent Researcher - Examples

## Example 1: Technology Research (MCP Servers)

### User Request
> "Research MCP servers that could help with web research and data collection"

### Orchestrator Response

**Step 1: Topic Decomposition**
- Subtopic 1: MCP protocol fundamentals and architecture
- Subtopic 2: Available MCP server implementations for web/data
- Subtopic 3: Integration patterns with Claude Code
- Subtopic 4: Authentication and rate limiting considerations

**Step 2: Parallel Agent Spawning**
```markdown
Spawning 4 researcher agents in parallel:
- Task 1: researcher → "MCP protocol fundamentals"
- Task 2: researcher → "MCP server implementations"
- Task 3: researcher → "Claude Code integration patterns"
- Task 4: researcher → "Authentication and rate limits"
```

**Step 3: Research Notes Generated**
- `files/research_notes/mcp-protocol-fundamentals.md` (1,245 words, 5 sources)
- `files/research_notes/mcp-server-implementations.md` (1,580 words, 7 sources)
- `files/research_notes/claude-code-integration.md` (1,120 words, 4 sources)
- `files/research_notes/authentication-rate-limits.md` (980 words, 3 sources)

**Step 4: Synthesis Delegation**
```markdown
Spawning report-writer agent:
- Input: All 4 research notes in files/research_notes/
- Task: Synthesize into comprehensive MCP servers report
- Output: files/reports/mcp-servers-for-research_20251119-142037.md
```

**Step 5: Report Delivered**
- Final report: 4,925 words
- Total sources: 19 unique citations
- Key findings: 3 recommended MCP servers with integration guides

---

## Example 2: Market Analysis

### User Request
> "Analyze the AI code editor market to understand competitive landscape"

### Orchestrator Response

**Topic Decomposition**
- Subtopic 1: Current market players (Cursor, GitHub Copilot, Tabnine, etc.)
- Subtopic 2: Feature comparison and differentiation
- Subtopic 3: User adoption metrics and feedback analysis

**Parallel Research**
- 3 researchers spawned simultaneously
- Total research time: ~8 minutes (vs 24 minutes if sequential)

**Research Notes**
- `files/research_notes/ai-editor-market-players.md` (1,620 words)
- `files/research_notes/ai-editor-feature-comparison.md` (1,890 words)
- `files/research_notes/user-adoption-feedback.md` (1,340 words)

**Synthesis Report**
- `files/reports/ai-code-editor-market_20251119-153422.md`
- 5,150 words with competitive analysis matrix
- Recommendations for product positioning

---

## Example 3: Technical Literature Review

### User Request
> "Study retrieval-augmented generation techniques for code understanding"

### Orchestrator Response

**Topic Decomposition**
- Subtopic 1: RAG fundamentals and architecture patterns
- Subtopic 2: Code-specific embedding techniques
- Subtopic 3: Retrieval strategies for source code
- Subtopic 4: Evaluation metrics and benchmark studies

**Parallel Research**
- 4 researchers spawned with academic focus
- Emphasis on recent papers (2023-2025)

**Research Notes**
- `files/research_notes/rag-fundamentals.md` (1,450 words, 6 papers cited)
- `files/research_notes/code-embedding-techniques.md` (1,680 words, 8 papers)
- `files/research_notes/code-retrieval-strategies.md` (1,320 words, 5 papers)
- `files/research_notes/rag-evaluation-metrics.md` (1,180 words, 4 papers)

**Synthesis Report**
- `files/reports/rag-for-code-understanding_20251119-161559.md`
- 5,630 words with technical depth
- 23 academic citations
- Implementation recommendations with code patterns

---

## Example 4: Quick Factual Research (Single Topic)

### User Request
> "What are the latest features in Claude Sonnet 4.5?"

### Orchestrator Decision
**Does NOT invoke multi-agent-researcher skill**

**Rationale**:
- Single factual lookup (1 source sufficient)
- No need for synthesis across multiple sources
- Quick documentation check

**Action**: Direct WebSearch for Claude Sonnet 4.5 release notes

**Lesson**: Use skill for multi-source research, not single factual queries

---

## Example 5: Best Practices Research

### User Request
> "Investigate best practices for building production-ready LLM agents"

### Orchestrator Response

**Topic Decomposition**
- Subtopic 1: Agent architecture patterns (ReAct, planning, reflection)
- Subtopic 2: Error handling and reliability strategies
- Subtopic 3: Prompt engineering and tool integration
- Subtopic 4: Testing, monitoring, and deployment

**Parallel Research**
- 4 researchers with focus on production systems
- Mix of academic papers and industry blog posts

**Research Notes**
- `files/research_notes/agent-architecture-patterns.md` (1,550 words)
- `files/research_notes/agent-reliability-strategies.md` (1,420 words)
- `files/research_notes/prompt-engineering-tools.md` (1,680 words)
- `files/research_notes/agent-testing-deployment.md` (1,380 words)

**Synthesis Report**
- `files/reports/llm-agent-best-practices_20251119-174822.md`
- 6,030 words with actionable recommendations
- Case studies from production systems
- Implementation checklist for agent reliability

---

## Anti-Pattern Examples

### ❌ Wrong: Sequential Research
```markdown
# DON'T DO THIS
1. Spawn researcher for subtopic 1, wait for completion
2. Spawn researcher for subtopic 2, wait for completion
3. Spawn researcher for subtopic 3, wait for completion
# This takes 3x longer!
```

### ✅ Correct: Parallel Research
```markdown
# DO THIS INSTEAD
Spawn all researchers in SINGLE message:
- Task 1: researcher agent for subtopic 1
- Task 2: researcher agent for subtopic 2
- Task 3: researcher agent for subtopic 3
# All run simultaneously, 3x faster
```

---

### ❌ Wrong: Direct Synthesis
```markdown
# DON'T DO THIS
1. Researchers complete
2. I read all research notes myself
3. I write synthesis report directly to files/reports/
# Result: Tool permission error (no Write access)
```

### ✅ Correct: Delegated Synthesis
```markdown
# DO THIS INSTEAD
1. Researchers complete
2. Verify all notes exist with Glob
3. Spawn report-writer agent via Task tool
4. Agent reads notes and writes comprehensive report
5. I read final report and deliver to user
```

---

## Output Quality Examples

### Research Note Quality (Good Example)
```markdown
# MCP Protocol Fundamentals

## Overview
The Model Context Protocol (MCP) is an open protocol that standardizes
communication between LLM applications and external data sources...

[1,245 words total]

## Key Concepts
- Server-client architecture
- Bidirectional communication channels
- Resource providers and tools

[Technical depth with code examples]

## Sources
1. MCP Specification - https://modelcontextprotocol.io/docs
2. Anthropic MCP Announcement - https://www.anthropic.com/news/mcp
3. GitHub MCP Servers Repository - https://github.com/anthropics/mcp-servers
4. MCP Integration Guide - https://docs.anthropic.com/mcp
5. Community MCP Servers - https://github.com/topics/mcp-server
```

### Synthesis Report Quality (Good Example)
```markdown
# Comprehensive Analysis: MCP Servers for Research

## Executive Summary
This report analyzes the Model Context Protocol (MCP) ecosystem with
focus on servers useful for web research and data collection. Based on
analysis of 19 sources across 4 subtopics, we identify 3 recommended...

[4,925 words total]

## Cross-Cutting Insights
- MCP's standardization enables easier integration than custom APIs
- Authentication patterns vary widely across server implementations
- Rate limiting is critical for production deployments

[Deep synthesis connecting findings across all subtopics]

## Practical Recommendations
1. Start with `@modelcontextprotocol/server-puppeteer` for web scraping
2. Use `@modelcontextprotocol/server-brave-search` for web search
3. Implement authentication via environment variables

[Actionable guidance based on synthesized research]

## Complete Source List
[All 19 sources with full citations]
```

---

## Integration Examples

### Research + Planning Workflow

**Step 1: Research Phase**
```markdown
User: "Research best practices for task management apps"
→ multi-agent-researcher skill activated
→ 4 researchers investigate UX patterns, features, tech stacks, accessibility
→ Comprehensive report generated
```

**Step 2: Planning Phase**
```markdown
User: "Plan a task management app incorporating best practices from research"
→ spec-workflow-orchestrator skill activated
→ spec-analyst uses research findings to inform requirements
→ spec-architect designs architecture based on researched tech stacks
→ spec-planner creates tasks implementing researched UX patterns
```

**Result**: Research-backed, well-informed specifications ready for development

---

## Usage Tips

1. **Be Specific**: "Research MCP servers for web scraping" better than "Research MCP"
2. **Scope Appropriately**: 2-4 subtopics optimal (1 too narrow, 5+ too broad)
3. **Trust the Process**: Let report-writer synthesize, don't try to write yourself
4. **Verify Quality**: Check research notes before synthesis (length, sources, depth)
5. **Iterate if Needed**: If synthesis misses key points, can re-run with refined prompts

## Command Shortcut

Use `/research-topic` command for quick invocation:
```markdown
/research-topic

[Edit the template with your specific research topic]
```
