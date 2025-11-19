# Spec Workflow Orchestrator - Reference Guide

## Overview

The spec-workflow-orchestrator skill orchestrates a comprehensive planning workflow from ideation to development-ready specifications using three specialized sequential agents with quality gate validation.

## Architecture

### Orchestration Flow
1. **Query Analysis**: Analyze user request to determine planning scope
2. **Requirements Phase**: Spawn spec-analyst agent for requirements gathering
3. **Architecture Phase**: Spawn spec-architect agent for system design + ADRs
4. **Planning Phase**: Spawn spec-planner agent for task breakdown
5. **Quality Gate**: Validate all deliverables against 85% threshold
6. **Iteration**: Re-spawn agents if quality gate fails (max 3 attempts)

### Agent Roles

#### spec-analyst.md
- **Location**: `.claude/agents/spec-analyst.md`
- **Tools**: Read, Write, Glob, Grep, WebFetch, TodoWrite
- **Purpose**: Requirements analysis and project scoping
- **Output**: `docs/planning/requirements.md` (~800-1,500 lines)
- **Deliverables**:
  - Executive summary
  - Functional requirements (prioritized with IDs)
  - Non-functional requirements (performance, security, scalability)
  - User stories with acceptance criteria (EARS format)
  - Stakeholder analysis
  - Assumptions and constraints
  - Success metrics

#### spec-architect.md
- **Location**: `.claude/agents/spec-architect.md`
- **Tools**: Read, Write, Glob, Grep, WebFetch, TodoWrite
- **Purpose**: System architecture design and technical decisions
- **Output**:
  - `docs/planning/architecture.md` (~1,000-2,000 lines)
  - `docs/adrs/*.md` (Architecture Decision Records, 3-7 files)
- **Deliverables**:
  - High-level system architecture diagram (Mermaid)
  - Technology stack with justifications
  - Component design and interactions
  - Data models and API specifications
  - Security architecture
  - Performance and scalability considerations
  - ADRs documenting key decisions

#### spec-planner.md
- **Location**: `.claude/agents/spec-planner.md`
- **Tools**: Read, Write, Glob, Grep, TodoWrite
- **Purpose**: Implementation planning and task breakdown
- **Output**: `docs/planning/tasks.md` (~500-800 lines)
- **Deliverables**:
  - Task breakdown (atomic, implementable)
  - Phase organization (logical grouping)
  - Dependencies mapping (blocking relationships)
  - Effort estimates (complexity, not hours)
  - Risk assessment with mitigations
  - Testing strategy
  - Rollout plan

## Skill Configuration

### Frontmatter (SKILL.md)
```yaml
---
name: spec-workflow-orchestrator
description: Orchestrates 3-phase planning workflow from ideation to dev-ready specs
allowed-tools: Read, Glob, Grep, TodoWrite, Task, AskUserQuestion
---
```

**Note**: Write tool **EXCLUDED** to enforce agent delegation for all document generation.

### Trigger Keywords (90+ keywords)
- **Planning Actions**: "plan", "design", "architect", "blueprint", "outline"
- **Build/Create**: "build", "create", "develop", "implement", "construct"
- **Specifications**: "specs", "specifications", "requirements", "acceptance criteria"
- **Architecture**: "architecture", "system design", "technical design"
- **Features**: "features", "feature list", "capabilities", "MVP"
- **Conversational**: "what should we build", "how should we structure", "need specs for"

See `.claude/skills/skill-rules.json` for complete trigger configuration.

## File Organization

### Planning Documents Directory
**Path**: `docs/planning/`
- Created fresh for each planning session
- Contains: `requirements.md`, `architecture.md`, `tasks.md`
- NOT gitignored (planning documents are development artifacts)

### Architecture Decision Records
**Path**: `docs/adrs/`
- Numbered format: `001-decision-title.md`, `002-another-decision.md`
- Follows ADR template (Context, Decision, Consequences)
- Committed to repository (part of project documentation)

## Quality Gate System

### Threshold
**85% (85 points out of 100)**
- Ensures production-quality specifications
- Prevents undercooked or incomplete planning
- Catches issues before development starts

### Scoring Criteria (4 criteria × 25 points each)

#### 1. Completeness (25 points)
- All required sections present
- No "TODO" or "[To be filled]" placeholders
- Edge cases and error scenarios documented
- Success metrics defined

