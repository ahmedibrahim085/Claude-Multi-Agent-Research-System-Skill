# Spec Workflow Orchestrator - Examples

## Example 1: Session Log Viewer (Web Application)

### User Request
> "Build a local web interface for session logs"

### Orchestrator Response

**Step 1: Query Analysis**
```markdown
Detected triggers: "build", "web interface"
Scope: New web application (multi-component system)
Constraints: Local-only, no cloud, file-based
Deliverables needed: Requirements, Architecture, Tasks
```

**Step 2: Spawn spec-analyst Agent**
```markdown
Task tool → subagent_type: spec-analyst
Context: "Local web interface to view 1,780+ Claude Code session logs with filtering, project grouping, timeline view"
```

**spec-analyst Output**: `docs/planning/requirements.md`
- Executive Summary: 3 paragraphs outlining vision
- Functional Requirements: 15 requirements (FR-001 through FR-015)
  - FR-001: File watching and auto-reload
  - FR-002: Filtering by project, date, keywords
  - FR-003: Project grouping and navigation
  - FR-004: Timeline view with zoom
  - FR-005: Tool call visualization
  - ... (10 more)
- Non-Functional Requirements: 8 requirements
  - NFR-001: Performance (handle 2,000+ logs, <2s initial load)
  - NFR-002: Security (local-only, no external requests)
  - NFR-003: Usability (keyboard shortcuts, responsive design)
  - ... (5 more)
- User Stories: 12 stories with EARS acceptance criteria
- Success Metrics: Load time, user satisfaction, feature coverage

**Quality Gate**: 88% (22/25 completeness, 23/25 depth, 22/25 actionable, 21/25 clarity)
✅ **PASS** - Proceed to architecture

**Step 3: Spawn spec-architect Agent**
```markdown
Task tool → subagent_type: spec-architect
Context: "Design architecture based on docs/planning/requirements.md"
```

**spec-architect Output**: `docs/planning/architecture.md` + 5 ADRs
- Architecture: Modern web stack (React, TypeScript, Node.js backend)
- Components:
  - Frontend: React with TanStack Query, Tailwind CSS
  - Backend: Express.js with file watchers (chokidar)
  - Data: File-based parsing (no database)
- System Diagram: Mermaid showing client-server-filesystem interactions
- API Design: 6 REST endpoints documented
- ADRs Created:
  - `docs/adrs/001-no-database-file-parsing.md`
  - `docs/adrs/002-react-tanstack-query.md`
  - `docs/adrs/003-websocket-file-updates.md`
  - `docs/adrs/004-local-only-no-cloud.md`
  - `docs/adrs/005-monorepo-structure.md`

**Quality Gate**: 91% (24/25 completeness, 23/25 depth, 22/25 actionable, 23/25 clarity)
✅ **PASS** - Proceed to planning

**Step 4: Spawn spec-planner Agent**
```markdown
Task tool → subagent_type: spec-planner
Context: "Create implementation plan based on requirements and architecture"
```

**spec-planner Output**: `docs/planning/tasks.md`
- Task Breakdown: 28 tasks organized into 5 phases
  - Phase 1: Project Setup (5 tasks)
  - Phase 2: Backend Foundation (7 tasks)
  - Phase 3: Frontend Core (8 tasks)
  - Phase 4: Advanced Features (5 tasks)
  - Phase 5: Polish & Testing (3 tasks)
- Dependencies: Clear blocking relationships mapped
- Effort Estimates: S/M/L complexity ratings
- Risk Assessment: 4 risks identified with mitigations
- Testing Strategy: Unit, integration, E2E test plan

**Quality Gate**: 89% (23/25 completeness, 22/25 depth, 23/25 actionable, 21/25 clarity)
✅ **PASS** - Planning complete!

**Step 5: Summary Delivered to User**
```markdown
Planning complete for Session Log Viewer! 📋

**Key Requirements** (15 functional, 8 non-functional):
- File watching with auto-reload
- Advanced filtering and search
- Project grouping and timeline view
- Performance: <2s load for 2,000+ logs

**Architecture Highlights**:
- React + TypeScript frontend with TanStack Query
- Express.js backend with WebSocket updates
- File-based parsing (no database needed)
- 5 ADRs document key technical decisions

**Implementation Plan**:
- 28 tasks across 5 phases
- Clear dependencies mapped
- Risk mitigations for file parsing performance

**Deliverables**:
- docs/planning/requirements.md (1,245 lines)
- docs/planning/architecture.md (1,680 lines)
- docs/planning/tasks.md (720 lines)
- docs/adrs/*.md (5 ADRs, ~800 lines total)

Ready to start development! 🚀
```

