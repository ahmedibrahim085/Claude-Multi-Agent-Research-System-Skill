---
name: spec-workflow-orchestrator
description: Orchestrate comprehensive planning phase from ideation to development-ready specifications using 4 specialized agents
allowed-tools: Task, Read, Glob, TodoWrite, Write, Edit
version: 1.0.0
---

# Spec Workflow Orchestrator

## Purpose

Transform ideas into development-ready specifications through:
1. Comprehensive planning with requirement analysis and architecture design
2. Quality-gated iterative refinement of specifications
3. Complete handoff documentation for development teams
4. Orchestration across planning phase with 4 specialized agents

## When to Use

Auto-invoke when user requests:
- **Planning**: "Plan [application]", "Design [system]", "Spec out [feature]", "Create requirements for [service]"
- **Architecture**: "Architecture for [project]", "Technical design for [application]", "Design specifications"
- **Requirements**: "Requirements for [project]", "Analyze requirements", "User stories for [feature]"
- **Pre-Development**: "Ready for development", "Spec-based planning", "Development specifications"

Do NOT invoke for:
- Actual code implementation (this skill stops at planning)
- Quick prototypes or experiments
- Single-file scripts
- Tasks that need immediate coding

## Orchestration Workflow

### Planning Phase (spec-planner → spec-analyst → spec-architect)

**Step 1: spec-orchestrator coordinates the planning workflow**

The orchestrator manages the sequential execution of planning agents and quality gates.

**Step 2: spec-planner - Initial Requirements**
- Gather initial requirements from user
- Define project scope and boundaries
- Identify stakeholders and constraints
- Output: Initial requirements document

**Step 3: spec-analyst - Detailed Analysis**
- Analyze requirements in depth
- Create user stories and acceptance criteria
- Identify edge cases and dependencies
- Output: Detailed requirements and user stories

**Step 4: spec-architect - Technical Design**
- Design system architecture
- Make technology stack decisions
- Document ADRs (Architecture Decision Records)
- Create technical specifications
- Output: Architecture documentation and ADRs

**Step 5: Quality Gate Check (85% threshold)**
- Orchestrator validates planning completeness
- Maximum 3 iterations if threshold not met
- Output: Development-ready specifications

---

## Agent Roles

**Planning Phase (4 agents)**:
- **spec-orchestrator**: Coordinates planning workflow and quality gates
- **spec-planner**: Initial requirement gathering and scope definition
- **spec-analyst**: Detailed requirement analysis and user story creation
- **spec-architect**: Technical design and architecture decisions

## Quality Gates

**Planning Gate** (85% threshold):
- Requirements completeness
- Architecture soundness
- Feasibility assessment
- Documentation quality
- Handoff readiness

**Maximum Iterations**: 3 for planning phase

---

## File Organization

- `docs/planning/*.md`: Planning phase outputs (requirements, architecture)
- `docs/adrs/*.md`: Architecture Decision Records
- Handoff ready for development team to implement

---

## Best Practices

**TODO: Best practices to be added in Phase 3**

---

## Examples

**TODO: Examples to be added in Phase 3**

---

**Note**: This skill focuses on planning phase only. It produces development-ready specifications but does not implement code, tests, or validation.
