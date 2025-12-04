# Compound Request Handling Workflow
## Disambiguating Research and Planning Action Verbs

This workflow documents the detection logic and user clarification process for requests that contain trigger keywords for both research and planning skills simultaneously.

---

## CRITICAL: Compound Request Handling

### What is a Compound Request?

A user request that triggers MULTIPLE skills simultaneously because it contains action verbs for both research AND planning.

**Example**: "Search for notification systems and build it"
- "Search" triggers: multi-agent-researcher (research action)
- "build" triggers: spec-workflow-orchestrator (planning action)
- Result: COMPOUND REQUEST → needs user clarification

### How Detection Works

The `user-prompt-submit` hook analyzes requests using two methods:

#### 1. Signal Strength Analysis
Determines if a keyword is used as an ACTION (verb) or SUBJECT (noun):

| Signal Type | Criteria | Interpretation |
|-------------|----------|----------------|
| **Strong** | Intent pattern matched | Keyword is ACTION verb |
| **Medium** | 3+ keywords, no pattern | Uncertain |
| **Weak** | 1-2 keywords, no pattern | Keyword is likely SUBJECT |
| **None** | No matches | Skill not triggered |

#### 2. Compound Pattern Matching
Checks against known TRUE and FALSE compound patterns:

- **TRUE Compound**: `"research X AND build Y"` - both are actions
- **FALSE Compound**: `"build a search feature"` - search is subject

### Decision Matrix

| Research Signal | Planning Signal | Compound Type | Result |
|-----------------|-----------------|---------------|--------|
| Strong | Strong | TRUE compound | **ASK USER** |
| Strong | Strong | FALSE compound | Primary skill (from pattern) |
| Strong | Weak/Medium | Any | Research only |
| Weak/Medium | Strong | Any | Planning only |
| Weak | Weak | Any | **ASK USER** (safe default) |

### Examples

| Prompt | Research | Planning | Result |
|--------|----------|----------|--------|
| "Search for notification systems and build it" | STRONG | STRONG | **ASK USER** |
| "Build a search feature" | WEAK | STRONG | Planning only |
| "Research build tools" | STRONG | WEAK | Research only |
| "Hire a researcher" | NONE | NONE | No skill |
| "Don't research, just build it" | NONE (negated) | STRONG | Planning only |
| "Build a search and analysis tool" | WEAK | STRONG | Planning only (compound noun) |

### When You See "COMPOUND REQUEST DETECTED"

This message from the user-prompt-submit hook means BOTH keywords are detected as ACTION verbs.

**YOU MUST:**
1. Use AskUserQuestion tool with the standard options
2. Wait for user response
3. Execute ONLY the chosen skill(s)

**YOU MUST NOT:**
- Invoke any skill before user responds
- Assume you know what user wants
- Skip the clarification step

### AskUserQuestion Template

```json
{
  "questions": [{
    "question": "This request involves both research and planning. How would you like to proceed?",
    "header": "Workflow",
    "multiSelect": false,
    "options": [
      {"label": "Research → Plan", "description": "Research first, then I'll ask you to proceed with planning"},
      {"label": "Research only", "description": "Just investigate and report findings"},
      {"label": "Plan only", "description": "Create specifications using existing knowledge"},
      {"label": "Both sequentially", "description": "Research first, then plan (separate workflows, no data sharing)"}
    ]
  }]
}
```

### Actions After User Responds

| User Choice | Claude Action |
|-------------|---------------|
| **Research → Plan** | Invoke research skill, wait for completion, tell user "Reply 'proceed with planning' when ready", wait for user, then invoke planning skill |
| **Research only** | Invoke research skill, deliver report, done |
| **Plan only** | Invoke planning skill, deliver specs, done |
| **Both sequentially** | Invoke research skill, deliver report, immediately invoke planning skill (no wait), deliver specs |

### IMPORTANT: "Research → Plan" Design

When user selects "Research → Plan", skills run sequentially with manual continuation by design.

**Why this design:**
- Skills run in separate agent contexts (research skill → planning skill)
- No automatic data passing between skill contexts
- User retains control over the workflow transition

**What actually happens:**
1. Research skill completes and produces report
2. User must **manually request** planning in a follow-up message
3. Planning skill then runs using research outputs as context

**Claude should inform user:**
> "I'll start with the research phase. Once complete, please ask me to proceed with planning, and I'll use the research findings to inform the specifications."
