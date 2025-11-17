# Skill Usage Decision Tree

## When User Prompt Arrives

```
┌─────────────────────────────────────┐
│   User Prompt Received              │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Contains research  │
    │ keywords?          │◄─── research, investigate, analyze,
    │                    │     study, examine, explore,
    └────┬───────────┬───┘     comprehensive, survey, etc.
         │           │
      YES│           │NO
         │           │
         ▼           ▼
    ┌────────────┐  ┌─────────────────┐
    │ Multiple   │  │ Single factual  │
    │ sources    │  │ lookup?         │
    │ needed?    │  │ (e.g., "What is │
    └────┬───┬───┘  │  X?")           │
         │   │      └────┬────────────┘
      YES│   │NO         │
         │   │           │
         │   │           ▼
         │   │      ┌─────────────────┐
         │   │      │ Use direct tool │
         │   │      │ (WebFetch,      │
         │   │      │  WebSearch)     │
         │   │      └─────────────────┘
         │   │
         │   ▼
         │  ┌─────────────────┐
         │  │ Check: >3       │
         │  │ searches        │
         │  │ needed?         │
         │  └────┬────────┬───┘
         │       │        │
         │    YES│        │NO
         │       │        │
         ▼───────┘        │
    ┌─────────────────────────┐  │
    │ USE                     │  │
    │ multi-agent-researcher  │  │
    │ SKILL                   │  │
    │                         │  │
    │ Steps:                  │  │
    │ 1. Decompose into       │  │
    │    2-4 subtopics        │  │
    │ 2. Spawn researchers    │  │
    │    IN PARALLEL          │  │
    │ 3. Synthesize report    │  │
    └─────────────────────────┘  │
                                 │
                                 ▼
                            ┌────────────┐
                            │ Use direct │
                            │ tools with │
                            │ caution    │
                            └────────────┘
```

## Quick Checklist

**Before using WebSearch/WebFetch directly, check ALL boxes**:

- [ ] Is this a SINGLE factual question? (not research)
- [ ] Do I need ONLY 1 source?
- [ ] Will I NOT need to synthesize across sources?
- [ ] Did user NOT say: research, investigate, analyze, study?

**If ANY box is unchecked** → Use `multi-agent-researcher` skill

## Examples

### ✅ Use Skill

- "Research MCP servers for web search"
- "Investigate notification system design patterns"
- "Analyze the impact of quantum computing on cryptography"
- "What are the latest developments in AI code generation?"
- "Comprehensive analysis of mini-app architectures"
- "Study the effectiveness of different frameworks"
- "Examine best practices for X"
- "Survey available tools for Y"

### ❌ Don't Use Skill (Direct Tool OK)

- "What is the capital of France?" (single fact)
- "Fetch https://example.com/readme" (specific URL)
- "How do I use Array.map?" (single documentation lookup)
- "What version of Node.js is current?" (single fact)

## Red Flags (Skill Was Needed But Not Used)

**If you find yourself doing these, you MISSED using the skill**:

1. ❌ Doing 5+ sequential WebSearch calls on related topics
2. ❌ Fetching multiple web pages and synthesizing yourself
3. ❌ Creating a comprehensive report manually
4. ❌ User said "investigate" but you used direct tools
5. ❌ Spawning agents manually instead of via skill
6. ❌ Writing synthesis yourself instead of using report-writer

## Recovery

**If you realize mid-task you should have used the skill**:

1. STOP current approach
2. Acknowledge the error
3. Invoke the appropriate skill
4. Complete task using proper orchestration
5. Document lesson learned

---

**Remember**: The skill exists to orchestrate parallel research efficiently. Using it is not optional when the criteria match - it's the correct architecture.
