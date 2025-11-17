# Multi-Agent Research System

A Skills-based orchestration system that conducts comprehensive research by coordinating multiple specialized AI agents.

## Overview

This skill replicates and enhances Anthropic's SDK-based research-agent using Claude Code's native Skills approach.

**Key Features**:
- Auto-invokes on research queries
- Spawns 2-4 researcher agents in parallel
- Synthesizes findings into comprehensive reports
- Saves structured outputs (research notes + final report)
- Progress tracking via TodoWrite
- Zero external dependencies

## How It Works

1. **Query Analysis**: Breaks research question into 2-4 focused subtopics
2. **Parallel Research**: Spawns researcher agents simultaneously
3. **Synthesis**: Combines findings into cohesive report
4. **Delivery**: Provides summary with file locations

## Usage

### Automatic Invocation
Simply ask a research question:
```
"Research the impact of AI on software development"
"Investigate quantum computing breakthroughs in 2025"
"What are the latest trends in remote work?"
```

### Manual Invocation
```
/skill multi-agent-researcher
```

## Components

- **researcher.md**: Individual research agent (WebSearch + Write)
- **report-writer.md**: Synthesis agent (Read + Glob + Write)
- **SKILL.md**: Orchestration logic (Task + TodoWrite)

## Output Structure

```
files/
├── research_notes/
│   ├── subtopic-1.md
│   ├── subtopic-2.md
│   └── subtopic-3.md
└── reports/
    └── topic-name_YYYYMMDD-HHMMSS.md
```

## Examples

### Simple Research (2-3 subtopics)
**Query**: "Research remote work productivity"
**Duration**: 30-40 minutes
**Output**: 3 research notes + 1 comprehensive report

### Complex Research (4 subtopics)
**Query**: "Investigate AGI development and implications"
**Duration**: 45-60 minutes
**Output**: 4 research notes + 1 comprehensive report

## Comparison to SDK Version

| Feature | SDK | Skills | Winner |
|---------|-----|--------|--------|
| Setup | Python + deps | Markdown only | Skills |
| Customization | Code editing | Markdown editing | Skills |
| Auto-invoke | No | Yes | Skills |
| Testing | Unit tests | Manual | SDK |
| Portability | Any Python | Claude Code only | SDK |

## Customization

### Domain-Specific Variants
Create specialized versions for:
- Academic research (peer-reviewed focus)
- Market research (business metrics focus)
- Technical research (code + docs focus)

### Agent Variants
Add specialized researchers:
- academic-researcher (scholar.google.com)
- industry-researcher (company reports)
- technical-researcher (GitHub + Stack Overflow)

## Troubleshooting

**Skill doesn't auto-invoke**: Expand description in SKILL.md
**Agents spawn sequentially**: Fix parallel Task calls
**Research notes not found**: Check Glob pattern
**Poor quality**: Refine agent instructions

## Version History

- **v1.0.0** (Jan 2025): Initial implementation
  - 2-4 parallel researchers
  - Flexible synthesis
  - File-based output
  - TodoWrite tracking

## Credits

Based on Anthropic's research-agent SDK demo, translated to Claude Code Skills approach.