#### 2. Technical Depth (25 points)
- Specific technology choices with justifications
- Concrete implementation details
- Performance/security considerations quantified
- Dependencies and constraints identified

#### 3. Actionability (25 points)
- Requirements testable with clear acceptance criteria
- Architecture decisions backed by ADRs
- Tasks atomic and implementable
- Clear dependencies and sequencing

#### 4. Clarity (25 points)
- Well-structured with clear sections
- Technical terms defined
- Examples and diagrams included
- Consistent formatting and style

### Validation Process

**For Each Deliverable**:
1. Orchestrator reads output file
2. Applies scoring rubric across 4 criteria
3. Calculates total score (0-100)
4. If score < 85: Provide detailed feedback and re-spawn agent
5. If score ≥ 85: Accept and proceed to next phase
6. Max 3 attempts per agent before escalation

## Workflow Steps

### Step 1: Query Analysis
**Orchestrator analyzes**:
- Is this a planning request? (check trigger keywords)
- What's the scope? (new feature, system, architecture change)
- What constraints exist? (technology, timeline, team)
- What deliverables are needed? (requirements, architecture, tasks)

### Step 2: Spawn spec-analyst Agent
```markdown
Use Task tool with:
- subagent_type: spec-analyst
- prompt: "Analyze requirements for [PROJECT]. Generate comprehensive requirements.md with:
  - Executive Summary
  - Functional Requirements (prioritized)
  - Non-Functional Requirements
  - User Stories with Acceptance Criteria
  - Stakeholder Analysis
  - Assumptions and Constraints
  - Success Metrics"
```

**Quality Gate**: Score ≥ 85% on requirements.md
- If fail: Provide feedback and retry (max 3 attempts)
- If pass: Proceed to architecture phase

### Step 3: Spawn spec-architect Agent
```markdown
Use Task tool with:
- subagent_type: spec-architect
- prompt: "Design system architecture for [PROJECT] based on requirements at docs/planning/requirements.md. Generate:
  - architecture.md with system design, tech stack, component interactions
  - docs/adrs/*.md with Architecture Decision Records
  - API specifications and data models
  - Security, performance, and scalability considerations"
```

**Quality Gate**: Score ≥ 85% on architecture.md + ADRs
- If fail: Provide feedback and retry
- If pass: Proceed to planning phase

### Step 4: Spawn spec-planner Agent
```markdown
Use Task tool with:
- subagent_type: spec-planner
- prompt: "Create implementation plan for [PROJECT] based on:
  - Requirements: docs/planning/requirements.md
  - Architecture: docs/planning/architecture.md
  Generate tasks.md with:
  - Task breakdown (atomic, implementable)
  - Phase organization
  - Dependencies mapping
  - Effort estimates
  - Risk assessment
  - Testing strategy"
```

**Quality Gate**: Score ≥ 85% on tasks.md
- If fail: Provide feedback and retry
- If pass: Planning complete!

### Step 5: Deliverables Summary
**Orchestrator reads all outputs and provides**:
- Summary of key requirements
- Architecture highlights
- Number of tasks and phases
- Risk assessment overview
- Next steps for implementation

## Common Patterns

### New Feature Development
**Example**: "Plan a user authentication system"
- Requirements: Login, signup, password reset, 2FA, OAuth
- Architecture: JWT tokens, session management, auth service
- Tasks: 15-25 tasks across 4 phases (setup, core auth, OAuth, security hardening)

### System Refactoring
**Example**: "Refactor monolith to microservices"
- Requirements: Service boundaries, data migration, backward compatibility
- Architecture: Service decomposition, API gateway, event bus
- Tasks: 30-50 tasks across 6 phases (planning, service extraction, data migration, testing, cutover)

### Infrastructure Changes
**Example**: "Migrate from on-prem to cloud"
- Requirements: Performance parity, cost constraints, security compliance
- Architecture: Cloud provider selection, network design, deployment strategy
- Tasks: 20-35 tasks across 5 phases (assessment, design, pilot, migration, optimization)

## Error Handling

### Agent Discovery Issues
- Verify agents exist: `ls .claude/agents/spec-*.md`
- Check frontmatter format (name, description, tools)
- Ensure agent names match Task tool `subagent_type` parameter