---

## Example 2: Authentication System (Feature Addition)

### User Request
> "Design a comprehensive user authentication system with OAuth support"

### Orchestrator Response

**Query Analysis**
- Scope: New feature (authentication subsystem)
- Complexity: High (security-critical, multiple auth methods)
- Deliverables: Requirements, architecture, implementation tasks

**spec-analyst Output**
- Functional Requirements: 22 requirements covering:
  - Email/password authentication
  - OAuth providers (Google, GitHub, Microsoft)
  - Password reset flow
  - 2FA/MFA support
  - Session management
  - Account linking
- Non-Functional Requirements:
  - NFR-001: Security (OWASP Top 10 compliance, bcrypt, JWT)
  - NFR-002: Performance (auth check <50ms)
  - NFR-003: Compliance (GDPR, data retention)
- User Stories: 18 stories for different auth scenarios
- Edge Cases: 12 error scenarios documented

**Quality Gate**: 87% ✅ PASS

**spec-architect Output**
- Architecture: Layered auth service
  - Auth Controller (routes)
  - Auth Service (business logic)
  - Token Manager (JWT handling)
  - OAuth Provider Adapters
  - User Repository (database)
- Technology Stack:
  - Passport.js for OAuth strategies
  - bcrypt for password hashing
  - JWT for stateless tokens
  - Redis for session storage
- Security Architecture:
  - Rate limiting on auth endpoints
  - CSRF protection
  - Secure cookie configuration
  - Token rotation strategy
- ADRs Created (7 ADRs):
  - 001-jwt-over-session-tokens.md
  - 002-passport-oauth-strategies.md
  - 003-bcrypt-password-hashing.md
  - 004-redis-session-storage.md
  - 005-token-rotation-strategy.md
  - 006-rate-limiting-auth-endpoints.md
  - 007-account-linking-approach.md

**Quality Gate**: 92% ✅ PASS

**spec-planner Output**
- Task Breakdown: 42 tasks in 6 phases
  - Phase 1: Foundation (database, user model) - 6 tasks
  - Phase 2: Core Auth (email/password) - 8 tasks
  - Phase 3: OAuth Integration - 10 tasks
  - Phase 4: Advanced Features (2FA, account linking) - 9 tasks
  - Phase 5: Security Hardening - 5 tasks
  - Phase 6: Testing & Docs - 4 tasks
- Critical Path: 18 blocking dependencies identified
- Risk Assessment: 6 risks (OAuth provider outages, token leakage, session fixation, etc.)
- Testing Strategy: Security testing emphasized (OWASP ZAP, penetration testing)

**Quality Gate**: 90% ✅ PASS

**Total Output**:
- requirements.md: 1,840 lines
- architecture.md: 2,350 lines
- tasks.md: 980 lines
- ADRs: 7 files, ~1,400 lines

---

## Example 3: Database Migration (Infrastructure Change)

### User Request
> "Plan migration from PostgreSQL to MongoDB for our document-heavy application"

### Orchestrator Response

**Query Analysis**
- Scope: Infrastructure change (database migration)
- Risk: HIGH (data migration, potential downtime)
- Deliverables: Requirements, architecture, migration plan

**spec-analyst Output**
- Functional Requirements:
  - FR-001: Zero data loss during migration
  - FR-002: Minimal downtime (<4 hours)
  - FR-003: Rollback capability if migration fails
  - FR-004: Data validation post-migration
  - ... (12 more)
- Non-Functional Requirements:
  - NFR-001: Performance parity or better
  - NFR-002: Cost constraints (stay within budget)
  - NFR-003: Team upskilling (MongoDB training)
- Migration Constraints:
  - Must complete within 2-week window
  - Cannot lose transactional data
  - Must maintain API compatibility
- Success Criteria: Zero data loss, <2% performance degradation, <4hr downtime

**Quality Gate**: 86% ✅ PASS

**spec-architect Output**
- Migration Architecture:
  - Dual-write phase (write to both databases)
  - Data synchronization layer
  - Schema transformation logic
  - Validation and reconciliation
- Technology Stack:
  - MongoDB 7.x with replica set
  - Mongoose ODM for Node.js
  - Change Data Capture (CDC) for sync
- Data Model Transformation:
  - Relational tables → MongoDB collections
  - Foreign keys → embedded documents or refs
  - Normalized data → denormalized for queries
- Rollback Strategy:
  - Keep PostgreSQL live during validation
  - Feature flags for cutover
  - Automated rollback procedure
