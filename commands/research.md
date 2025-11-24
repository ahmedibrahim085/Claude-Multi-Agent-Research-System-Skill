---
description: Start comprehensive multi-agent research
---

# Research Command

Start a comprehensive research session with parallel multi-agent coordination.

## Usage

```
/research <topic>
```

## What This Does

1. **Activates**: `multi-agent-researcher` skill
2. **Decomposition**: Breaks topic into 3 subtopics (optimal depth)
3. **Parallel Research**: Spawns 3 specialized researchers simultaneously
4. **MCP Tools**: Uses Exa, Tavily, Brave, and Perplexity search
5. **Synthesis**: Report-writer agent creates comprehensive report
6. **Output**: Research notes + final report in `files/`

## Example

```
/research quantum error correction
```

This will research:
- Theoretical foundations
- Hardware implementations  
- Commercial viability

## Time Estimate

15-20 minutes for complete research cycle.

## See Also

- `/research-quick` - Faster research with 2 subtopics
- `/research-deep` - Comprehensive research with 4 subtopics