### Quality Gate Failures
**Symptom**: Agent output scores < 85%
**Common Causes**:
- Missing sections (incompleteness)
- Vague requirements (lack of technical depth)
- Untestable criteria (not actionable)
- Poor organization (clarity issues)

**Fix**: Orchestrator provides specific feedback, agent retries with improvements

### Output File Conflicts
**Symptom**: Previous planning docs exist in docs/planning/
**Fix**:
1. Ask user if should overwrite or use different directory
2. Archive old plans to `docs/planning/archive/{date}/`
3. Proceed with fresh planning session

## Best Practices

1. **Sequential Execution**: Always run spec-analyst → spec-architect → spec-planner (dependencies matter)
2. **Quality First**: Don't skip quality gates, even if user is impatient
3. **Comprehensive Scope**: Break large projects into phases, but plan comprehensively within scope
4. **ADR Documentation**: Every significant architecture decision should have an ADR
5. **Testable Requirements**: All requirements must have specific, measurable acceptance criteria
6. **Risk Awareness**: Identify and mitigate risks upfront during planning

## Troubleshooting

### "Agent type 'spec-analyst' not found"
**Cause**: Agent not in standard registry location
**Fix**: Verify agents are in `.claude/agents/`, NOT `.claude/skills/*/agents/`

### Requirements Too Vague
**Symptom**: Quality gate fails on "Technical Depth"
**Fix**: Re-spawn spec-analyst with feedback: "Add specific metrics, quantify performance requirements, define edge cases"

### Architecture Lacks Justification
**Symptom**: Quality gate fails on "Actionability"
**Fix**: Re-spawn spec-architect with feedback: "Create ADRs for technology choices, explain trade-offs, document alternatives considered"

### Tasks Not Atomic
**Symptom**: Quality gate fails on "Actionability"
**Fix**: Re-spawn spec-planner with feedback: "Break tasks into smaller units (1-2 days max), clarify dependencies, add acceptance criteria"

## Integration with Research Skill

For complex projects, use multi-agent-researcher BEFORE spec-workflow-orchestrator:

1. **Research Phase**: Investigate similar products, technologies, best practices
2. **Planning Phase**: Use research findings to inform requirements and architecture
3. **Development Phase**: Implement with research-backed decisions

**Example Workflow**:
```markdown
User: "Research task management app best practices"
→ multi-agent-researcher skill (research findings in files/reports/)

User: "Plan a task management app incorporating best practices from research"
→ spec-workflow-orchestrator skill (references research report)
→ spec-analyst: Extracts requirements from research
→ spec-architect: Chooses tech stack based on research
→ spec-planner: Creates tasks implementing researched patterns
```

## ADR Template

Architecture Decision Records follow this format:

```markdown
# ADR-001: [Decision Title]

**Status**: Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date**: YYYY-MM-DD
**Deciders**: [Who made this decision]

## Context
[What is the issue motivating this decision?]

## Decision
[What is the change we're making?]

## Consequences
**Positive**:
- [Good outcome 1]
- [Good outcome 2]

**Negative**:
- [Trade-off 1]
- [Trade-off 2]

## Alternatives Considered
1. **Alternative A**: [Pros/cons, why rejected]
2. **Alternative B**: [Pros/cons, why rejected]

## References
- [Link to related docs]
- [Related ADRs]
```

## Quality Metrics

### Successful Planning Session
- ✅ All 3 deliverables score ≥ 85%
- ✅ Requirements have specific acceptance criteria (no vague "should work well")
- ✅ Architecture has 3-7 ADRs documenting key decisions
- ✅ Tasks are atomic (1-2 days max), with clear dependencies
- ✅ Risk assessment identifies blockers with mitigations
- ✅ Total output: 2,500-4,000 lines across all documents

### Red Flags (Quality Issues)
- ❌ "TODO" or "[To be filled]" placeholders
- ❌ Vague requirements ("fast", "secure", "user-friendly")
- ❌ Technology choices without justification
- ❌ Tasks like "Implement feature X" (too broad)
- ❌ No error handling or edge cases documented
- ❌ Missing performance/security/scalability considerations

## Command Shortcuts

Use `/plan-feature` command for quick invocation:
```markdown
/plan-feature

[Edit template with your specific project details]
```

Use `/project-status` to check implementation plan progress:
```markdown
/project-status

Shows current phase, completed tasks, what's next
```