- ADRs Created (6 ADRs):
  - 001-dual-write-migration-approach.md
  - 002-mongodb-over-dynamodb.md
  - 003-mongoose-odm-choice.md
  - 004-denormalization-strategy.md
  - 005-change-data-capture-sync.md
  - 006-rollback-mechanism.md

**Quality Gate**: 93% ✅ PASS

**spec-planner Output**
- Task Breakdown: 35 tasks in 7 phases
  - Phase 1: Preparation (setup, training) - 4 tasks
  - Phase 2: Schema Design (model transformation) - 6 tasks
  - Phase 3: Dual-Write Implementation - 7 tasks
  - Phase 4: Data Migration (historical data) - 6 tasks
  - Phase 5: Validation & Testing - 5 tasks
  - Phase 6: Cutover (switch to MongoDB) - 4 tasks
  - Phase 7: Cleanup (remove dual-write) - 3 tasks
- Dependencies: Critical path identified (21 days)
- Risk Assessment: 8 HIGH risks identified
  - Data inconsistency during dual-write
  - Migration script failures
  - Performance regression
  - Rollback complications
  - (Mitigations documented for each)
- Testing Strategy: Heavy emphasis on data validation, performance benchmarks

**Quality Gate**: 88% ✅ PASS

**Migration Timeline**: 6 weeks (2 weeks prep, 2 weeks dual-write, 1 week migration, 1 week validation)

---

## Example 4: Quality Gate Failure & Retry

### User Request
> "Plan a simple blog platform"

### Orchestrator Response

**spec-analyst Output** (Attempt 1)
```markdown
# Requirements

## Functional Requirements
- Users can create posts
- Users can comment
- Users can like posts

[Very brief, vague requirements - only 150 lines]
```

**Quality Gate**: 62% ❌ FAIL
- Completeness: 12/25 (missing NFRs, user stories, edge cases)
- Technical Depth: 15/25 (no specific metrics, vague descriptions)
- Actionability: 18/25 (not testable)
- Clarity: 17/25 (poor organization)

**Feedback to spec-analyst**:
```markdown
Requirements are too vague and incomplete. Please improve:

1. Add specific acceptance criteria (e.g., "Post creation completes in <200ms")
2. Document all user types (admin, author, reader, guest)
3. Add non-functional requirements (performance, security, scalability)
4. Include edge cases (spam prevention, moderation, deleted content)
5. Write user stories with EARS format acceptance criteria
6. Define success metrics (user engagement, performance targets)

Target length: 800-1,500 lines with comprehensive coverage.
```

**spec-analyst Output** (Attempt 2)
```markdown
# Requirements Document: Blog Platform

## Executive Summary
[Comprehensive 4-paragraph overview]

## Stakeholder Analysis
- Primary Users: Content authors (create/edit posts)
- Secondary Users: Readers (consume, comment, interact)
- Administrators: Moderation, user management

## Functional Requirements

### FR-001: Post Management
**Description**: Authors can create, edit, delete posts with rich text
**Priority**: High
**Acceptance Criteria**:
- WHEN author clicks "Create Post" THEN editor opens with rich text tools
- IF post saved THEN auto-save every 30 seconds
- FOR published posts VERIFY slug is unique and SEO-friendly
[... detailed criteria for 22 functional requirements]

## Non-Functional Requirements

### NFR-001: Performance
**Description**: System must handle 10,000 concurrent readers
**Metrics**:
- Page load time < 2 seconds (95th percentile)
- API response time < 200ms
- Database queries < 100ms
[... 8 comprehensive non-functional requirements]

## User Stories
[18 user stories with detailed EARS acceptance criteria]

## Edge Cases & Error Scenarios
[12 edge cases documented]

## Success Metrics
- User engagement: 30% of readers leave comments
- Performance: <2s page load maintained under load
- Content quality: <5% spam rate with moderation

[Total: 1,180 lines]
```

**Quality Gate**: 89% ✅ PASS (second attempt)
- Completeness: 24/25
- Technical Depth: 22/25
- Actionability: 22/25
- Clarity: 21/25

**Proceed to spec-architect** ✓

---

## Example 5: Small vs Large Scope

### Small Scope (Don't Use Skill)
**User Request**: "Add a dark mode toggle to the settings page"

**Orchestrator Decision**: ❌ DON'T invoke spec-workflow-orchestrator
**Rationale**:
- Trivial task (single component, simple CSS changes)
- 1-2 steps, no formal specs needed
- Use direct TodoWrite planning instead

---

### Large Scope (Use Skill)
**User Request**: "Architect a multi-tenant SaaS platform with user workspaces"

**Orchestrator Decision**: ✅ Invoke spec-workflow-orchestrator
**Rationale**:
- Complex system (multi-tenant, data isolation, subscriptions)
- Requires formal architecture (tenant isolation, database design)
- Many components and integrations
- Security and compliance critical

