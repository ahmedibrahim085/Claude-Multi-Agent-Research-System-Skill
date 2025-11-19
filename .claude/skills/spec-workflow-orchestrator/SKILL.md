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

### Planning Phase (spec-analyst → spec-architect → spec-planner)

The orchestrator manages sequential execution of three specialized agents with quality gate validation.

---

**Step 1: Query Analysis**

Parse user's planning request and validate suitability:
- Identify project scope, constraints, and stakeholders
- Confirm request is suitable for planning workflow (not immediate coding)
- Determine if sufficient information provided (or elicit more details)
- Output: Planning scope definition ready for spec-analyst

---

**Step 2: Spawn spec-analyst Agent**

Use Task tool to spawn requirements analysis agent:

```
Agent: spec-analyst (from .claude/skills/spec-workflow-orchestrator/agents/spec-analyst.md)

Prompt: "Analyze requirements for [PROJECT_NAME]. Generate comprehensive requirements.md with:
- Executive Summary (project goals and scope)
- Functional Requirements (prioritized with IDs: FR1, FR2, etc.)
- Non-Functional Requirements (performance, security, scalability with metrics)
- User Stories with Acceptance Criteria (measurable criteria for each story)
- Stakeholder Analysis (identify all stakeholder groups and their needs)
- Assumptions and Constraints (technical, business, timeline)
- Success Metrics (how to measure project success)

Save to: docs/planning/requirements.md"

Wait for completion → Read output: docs/planning/requirements.md
```

**Expected Output**: Comprehensive requirements document (typically 800-1,500 lines)

---

**Step 3: Spawn spec-architect Agent**

Use Task tool to spawn architecture design agent:

```
Agent: spec-architect (from .claude/skills/spec-workflow-orchestrator/agents/spec-architect.md)

Prompt: "Design system architecture for [PROJECT_NAME] based on requirements at docs/planning/requirements.md.

Generate:
1. architecture.md with:
   - Executive Summary
   - Technology Stack (with justification for each choice)
   - System Components (with interaction diagrams)
   - API Specifications (endpoints, contracts, data models)
   - Security Considerations (authentication, authorization, data protection)
   - Performance & Scalability (caching, load balancing, horizontal scaling)
   - Deployment Architecture

2. docs/adrs/*.md with Architecture Decision Records for key decisions:
   - ADR format: Status, Context, Decision, Rationale, Consequences, Alternatives
   - Create separate ADR for: technology stack, database choice, real-time architecture, etc.

Save to: docs/planning/architecture.md, docs/adrs/*.md"

Wait for completion → Read outputs: docs/planning/architecture.md, docs/adrs/*.md
```

**Expected Output**: Architecture document (600-1,000 lines) + 3-5 ADRs (150-250 lines each)

---

**Step 4: Spawn spec-planner Agent**

Use Task tool to spawn implementation planning agent:

```
Agent: spec-planner (from .claude/skills/spec-workflow-orchestrator/agents/spec-planner.md)

Prompt: "Create implementation plan for [PROJECT_NAME] based on:
- Requirements: docs/planning/requirements.md
- Architecture: docs/planning/architecture.md

Generate tasks.md with:
1. Overview (total tasks, estimated effort, critical path, parallel streams)
2. Task Breakdown by Phase:
   - Each task with: ID, complexity, effort estimate, dependencies, description
   - Acceptance criteria for each task (concrete, measurable)
   - Tasks should be atomic and implementable (1-8 hours each)
3. Risk Assessment:
   - Technical risks with severity, probability, impact
   - Mitigation strategies for each risk
4. Testing Strategy:
   - Unit test coverage targets
   - Integration test scenarios
   - End-to-end test requirements

Save to: docs/planning/tasks.md"

Wait for completion → Read output: docs/planning/tasks.md
```

**Expected Output**: Task breakdown document (500-800 lines with 15-30 tasks)

---

**Step 5: Quality Gate Validation**

Orchestrator validates planning completeness using checklist (see Quality Gates section):

