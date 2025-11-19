# Multi-Agent Researcher - Reference Guide

## Overview

The multi-agent-researcher skill orchestrates parallel web research using specialized researcher agents, then synthesizes findings into comprehensive reports via a dedicated report-writer agent.

## Architecture

### Orchestration Flow
1. **Topic Decomposition**: Orchestrator breaks user's research topic into 2-4 focused subtopics
2. **Parallel Research**: Spawns 2-4 researcher agents simultaneously (NOT sequentially)
3. **Synthesis**: Spawns report-writer agent to aggregate findings into comprehensive report

### Agent Roles

#### researcher.md
- **Location**: `.claude/agents/researcher.md`
- **Tools**: WebSearch, Write, Read
- **Purpose**: Conduct focused research on assigned subtopic
- **Output**: Individual research note in `files/research_notes/{subtopic-slug}.md`

#### report-writer.md
- **Location**: `.claude/agents/report-writer.md`
- **Tools**: Read, Glob, Write
- **Purpose**: Synthesize all research notes into comprehensive report
- **Output**: Final report in `files/reports/{topic-slug}_{timestamp}.md`

## Skill Configuration

### Frontmatter (SKILL.md)
```yaml
---
name: multi-agent-researcher
description: Orchestrates parallel research agents for comprehensive topic investigation
allowed-tools: Read, Glob, TodoWrite, Task, WebSearch, WebFetch
---
```

**CRITICAL**: Write tool is **EXCLUDED** from allowed-tools to enforce mandatory delegation to report-writer agent for synthesis.

### Trigger Keywords
- Search/Discovery: "search", "find", "discover", "look up", "uncover"
- Investigation: "research", "investigate", "analyze", "study", "explore"
- Collection: "gather", "collect", "compile"
- Learning: "learn about", "tell me about", "dig into"

## File Organization

### Research Notes Directory
**Path**: `files/research_notes/`
- Individual researcher agent outputs (one file per subtopic)
- Format: `{subtopic-slug}.md` (e.g., `mcp-protocol-basics.md`)
- Gitignored for privacy

### Reports Directory
**Path**: `files/reports/`
- Comprehensive synthesis reports
- Format: `{topic-slug}_{timestamp}.md` (e.g., `mcp-servers_20251119-142037.md`)
- Gitignored for privacy

## Workflow Steps

### Step 1: Topic Analysis
- Orchestrator analyzes user's research request
- Identifies scope, depth requirements, and focus areas
- Determines optimal number of subtopics (2-4)

### Step 2: Subtopic Decomposition
- Breaks topic into focused, non-overlapping subtopics
- Ensures comprehensive coverage without redundancy
- Assigns clear research scope to each subtopic

### Step 3: Parallel Agent Spawning
**CRITICAL**: Spawn all researchers in PARALLEL, not sequentially
```markdown
Use multiple Task tool calls in SINGLE message:
- Task 1: researcher agent for subtopic 1
- Task 2: researcher agent for subtopic 2
- Task 3: researcher agent for subtopic 3
```

### Step 4: Output Verification
- Wait for all researcher agents to complete
- Use Glob to verify all research notes exist: `files/research_notes/*.md`
- Check file sizes and content quality

### Step 5: Synthesis Delegation
**MANDATORY**: Spawn report-writer agent via Task tool
- Agent reads ALL research notes
- Synthesizes findings with citations
- Writes comprehensive report to `files/reports/`

### Step 6: Report Delivery
- Orchestrator reads final report
- Delivers key findings to user
- Provides file path for full report

## Quality Standards

### Research Notes (Per Subtopic)
- 800-1,500 words minimum
- Multiple authoritative sources (3-5+ per subtopic)
- Proper citations with URLs
- Clear section structure
- Technical depth appropriate to topic

### Synthesis Report
- Executive summary
- Comprehensive findings across all subtopics
- Cross-subtopic analysis and connections
- Practical recommendations
- Full source list with citations
- 2,500-5,000+ words for comprehensive topics

## Common Patterns

### Technology Survey
**Example**: "Research MCP servers for web research integration"
- Subtopic 1: MCP protocol basics and architecture
- Subtopic 2: Available MCP server implementations
- Subtopic 3: Integration patterns and best practices
- Subtopic 4: Security and authentication considerations

### Market Research
**Example**: "Analyze AI code editor market landscape"
- Subtopic 1: Current market players and features
- Subtopic 2: Technology stack comparison
- Subtopic 3: User adoption and feedback analysis
- Subtopic 4: Future trends and opportunities

### Literature Review
**Example**: "Study RAG techniques for code understanding"
- Subtopic 1: Core RAG concepts and algorithms
- Subtopic 2: Code-specific embedding approaches
- Subtopic 3: Retrieval strategies for code
- Subtopic 4: Evaluation metrics and benchmarks

## Error Handling

### Agent Discovery Issues
- Verify researchers exist: `ls .claude/agents/researcher.md`
- Check frontmatter format is valid YAML
- Ensure agent names match Task tool `subagent_type` parameter

### Write Permission Errors
**Symptom**: Orchestrator tries to write report directly
**Cause**: Architectural constraint - orchestrator lacks Write tool
**Fix**: Always delegate synthesis to report-writer agent

### Incomplete Research
**Symptom**: Some research notes missing or empty
**Fix**:
1. Check researcher agent errors in logs
2. Verify WebSearch access permissions
3. Re-spawn failed researcher agents individually

## Best Practices

1. **Parallel Execution**: Always spawn researchers in parallel for speed
2. **Clear Subtopics**: Ensure subtopics are focused and non-overlapping
3. **Quality Gates**: Verify research notes before synthesis
4. **Mandatory Delegation**: NEVER write reports directly, always use report-writer agent
5. **Comprehensive Scope**: Break complex topics into 3-4 subtopics for thorough coverage

## Troubleshooting

### "Agent type 'researcher' not found"
**Cause**: Agent not in standard registry location
**Fix**: Verify agents are in `.claude/agents/`, NOT `.claude/skills/*/agents/`

### Empty Research Notes
**Cause**: WebSearch rate limiting or poor query formulation
**Fix**: Check agent logs, adjust search queries, retry with refined prompts

### Synthesis Skipped
**Cause**: Orchestrator trying to bypass report-writer agent
**Fix**: Architectural constraint prevents this - if attempted, tool permission error will occur

## Integration with Planning Skill

The multi-agent-researcher skill can be used BEFORE spec-workflow-orchestrator to gather requirements:

1. **Research Phase**: Investigate similar products, technologies, best practices
2. **Planning Phase**: Use research findings to inform requirements and architecture
3. **Development Phase**: Implement based on research-informed specifications

**Example Workflow**:
1. "Research task management app best practices" → multi-agent-researcher
2. "Plan a task management web app with features found in research" → spec-workflow-orchestrator
3. Implement with research-backed decisions