**Outcome**:
- requirements.md: 2,140 lines (28 functional, 12 non-functional requirements)
- architecture.md: 3,250 lines (tenant architecture, data isolation, multi-database strategy)
- tasks.md: 1,420 lines (68 tasks across 9 phases)
- 12 ADRs documenting tenant isolation, database per tenant vs shared, subscription billing, etc.

---

## Anti-Pattern Examples

### ❌ Wrong: Manual Planning
```markdown
User: "Plan a task management app"
Me: "Let me create a todo list..." [Uses TodoWrite directly]

# This bypasses the specialized planning agents!
```

### ✅ Correct: Skill Invocation
```markdown
User: "Plan a task management app"
Me: "I'll invoke spec-workflow-orchestrator skill..."
→ spec-analyst generates comprehensive requirements
→ spec-architect designs architecture with ADRs
→ spec-planner creates detailed task breakdown
```

---

### ❌ Wrong: Skipping Quality Gates
```markdown
spec-analyst output: 450 lines, many TODOs, vague requirements
Quality Gate: 72% FAIL
Me: "Good enough, let's proceed to architecture"

# This leads to incomplete specs and rework later!
```

### ✅ Correct: Enforce Quality Standards
```markdown
spec-analyst output: 450 lines, many TODOs
Quality Gate: 72% FAIL
Me: "Requirements incomplete. Feedback: [specific improvements needed]"
→ Re-spawn spec-analyst with detailed feedback
→ Attempt 2: 1,120 lines, comprehensive
Quality Gate: 87% PASS
→ Proceed to architecture
```

---

## Integration Example: Research + Planning

### Scenario: Building an AI-Powered Code Review Tool

**Step 1: Research Phase**
```markdown
User: "Research best practices for AI code review tools"
→ multi-agent-researcher skill activated
→ 4 researchers investigate:
  - Subtopic 1: AI models for code understanding
  - Subtopic 2: Code review workflows and UX patterns
  - Subtopic 3: Security and privacy considerations
  - Subtopic 4: Integration with Git platforms
→ Comprehensive report: files/reports/ai-code-review-best-practices_20251119.md
```

**Step 2: Planning Phase**
```markdown
User: "Plan an AI code review tool incorporating best practices from research"
→ spec-workflow-orchestrator skill activated

spec-analyst:
- Reads research report
- Extracts requirements based on best practices
- Documents functional requirements (AI model integration, PR integration, inline comments)
- Non-functional: Privacy (no code sent to external APIs), performance (<5s review time)
- Output: requirements.md (1,420 lines) incorporating research findings

spec-architect:
- Reads requirements + research report
- Chooses tech stack based on researched approaches (local LLM, no cloud)
- Designs architecture: local code analysis, rule engine, LLM integration
- Creates ADRs referencing research (why local LLM, why specific model)
- Output: architecture.md (1,890 lines) + 6 ADRs

spec-planner:
- Reads requirements + architecture
- Creates tasks implementing researched UX patterns
- Phases aligned with research recommendations
- Output: tasks.md (820 lines)

Result: Research-backed, well-informed specifications ready for implementation
```

---

## Output Quality Examples

### Requirements Document (Good)
- **Length**: 1,245 lines
- **Structure**: Executive summary, stakeholders, 15 FRs, 8 NFRs, 12 user stories, edge cases, success metrics
- **Specificity**: "Post creation API responds in <200ms for 95th percentile"
- **Testability**: All user stories have EARS acceptance criteria

### Architecture Document (Good)
- **Length**: 1,680 lines
- **Diagrams**: 4 Mermaid diagrams (system, component, sequence, data flow)
- **Technology Justification**: Each tech choice explained with trade-offs
- **ADRs**: 5 decisions documented with context, alternatives, consequences
- **Security**: Dedicated section with threat model and mitigations

### Tasks Document (Good)
- **Length**: 720 lines
- **Task Breakdown**: 28 atomic tasks (each 1-2 days max)
- **Dependencies**: Mermaid graph showing blocking relationships
- **Risk Assessment**: 4 risks identified with specific mitigations
- **Testing Strategy**: Unit, integration, E2E coverage defined

---

## Command Shortcuts

Quick invocation via `/plan-feature`:
```markdown
/plan-feature

I need comprehensive planning for: [Your project description]
```

Check project status via `/project-status`:
```markdown
/project-status

Shows current implementation phase and next steps
```

Verify structure via `/verify-structure`:
```markdown
/verify-structure

Confirms all agents and skills are properly configured
```
