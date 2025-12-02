# Planning Orchestration Workflow
## Comprehensive Specification Development with Quality Gates

This workflow documents the mandatory orchestration pattern for planning tasks, including trigger keywords, workflow steps, and quality gate validation that ensures development-ready specifications.

---

## CRITICAL: Planning Orchestration Rules

### ALWAYS Use spec-workflow-orchestrator Skill When:

**Trigger Keywords in User Prompt**:
- **Planning Actions**: "plan", "design", "architect", "blueprint", "outline", "draft", "sketch", "map out", "structure", "organize", "prototype", "model", "define", "specify", "scaffold", "frame", "conceptualize"
- **Build/Create**: "build", "create", "develop", "implement", "construct", "craft", "engineer", "make", "set up", "establish"
- **Specifications**: "specs", "specifications", "requirements", "functional requirements", "non-functional requirements", "acceptance criteria", "user stories", "use cases", "scenarios", "test cases"
- **Architecture**: "architecture", "system design", "technical design", "infrastructure", "framework", "schema", "data model", "API design", "component design"
- **Requirements**: "analyze requirements", "gather requirements", "define requirements", "requirement analysis", "feasibility study", "needs assessment", "scope definition"
- **Documentation**: "PRD", "product requirements document", "technical spec", "design doc", "architecture document", "ADR", "architecture decision record", "RFC", "proposal"
- **Features**: "features", "feature list", "capabilities", "functionality", "feature set", "feature spec", "MVP", "minimum viable product"
- **Planning Phases**: "roadmap", "project plan", "implementation plan", "development plan", "rollout plan", "migration plan", "deployment plan"
- **Conversational**: "what should we build", "how should we structure", "what's the best approach", "help me plan", "need to design", "want to architect", "thinking about building", "considering implementing", "what are the requirements for", "what features should", "how do we implement", "what's the architecture", "need specs for", "create a plan for", "design a system for", "outline the approach", "ready for development", "before we start coding", "what do we need", "how should this work"

**MANDATORY Workflow**:
1. **STOP** - Do NOT start manual planning with TodoWrite or direct file creation
2. **INVOKE**: Use `/skill spec-workflow-orchestrator` or let it auto-activate
3. **ANALYZE**: Spawn spec-analyst agent for requirements gathering
4. **ARCHITECT**: Spawn spec-architect agent for system design + ADRs
5. **PLAN**: Spawn spec-planner agent for task breakdown
6. **VALIDATE**: Quality gate (85% threshold) with iteration if needed

### Direct Planning vs Skill Orchestration

**Do Manual Planning ONLY for**:
- Trivial tasks (single-file changes, simple fixes)
- Tasks with 1-2 steps that don't need formal specs
- Quick experiments or prototypes explicitly marked as throwaway

**Use spec-workflow-orchestrator Skill for**:
- New features or systems (any non-trivial addition)
- Architecture changes (refactoring, new patterns)
- Multi-component work (3+ files or modules)
- Requirements gathering (when user asks "what should we build?")
- ANY task requiring formal specifications
- Projects needing ADRs or technical design docs

### Example Violations to AVOID

❌ **WRONG**: User asks "build a local web interface for session logs"
   → I create TodoWrite list and start planning manually
   → I analyze requirements myself
   → I write specs directly

✅ **CORRECT**: User asks "build a local web interface for session logs"
   → I invoke spec-workflow-orchestrator skill
   → Skill spawns spec-analyst for requirements (outputs: docs/planning/requirements.md)
   → Skill spawns spec-architect for design (outputs: docs/planning/architecture.md + docs/adrs/*.md)
   → Skill spawns spec-planner for tasks (outputs: docs/planning/tasks.md)
   → Quality gate validates all deliverables (85% threshold)

### Self-Check Before Acting

**Before starting planning work, ask yourself**:
1. Is this a new feature/system/architecture? → Use Skill
2. Did user ask for specs/requirements/features? → Use Skill
3. Will this require >3 files or multi-component work? → Use Skill
4. Did user say "plan", "design", "build", "architect"? → Use Skill
5. Is this more than a trivial 1-2 step task? → Use Skill

### Quality Gates

The spec-workflow-orchestrator enforces quality standards for all deliverables:

**Scoring System**:
- **Total Points**: 100 per deliverable
- **Pass Threshold**: 85/100 (85%)
- **Max Iterations**: 3 attempts per agent (fail after 3rd attempt)

**4 Criteria (25 points each)**:
1. **Completeness** (25 pts): All required sections present, no gaps, comprehensive coverage
2. **Technical Depth** (25 pts): Detailed technical specifications, architectural decisions documented
3. **Actionability** (25 pts): Clear implementation steps, testable acceptance criteria
4. **Clarity** (25 pts): Well-structured, easy to understand, proper formatting

**3 Deliverables Validated**:
- **requirements.md** (spec-analyst): User stories, acceptance criteria, constraints (~800-1,500 lines)
- **architecture.md + ADRs** (spec-architect): System design, technology choices, decision records (~600-1,000 lines)
- **tasks.md** (spec-planner): Implementation tasks, priorities, dependencies (~500-800 lines)

**Validation Flow**:
1. Agent creates deliverable
2. Quality gate validates (4 criteria × 25 points = 100 total)
3. If score ≥85: PASS, proceed to next agent
4. If score <85: FAIL, agent revises (max 3 iterations)
5. After 3 failures: Workflow stops, user notified