**Validation Process**:
1. Read all planning artifacts (requirements.md, architecture.md, tasks.md, adrs/*.md)
2. Score against 6-category checklist (100 points total)
3. Calculate total score: Sum of all category points / 100
4. Compare to threshold: ≥ 85% to pass

**Decision**:
- If score ≥ 85%: Proceed to Step 7 (Deliverable Handoff)
- If score < 85%: Proceed to Step 6 (Iteration Loop)

---

**Step 6: Iteration Loop (Max 3 Iterations)**

When quality gate fails, provide targeted feedback and re-spawn relevant agent:

**Feedback Generation Process**:
1. Identify which checklist categories failed (< expected points)
2. Determine root cause (requirements gap, architecture issue, tasks unclear)
3. Generate specific, actionable feedback listing gaps
4. Re-spawn agent with previous output + feedback + gap list

**Example Feedback for spec-analyst**:
```
"Requirements analysis incomplete. Score: 68/100

Gaps identified:
- Non-functional requirements missing performance metrics (0/5 points)
  → Add specific metrics: API response time, throughput, concurrent users
- User stories lack measurable acceptance criteria (2/5 points)
  → Provide concrete, testable criteria for each story
- Stakeholder analysis incomplete (2/5 points)
  → Identify admin users, end users, external integrations

Please regenerate requirements.md addressing these specific gaps."
```

**Re-spawn agent** with feedback → Wait for revised output → Return to Step 5 (Quality Gate)

**Iteration Limit Enforcement**:
- Track iteration count per agent (max 3 total iterations)
- If iterations = 3 and score still < 85%: Escalate to user with current artifacts
- User decides: accept current quality OR provide manual guidance

---

**Step 7: Deliverable Handoff**

Generate planning summary and return artifacts to user:

**Planning Summary Includes**:
- Project scope and objectives (from requirements.md)
- Key architectural decisions (from ADRs)
- Implementation roadmap (from tasks.md with effort estimates)
- Technical risks and mitigation strategies (from tasks.md)
- Quality gate score (e.g., "92/100 - Planning phase complete")
- Next steps for development team

**Deliverables Returned**:
- 📄 docs/planning/requirements.md
- 📄 docs/planning/architecture.md
- 📄 docs/planning/tasks.md
- 📄 docs/adrs/*.md (3-5 Architecture Decision Records)

**Status**: "✅ Planning phase complete. Development-ready specifications available."

**Handoff**: Development team can begin implementation using planning artifacts as source of truth

---

## Agent Roles

**Planning Phase (4 agents)**:
- **spec-orchestrator**: Coordinates planning workflow and quality gates
- **spec-planner**: Initial requirement gathering and scope definition
- **spec-analyst**: Detailed requirement analysis and user story creation
- **spec-architect**: Technical design and architecture decisions

## Quality Gates

### Planning Gate (85% Threshold)

**Purpose**: Validate planning completeness before handoff to development team

**Validation Checklist** (100 points total):

#### 1. Requirements Completeness (25 points)
- ✅ All functional requirements documented with IDs (10 pts)
- ✅ Non-functional requirements specified with metrics (5 pts)
- ✅ User stories with measurable acceptance criteria (5 pts)
- ✅ Stakeholder needs addressed and documented (5 pts)

#### 2. Architecture Soundness (25 points)
- ✅ System design addresses all requirements (10 pts)
- ✅ Technology stack justified with rationale (5 pts)
- ✅ Scalability and performance considerations documented (5 pts)
- ✅ Security and compliance requirements addressed (5 pts)

#### 3. Task Breakdown Quality (20 points)
- ✅ Tasks are atomic and implementable (1-8 hours each) (10 pts)
- ✅ Dependencies clearly identified with task IDs (5 pts)
- ✅ Effort estimates provided with complexity ratings (5 pts)

#### 4. Architecture Decision Records (10 points)
- ✅ Key decisions documented in ADRs (5 pts)
- ✅ Trade-offs and alternatives considered explicitly (5 pts)

#### 5. Risk Management (10 points)
- ✅ Technical risks identified with severity/probability (5 pts)
- ✅ Mitigation strategies documented for each risk (5 pts)

#### 6. Handoff Readiness (10 points)
- ✅ Documentation clear and comprehensive (5 pts)
- ✅ Next steps explicitly defined for dev team (5 pts)

---

**Scoring Method**:
1. Sum all checklist points from 6 categories
2. Score = Total Points / 100
3. Threshold: ≥ 85% to pass quality gate

**Maximum Iterations**: 3 attempts per planning session

---

### Feedback Loop Process

**When Quality Gate Fails (Score < 85%)**:

#### Step 1: Failure Analysis

Categorize gaps by severity:
- **Critical** (0-50% score): Fundamental gaps requiring complete rework
- **Major** (51-74% score): Significant improvements needed
- **Minor** (75-84% score): Small refinements to reach threshold

#### Step 2: Root Cause Identification

Map failures to responsible agent:
- Requirements incomplete or unclear? → Re-spawn **spec-analyst**
- Architecture infeasible or under-specified? → Re-spawn **spec-architect**
- Tasks too vague or poorly estimated? → Re-spawn **spec-planner**
- Multiple issues? → Address in priority order (requirements first)

#### Step 3: Generate Specific Feedback

Create targeted feedback for agent re-spawning with:
- Current score and gap breakdown
- Specific items missing (reference checklist categories)
- Actionable improvements needed
- Concrete examples of what's expected

**Example Feedback Templates**:

**For spec-analyst (Requirements Gap)**:
```
"Requirements analysis incomplete. Score: 68/100

Gaps identified:
- Non-functional requirements missing performance metrics (0/5 points)
  → Add specific metrics: API response time < 200ms p95, throughput > 1000 req/s,
     concurrent users > 500
- User stories lack measurable acceptance criteria (2/5 points)
  → Provide concrete, testable criteria for each story
  → Example: 'AC1: User can create task within 2 seconds' (not 'AC1: Task creation works')
- Stakeholder analysis incomplete (2/5 points)
  → Identify: admin users, end users, API consumers, external integrations
  → Document needs and priorities for each stakeholder group

Please regenerate requirements.md addressing these specific gaps."
```

**For spec-architect (Architecture Gap)**:
```
"Architecture design incomplete. Score: 72/100

Gaps identified:
- Scalability not addressed (0/5 points)
  → Design for 10x growth: horizontal scaling strategy, database sharding plan
  → Address: load balancing, caching layers, CDN for static assets
- Security considerations incomplete (1/5 points)
  → Add: authentication mechanism (JWT/OAuth), authorization model (RBAC),
     data encryption (at rest and in transit), input validation strategy
- ADRs missing key decisions (2/5 points)
  → Create ADR for: database choice (SQL vs. NoSQL), real-time architecture
     (WebSockets vs. polling), deployment platform (cloud provider choice)
  → Format: Status, Context, Decision, Rationale, Consequences, Alternatives

Please regenerate architecture.md and adrs/ addressing these gaps."
```

**For spec-planner (Task Breakdown Gap)**:
```
"Task breakdown incomplete. Score: 76/100

Gaps identified:
- Tasks too large and not atomic (4/10 points)
  → Break down: 'Build authentication system' is too broad
  → Should be: 'T2.1: Create user registration API endpoint (4h)',
     'T2.2: Implement JWT token generation (3h)', etc.
- Dependencies not clearly identified (2/5 points)
  → Use task IDs: 'Dependencies: T1.3, T2.1' (not 'depends on auth')
  → Ensure topological order (no circular dependencies)
- Risk mitigation incomplete (3/5 points)
  → For each risk, provide concrete mitigation strategy
  → Example: 'Risk: WebSocket scaling' → 'Mitigation: Implement Redis adapter
     early in Phase 2, test with 1000 concurrent connections'

Please regenerate tasks.md addressing these gaps."
```

#### Step 4: Re-spawn Agent with Feedback

Execute re-spawning process:
1. Use Task tool to spawn same agent again
2. Provide prompt with:
   - Previous output file path (to build upon, not start from scratch)
   - Specific feedback with gap list
   - Target improvements needed to reach 85% threshold
3. Wait for revised output
4. Read revised artifact

**Example Re-spawn for spec-analyst**:
```
Agent: spec-analyst

Prompt: "Improve requirements.md based on feedback.

Previous version: docs/planning/requirements.md

Feedback:
[Insert feedback from Step 3]

Please revise requirements.md to address all identified gaps. Focus on:
1. Adding quantitative non-functional requirements
2. Providing measurable acceptance criteria for all user stories
3. Completing stakeholder analysis with needs documentation

Target: 85% quality gate score"
```

#### Step 5: Re-validate

Return to Step 5 of Orchestration Workflow (Quality Gate Validation):
1. Re-run quality gate checklist on revised artifacts
2. Calculate new score
3. Compare to previous score (expect improvement)
4. **Decision**:
   - If new score ≥ 85%: Proceed to next agent or Step 7 (Deliverable Handoff)
   - If new score < 85% AND iterations < 3: Repeat Step 6 (Feedback Loop)
   - If iterations = 3: Escalate to user with current artifacts

---

### Iteration Limit Enforcement

**Maximum 3 iterations per planning session** to prevent infinite loops:

- **Iteration 1**: Initial attempt (typically 60-75% score)
  - Agents work from user's initial request
  - Common gaps: vague requirements, missing NFRs, incomplete architecture

- **Iteration 2**: Refinement with feedback (typically 75-85% score)
  - Agents improve based on specific gap feedback
  - Focus on addressing major gaps from Iteration 1
  - Most planning sessions reach 85% threshold here

- **Iteration 3**: Final optimization (target 85%+ score)
  - Last chance to reach threshold
  - Address remaining minor gaps
  - If still < 85%: Escalation needed

**After 3 iterations, if score < 85%**:
1. Return current artifacts to user with status report:
   ```
   "Planning quality gate not reached after 3 iterations.

   Current score: 82/100

   Remaining gaps:
   - [List specific gaps still present]

   Artifacts available:
   - requirements.md (mostly complete, minor gaps)
   - architecture.md (complete)
   - tasks.md (needs minor refinement)

   Options:
   A) Accept current quality level and proceed to development
   B) Provide manual guidance to close remaining gaps
   C) Restart planning with clearer initial requirements"
   ```

2. User decides next action (orchestrator waits for user input)
3. Document lessons learned for process improvement:
   - What gaps were hardest to close?
   - What initial information would have helped?
   - Update agent prompts or checklist based on findings

---

## File Organization

- `docs/planning/*.md`: Planning phase outputs (requirements, architecture)
- `docs/adrs/*.md`: Architecture Decision Records
- Handoff ready for development team to implement

---

## Best Practices

### Planning Phase Principles

1. **Clear Phase Definition**
   - Planning phase has specific goal: Development-ready specifications
   - Success criteria: 85% quality gate score
   - Deliverables: requirements.md, architecture.md, tasks.md, adrs/*.md
   - Handoff point: Complete specifications ready for implementation team
   - Timeline: Typically 2-4 hours for small projects, 1-2 days for complex systems

2. **Quality-First Approach**
   - Never compromise on 85% threshold for handoff
   - Better to iterate 2-3 times than hand off incomplete planning
   - Each iteration should show measurable improvement (+10-15% score)
   - Quality gate ensures development team has what they need to succeed
   - Incomplete planning = expensive rework during development

3. **Sequential Execution**
   - Planning workflow is intentionally sequential (not parallel)
   - spec-analyst completes requirements BEFORE spec-architect begins architecture
   - spec-architect completes architecture BEFORE spec-planner begins tasks
   - **Reason**: Each agent builds on previous agent's output (dependencies)
   - **Exception**: spec-architect may create multiple ADRs in parallel

4. **Incremental Validation**
   - Validate planning artifacts at end of workflow (Step 5: Quality Gate)
   - Don't wait until all agents complete to find gaps
   - Quality gate provides concrete score (0-100) and specific feedback
   - Iterative refinement with max 3 attempts prevents infinite loops
   - Early validation catches issues before they compound

5. **Continuous Learning**
   - Document lessons learned from failed quality gates
   - Update checklist based on common gaps across projects
   - Refine agent prompts to improve initial quality (reduce iterations)
   - Share knowledge: What worked? What patterns emerged?
   - Process improvement: Evolve workflow based on evidence

---

### Planning Workflow Optimization

#### Preparation Phase (Before spawning agents)

**User Interaction**:
- Clarify project scope with user (what's in scope, what's out of scope)
- Identify known constraints (budget, timeline, technical stack requirements)
- Confirm stakeholders and success criteria (who decides if it's good?)
- Elicit domain knowledge (any existing systems, data, APIs to integrate?)

**Set Realistic Expectations**:
- Planning takes 2-4 hours for small projects (e.g., todo app)
- Complex systems may need 1-2 days (e.g., e-commerce platform)
- Quality gate may require 2-3 iterations (normal, not a failure)
- Development-ready ≠ perfect; specs will evolve during implementation

#### Execution Phase (During agent spawning)

**Provide Clear Prompts**:
- Include context from previous agents' outputs (file paths)
- Reference specific files: "Based on requirements.md, design architecture..."
- Specify expected output format and file locations
- Give concrete examples of what "good" looks like

**Allow Sufficient Time**:
- spec-analyst: 30-60 minutes for requirements analysis
- spec-architect: 45-90 minutes for architecture + ADRs
- spec-planner: 30-60 minutes for task breakdown
- Don't rush agents; thoughtful analysis takes time

**Monitor Progress**:
- Use TodoWrite tool to track agent spawning and completion
- Read agent outputs immediately after completion (verify before proceeding)
- Check for obvious gaps early (missing sections, incomplete analysis)
- Be prepared to provide additional context if agent asks questions

#### Validation Phase (Quality gate)

**Use Checklist Systematically**:
- Don't skip checklist items (even if you think they're minor)
- Score objectively using defined point values (not "feels complete")
- Document specific gaps for each failed category
- Prioritize critical gaps (0-point items) over minor improvements

**Provide Actionable Feedback**:
- Specific > vague: "Add API response time NFR" not "improve NFRs"
- Measurable targets: "85% test coverage" not "good test coverage"
- Concrete examples: Show what "measurable acceptance criteria" looks like
- Reference checklist categories: "NFR missing performance metrics (0/5 pts)"

**Track Iterations**:
- Iteration 1 score: Baseline (typically 60-75%)
- Iteration 2 score: Improvement (expect +10-15% increase)
- Iteration 3 score: Final (if needed, should reach 85%+)
- If no improvement between iterations: Feedback may be unclear, rephrase

**Enforce Max 3 Iterations**:
- Prevent infinite loops that waste time and resources
- After 3 attempts: Escalate to user with current state
- User decides: Accept current quality OR provide manual guidance
- Learn from 3-iteration failures: What went wrong? How to prevent?

#### Handoff Phase (After quality gate passes)

**Generate Executive Summary**:
- Project scope and key objectives (1-2 paragraphs)
- Major architectural decisions (from ADRs, summarized)
- Implementation roadmap (phases, estimated effort from tasks.md)
- Critical risks and mitigation strategies (top 3-5 risks)

**Highlight Key Artifacts**:
- requirements.md: Source of truth for what to build
- architecture.md: Source of truth for how to build
- tasks.md: Source of truth for implementation order and effort
- adrs/*.md: Source of truth for why decisions were made

**Set Clear Next Steps**:
- "Review planning artifacts (estimated 30-60 minutes)"
- "Set up development environment following architecture.md"
- "Implement tasks in priority order from tasks.md"
- "Reference ADRs when questions arise about design decisions"
- "Treat specs as living documents; update as implementation evolves"

---

### Common Planning Pitfalls (and How to Avoid)

❌ **Pitfall 1: Vague Requirements**

**Symptom**: Requirements say "should be fast", "must be secure", "needs to scale"

**Impact**: Architecture can't make concrete decisions, tasks can't be estimated

**Solution**: spec-analyst must quantify all non-functional requirements
- Performance: "API response time < 200ms p95, throughput > 1000 req/s"
- Security: "JWT authentication, HTTPS only, input sanitization for XSS/SQLi"
- Scalability: "Support 10,000 concurrent users, horizontal scaling with load balancer"

**Quality Gate Catches This**: "Non-functional requirements missing metrics (0/5 points)"

---

❌ **Pitfall 2: Over-Engineering Architecture**

**Symptom**: Architecture designed for 1M users when current need is 100 users

**Impact**: Increased complexity, longer development time, higher costs

**Solution**: spec-architect must align with actual requirements and constraints
- Design for current requirements + 10x growth (not 1000x)
- Use ADRs to justify complexity: "Why microservices vs. monolith?"
- Start simple, document how to scale later (evolutionary architecture)

**Quality Gate Catches This**: "Architecture doesn't justify complexity or align with requirements"

---

❌ **Pitfall 3: Tasks Too Large**

**Symptom**: Tasks like "Build authentication system" (days of work, unclear scope)

**Impact**: Hard to estimate, hard to track progress, hard to parallelize

**Solution**: spec-planner must break into atomic tasks (1-8 hours each)
- "T2.1: Create user registration API endpoint (4h)"
- "T2.2: Implement JWT token generation (3h)"
- "T2.3: Add authentication middleware for protected routes (2h)"
- Each task has concrete acceptance criteria and effort estimate

**Quality Gate Catches This**: "Tasks not atomic and implementable (< 10 points)"

---

❌ **Pitfall 4: Missing ADRs**

**Symptom**: Technology choices without documented rationale ("We'll use React")

**Impact**: Future developers don't understand why choices were made, can't evaluate alternatives

**Solution**: spec-architect must create ADR for key decisions
- What: Decision made ("Use PostgreSQL for data storage")
- Why: Rationale ("Relational data model, ACID guarantees, mature ecosystem")
- Trade-offs: Alternatives considered ("MongoDB: Flexible schema but weaker consistency")
- Format: Status, Context, Decision, Rationale, Consequences, Alternatives

**Quality Gate Catches This**: "Key decisions not documented in ADRs (< 5 points)"

---

❌ **Pitfall 5: No Risk Assessment**

**Symptom**: Plan assumes everything will work perfectly (no risk identification)

**Impact**: Surprises during implementation, missed dependencies, timeline delays

**Solution**: spec-planner must identify risks and mitigation strategies
- Risk: "WebSocket scaling for real-time features" (Medium severity, High probability)
- Mitigation: "Implement Redis adapter early (Phase 2), load test with 1000 concurrent connections"
- Risk: "Third-party API dependency" (High severity, Low probability)
- Mitigation: "Implement circuit breaker pattern, design fallback behavior"

**Quality Gate Catches This**: "Technical risks not identified (< 5 points)"

---

### Success Factors

✅ **1. Thorough Requirements Analysis**

**Invest Time Upfront**:
- spec-analyst phase is foundation for everything else
- Better requirements → better architecture → better tasks → faster development
- Don't rush to architecture before requirements are solid (resist temptation)

**Quantify Everything**:
- Functional requirements: Clear inputs, outputs, behaviors
- Non-functional requirements: Specific metrics (not "fast" but "< 200ms")
- User stories: Measurable acceptance criteria (not "works" but "completes in < 2s")

**Validate with Stakeholders**:
- Confirm understanding: "Did I capture this correctly?"
- Identify hidden requirements: "What about error handling? Notifications?"
- Prioritize ruthlessly: "What's must-have vs. nice-to-have?"

---

✅ **2. Justified Architecture Decisions**

**Document WHY (ADRs), not just WHAT**:
- Architecture documents describe the design (components, interactions, data flow)
- ADRs explain the reasoning (why this choice over alternatives)
- ADRs preserve institutional knowledge (future developers understand context)

**Consider Alternatives Explicitly**:
- Don't assume first solution is best (explore 2-3 options)
- Document trade-offs: Pros/cons of each alternative
- Make decision criteria clear: "We chose PostgreSQL because relational model matches domain and team has expertise"

**Architecture Should Be Traceable**:
- Every component should address specific requirements (traceability matrix)
- If architecture includes feature not in requirements: Add requirement OR remove feature
- Architecture is servant of requirements, not the other way around

---

✅ **3. Actionable Task Breakdown**

**Tasks Must Be Implementation-Ready**:
- Developer should be able to start immediately (no further decomposition needed)
- Clear inputs: What data/files/APIs are available?
- Clear outputs: What should be created? What does "done" look like?
- Clear acceptance criteria: How to verify task is complete?

**Include Effort Estimates**:
- Helps developers plan sprints and iterations
- Realistic estimates: 2-8 hours per task (don't over-optimize)
- Complexity ratings: Simple/Medium/Complex (informs who should do it)

**Identify Dependencies Explicitly**:
- Use task IDs: "Dependencies: T1.3, T2.1" (not vague "depends on auth")
- Topological order: Ensure no circular dependencies
- Critical path: Highlight tasks that block other tasks

---

✅ **4. Iterative Refinement**

**Embrace Quality Gate Feedback**:
- Failing quality gate is not a failure; it's the process working correctly
- Feedback identifies specific gaps (saves time vs. manual discovery)
- Each iteration should show measurable improvement (+10-15% score)

**Address Gaps Systematically**:
- Priority 1: Critical gaps (0-point items, fundamental issues)
- Priority 2: Major gaps (missing sections, incomplete analysis)
- Priority 3: Minor gaps (refinements to reach 85% threshold)

**Max 3 Iterations Keeps Process Bounded**:
- Iteration 1: Initial attempt (learn the domain)
- Iteration 2: Refinement (address major gaps)
- Iteration 3: Final optimization (polish to 85%+)
- After 3: Escalate to user (process should work in 3 iterations)

---

✅ **5. Clear Handoff Documentation**

**Development Team Should Understand**:
- **Scope**: What are we building? What's in/out of scope?
- **Architecture**: How should it be built? What technologies? What patterns?
- **Roadmap**: What order to implement? What's the critical path?
- **Risks**: What might go wrong? What's the mitigation plan?
- **Success Criteria**: How do we know when it's done? What metrics?

**Planning Artifacts Are Living Documents**:
- Specs will evolve during implementation (new insights, changed requirements)
- Architecture may be adjusted (technical discoveries, constraints)
- Tasks will be added/modified (as implementation progresses)
- Planning phase creates starting point, not immutable contract

**Handoff Includes Next Steps**:
- Concrete actions: "Review docs (30 min) → Set up environment → Start Task 1.1"
- Timeline expectations: "Estimated 12-15 person-days for implementation"
- Communication plan: "Daily standups, reference ADRs for design questions"

---

## Examples

### Example: Planning a Task Management Web Application

**User Request**: "Plan a task management web application with user authentication, real-time updates, and mobile responsiveness"

This example demonstrates the complete planning workflow from query analysis to deliverable handoff.

---

#### Step 1: Query Analysis

**Scope Identified**:
- Web application (not mobile native)
- User authentication (registration, login, JWT)
- Real-time updates (WebSocket or similar)
- Mobile responsive (not separate mobile app)

**Constraints**: Not specified (assume standard web stack)

**Stakeholders**: End users (task managers), development team

**Suitability Check**: ✅ Clear scope, well-defined domain, suitable for planning workflow

---

#### Step 2: spec-analyst Output

**Generated File**: `docs/planning/requirements.md` (abbreviated example)

```markdown
# Task Management Application - Requirements

## Executive Summary
A web-based task management system enabling users to create, organize, and track
tasks with real-time collaboration features and mobile accessibility.

## Functional Requirements

### FR1: User Management (Priority: High)
- FR1.1: User registration with email/password
- FR1.2: Secure authentication (JWT-based)
- FR1.3: User profile management
- FR1.4: Password reset functionality

### FR2: Task Management (Priority: High)
- FR2.1: Create tasks with title, description, due date, priority
- FR2.2: Update task status (Todo, In Progress, Done)
- FR2.3: Delete tasks
- FR2.4: Organize tasks in projects/categories

### FR3: Real-Time Updates (Priority: Medium)
- FR3.1: WebSocket connection for live updates
- FR3.2: Instant task status synchronization across devices
- FR3.3: Online/offline user presence indicators

### FR4: Mobile Responsiveness (Priority: High)
- FR4.1: Responsive design for mobile, tablet, desktop
- FR4.2: Touch-optimized interactions
- FR4.3: Progressive Web App (PWA) support

## Non-Functional Requirements

### NFR1: Performance
- API response time < 200ms (p95)
- Real-time update latency < 100ms
- Support 1,000 concurrent users

### NFR2: Security
- HTTPS for all communications
- JWT tokens with 1-hour expiration
- Input validation and sanitization
- SQL injection prevention

### NFR3: Scalability
- Horizontal scaling capability
- Database connection pooling
- Stateless API design

## User Stories

**US1**: As a user, I want to create tasks so that I can track my work.
- AC1: User can create task with title (required) and description (optional)
- AC2: Task is saved and appears in task list immediately
- AC3: Task creation fails gracefully with error message if title is empty

**US2**: As a user, I want to see real-time updates when my team changes tasks.
- AC1: When another user updates a task, my view updates within 2 seconds
- AC2: Update animation shows which task changed
- AC3: Connection loss shows offline indicator and queues updates
```

**Initial Quality Check**: Requirements document is comprehensive (estimated 90/100)

---

#### Step 3: spec-architect Output

**Generated Files**:
- `docs/planning/architecture.md`
- `docs/adrs/001-technology-stack.md`
- `docs/adrs/002-real-time-architecture.md`

**architecture.md** (abbreviated):
```markdown
# System Architecture

## Technology Stack
- **Frontend**: React 18 + TypeScript + Vite
- **Backend**: Node.js + Express + TypeScript
- **Database**: PostgreSQL 15
- **Real-Time**: Socket.io
- **Authentication**: JWT + bcrypt
- **Hosting**: Vercel (frontend) + Railway (backend + database)

## System Components

### Frontend Application
- React SPA with routing (React Router v6)
- State management: React Query + Context API
- UI components: Tailwind CSS + Shadcn/ui
- Real-time: Socket.io client

### Backend API
- RESTful API for CRUD operations
- WebSocket server for real-time updates
- JWT middleware for authentication
- PostgreSQL connection pool

### Database Schema
- users (id, email, password_hash, created_at)
- tasks (id, user_id, title, description, status, due_date, priority, created_at, updated_at)
- projects (id, name, user_id)
- Indexes on user_id, status, due_date

## API Specification

### REST Endpoints
- POST /api/auth/register - Create new user
- POST /api/auth/login - Authenticate user (returns JWT)
- GET /api/tasks - List user's tasks (with filtering)
- POST /api/tasks - Create new task
- PATCH /api/tasks/:id - Update task
- DELETE /api/tasks/:id - Delete task

### WebSocket Events
- connection, task:created, task:updated, task:deleted, disconnect

## Security
- HTTPS enforced in production
- JWT tokens in httpOnly cookies
- CORS configured for frontend origin
- Rate limiting: 100 requests/15min per IP
- Password hashing with bcrypt (cost factor 10)

## Performance & Scalability
- Database connection pooling (max 20 connections)
- Stateless API design allows horizontal scaling
- WebSocket sticky sessions or Redis adapter for multi-instance
```

**ADR 002-real-time-architecture.md**:
```markdown
# ADR 002: Real-Time Architecture with Socket.io

## Status: Accepted

## Context
Application requires real-time task updates across devices. Options:
1. Polling (HTTP requests every N seconds)
2. Server-Sent Events (SSE)
3. WebSockets (Socket.io)

## Decision
Use WebSockets with Socket.io library.

## Rationale
- Bi-directional communication (client ↔ server)
- Low latency < 100ms (meets NFR1)
- Socket.io benefits: automatic reconnection, fallback to polling
- Horizontal scaling possible with Redis adapter

## Consequences
- **Positive**: Real-time UX, efficient bandwidth usage
- **Negative**: Persistent connections (scalability consideration)
- **Mitigation**: Implement Redis adapter for multi-instance

## Alternatives Considered
- **Polling**: Simple but wasteful (60 req/min per user)
- **SSE**: Uni-directional only (server → client)
```

**Initial Quality Check**: Architecture document is solid (estimated 88/100)

---

#### Step 4: spec-planner Output

**Generated File**: `docs/planning/tasks.md` (abbreviated)

```markdown
# Implementation Tasks

## Overview
- **Total Tasks**: 24
- **Estimated Effort**: 12-15 person-days
- **Critical Path**: Authentication → Task CRUD → Real-time sync
- **Parallel Streams**: Frontend + Backend after API contract defined

## Phase 1: Project Setup (1 day)

### T1.1: Initialize Frontend Project
- Complexity: Low | Effort: 2h | Dependencies: None
- Create React + Vite + TypeScript project with Tailwind
- AC: npm create vite working, Tailwind configured, React Router setup

### T1.2: Initialize Backend Project
- Complexity: Low | Effort: 2h | Dependencies: None
- Create Node.js + Express + TypeScript with PostgreSQL connection
- AC: Express server starts, PostgreSQL connection successful

### T1.3: Database Schema Setup
- Complexity: Medium | Effort: 2h | Dependencies: T1.2
- Create SQL migration for users and tasks tables with indexes
- AC: Tables created, foreign keys set, indexes on user_id/status/due_date

## Phase 2: Authentication (2-3 days)

### T2.1: User Registration API
- Complexity: Medium | Effort: 4h | Dependencies: T1.3
- POST /api/auth/register with email validation and password hashing
- AC: Email validated, password hashed with bcrypt, user created, returns 201

### T2.2: User Login API
- Complexity: Medium | Effort: 4h | Dependencies: T2.1
- POST /api/auth/login with JWT generation
- AC: Password verified, JWT generated (1h expiration), returns token + user

### T2.3: JWT Authentication Middleware
- Complexity: Medium | Effort: 3h | Dependencies: T2.2
- Express middleware to verify JWT tokens on protected routes
- AC: JWT extracted from header, verified, user ID attached, returns 401 if invalid

[... 18 more tasks for Task CRUD, Real-time sync, Mobile UI ...]

## Risk Assessment

### Risk 1: Real-time scaling complexity
- Severity: Medium | Probability: High
- Impact: Multi-instance deployment requires Redis adapter
- Mitigation: Implement Redis adapter early (Phase 4)

### Risk 2: WebSocket connection stability
- Severity: Medium | Probability: Medium
- Impact: Users on unstable networks may lose updates
- Mitigation: Socket.io auto-reconnect + optimistic UI updates

### Risk 3: Database connection pool exhaustion
- Severity: High | Probability: Low
- Impact: API unresponsive under high load
- Mitigation: Max pool size 20, connection timeout, monitoring

## Testing Strategy
- Unit Tests: 80% coverage (auth logic, task CRUD, validation)
- Integration Tests: API endpoints with test database, WebSocket flows
- E2E Tests (Cypress): Registration, login, task creation, real-time sync
```

**Initial Quality Check**: Task breakdown is actionable (estimated 86/100)

---

#### Step 5: Quality Gate Validation

**Checklist Scoring**:

1. **Requirements Completeness**: 22/25 points
   - ✅ Functional requirements documented (10/10)
   - ✅ Non-functional requirements specified (5/5)
   - ✅ User stories with acceptance criteria (5/5)
   - ⚠️ Stakeholder needs addressed (2/5) - Missing admin user stories

2. **Architecture Soundness**: 23/25 points
   - ✅ System design addresses requirements (10/10)
   - ✅ Technology stack justified (5/5)
   - ✅ Scalability and performance considered (5/5)
   - ⚠️ Security and compliance (3/5) - Missing GDPR, detailed rate limiting

3. **Task Breakdown Quality**: 20/20 points
   - ✅ Tasks atomic and implementable (10/10)
   - ✅ Dependencies clearly identified (5/5)
   - ✅ Effort estimates provided (5/5)

4. **Architecture Decision Records**: 8/10 points
   - ✅ Key decisions documented in ADRs (4/5) - Missing database choice ADR
   - ✅ Trade-offs and alternatives considered (4/5)

5. **Risk Management**: 10/10 points
   - ✅ Technical risks identified (5/5)
   - ✅ Mitigation strategies documented (5/5)

6. **Handoff Readiness**: 9/10 points
   - ✅ Documentation clear and comprehensive (5/5)
   - ⚠️ Next steps explicitly defined (4/5) - Needs deployment guide

**Total Score**: 92/100 = **92%** ✅ **PASS** (threshold: 85%)

**Decision**: Proceed to Step 7 (Deliverable Handoff) - quality gate passed on first attempt

---

#### Step 6: Iteration Loop

**Not needed** - Score of 92% exceeds 85% threshold on initial attempt.

**Reason for high score**: Task management is a well-understood domain with clear requirements. User provided sufficient detail in initial request.

---

#### Step 7: Deliverable Handoff

**Planning Summary**:

✅ **Scope**: Task management web app with authentication, real-time updates, mobile responsiveness

✅ **Architecture**: React frontend + Node.js backend + PostgreSQL database + Socket.io for real-time

✅ **Key Architectural Decisions**:
- ADR 001: React + Node.js stack (familiar, mature ecosystem, TypeScript throughout)
- ADR 002: Socket.io for real-time (low latency, automatic reconnection, bi-directional)
- (Missing: Database choice ADR - noted in quality gate but acceptable at 92%)

✅ **Implementation Roadmap** (24 tasks, 12-15 person-days):
- Phase 1: Project setup (1 day)
- Phase 2: Authentication (2-3 days)
- Phase 3: Task CRUD operations (3-4 days)
- Phase 4: Real-time synchronization (3-4 days)
- Phase 5: Mobile responsive UI (2-3 days)

✅ **Risks Identified**:
- Real-time scaling → Mitigated with Redis adapter
- WebSocket stability → Mitigated with auto-reconnect
- Database pool exhaustion → Mitigated with connection limits

✅ **Next Steps for Development Team**:
1. Review planning artifacts (requirements, architecture, tasks) - 30-60 min
2. Set up development environment following T1.1, T1.2 instructions
3. Implement in priority order: authentication → CRUD → real-time
4. Reference ADRs when questions arise about design decisions
5. Use tasks.md as sprint backlog (24 tasks mapped to 5 phases)

**Deliverables Provided**:
- 📄 `docs/planning/requirements.md` (~1,200 lines)
- 📄 `docs/planning/architecture.md` (~800 lines)
- 📄 `docs/planning/tasks.md` (~600 lines with 24 tasks)
- 📄 `docs/adrs/001-technology-stack.md` (~150 lines)
- 📄 `docs/adrs/002-real-time-architecture.md` (~200 lines)

**Status**: ✅ **Planning phase complete. Development-ready specifications available.**

**Estimated Development Timeline**: 12-15 person-days (approximately 3 weeks for solo developer, 2 weeks for pair)

---

### Key Takeaways from This Example

1. **First-Attempt Success**: Quality gate passed with 92% score on initial attempt (no iterations needed)

2. **Sequential Dependencies**: Each agent built on previous agent's output:
   - spec-analyst produced requirements → spec-architect used them for architecture
   - spec-architect produced architecture → spec-planner used it for task breakdown

3. **Quality Gate Value**: Even with 92% passing score, quality gate identified minor gaps:
   - Missing admin user stories (stakeholder analysis)
   - Missing database choice ADR (architecture decisions)
   - Missing deployment guide (handoff readiness)
   - These could be addressed in future iteration if needed

4. **Realistic Outputs**: Agent outputs shown are representative of actual planning artifacts:
   - Requirements: Functional/non-functional requirements, user stories, acceptance criteria
   - Architecture: Technology stack justification, system components, API specs, security
   - Tasks: Atomic tasks (1-8h each), dependencies, effort estimates, risk assessment

5. **Development-Ready**: With these artifacts, a development team can immediately begin implementation:
   - Clear scope (what to build)
   - Technical design (how to build)
   - Implementation roadmap (order and effort)
   - Risk awareness (what might go wrong)

---

**Note**: This skill focuses on planning phase only. It produces development-ready specifications but does not implement code, tests, or validation.
