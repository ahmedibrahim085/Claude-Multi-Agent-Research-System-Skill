---
name: balanced-decision-analyzer
description: Orchestrate dual-perspective analysis for technical and business decisions by spawning opportunity-finder and risk-assessor agents in parallel
allowed-tools: Task, Read, Write
version: 1.0.0
---

# Balanced Decision Analyzer

## Purpose

Provide balanced analysis for decisions by coordinating two specialized agents:
- **Opportunity Finder**: Optimistic perspective (benefits, opportunities)
- **Risk Assessor**: Critical perspective (risks, challenges)

## When to Use

Activate this skill when the user asks about:
- "Should we [decision]?"
- "What are the pros and cons of [approach]?"
- "Is [technology/approach] a good choice?"
- "Evaluate [decision/approach]"
- Any decision-making or evaluation request

## Orchestration Process

### Step 1: Parse the Decision
Extract the core decision or approach being evaluated from the user's request.

### Step 2: Spawn Analysis Agents in Parallel

Use the Task tool to spawn both agents simultaneously:

**Agent 1: opportunity-finder**
- Prompt: "Analyze this decision from an optimistic perspective: [DECISION]. Identify benefits, opportunities, success patterns, and potential value. Be thorough but realistic."

**Agent 2: risk-assessor**
- Prompt: "Analyze this decision from a critical perspective: [DECISION]. Identify risks, challenges, failure patterns, costs, and mitigation strategies. Be thorough but constructive."

### Step 3: Wait for Completion
Both agents work independently in parallel. Wait for both to complete.

### Step 4: Synthesize Balanced Recommendation

Combine insights from both agents:

1. **Present both perspectives** clearly labeled
2. **Identify tensions** between opportunity and risk
3. **Make balanced recommendation** based on:
   - Net value (benefits vs costs)
   - Risk tolerance appropriate for context
   - Feasibility of mitigations
   - Strategic alignment

4. **Suggest actionable path** forward:
   - "Proceed" with specific actions
   - "Proceed with caution" with mitigations
   - "Defer" until conditions change
   - "Avoid" if risks outweigh benefits

### Output Format

```markdown
# Decision Analysis: [DECISION]

## 🟢 Opportunities & Benefits
[Output from opportunity-finder agent]

## 🔴 Risks & Challenges
[Output from risk-assessor agent]

## ⚖️ Balanced Recommendation

**Verdict**: [Proceed / Proceed with Caution / Defer / Avoid]

**Reasoning**:
[Synthesize both perspectives, explain verdict]

**Key Tensions**:
- [Opportunity vs Risk tension 1]
- [Opportunity vs Risk tension 2]

**Suggested Path Forward**:
1. [Concrete action step 1]
2. [Concrete action step 2]
3. [Concrete action step 3]

**Timeline**: [Realistic timeframe]
**Prerequisites**: [What needs to be in place first]
```

## Best Practices

- **Neutrality**: Don't favor one perspective over the other
- **Context matters**: Consider company size, risk tolerance, resources
- **Actionable**: Always provide concrete next steps
- **Realistic**: Avoid both over-optimism and over-pessimism
- **Time-bound**: Include timeline estimates

## Example Invocations

User: "Should we adopt TypeScript for our JavaScript codebase?"
→ Spawn opportunity-finder + risk-assessor → Synthesize

User: "Evaluate moving from REST to GraphQL"
→ Spawn opportunity-finder + risk-assessor → Synthesize

User: "Is it worth investing in automated testing?"
→ Spawn opportunity-finder + risk-assessor → Synthesize
