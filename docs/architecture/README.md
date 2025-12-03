# Architecture Documentation

This directory contains Architecture Decision Records (ADRs) and architectural design documentation for the Claude Multi-Agent Research System.

---

## Architecture Decision Records (ADRs)

ADRs document significant architectural decisions, their rationale, alternatives considered, and consequences.

### ADR-001: Direct Script vs Agent for Auto-Reindex

**Status**: ✅ Accepted
**Date**: 2025-12-03
**Impact**: Core auto-reindex implementation

**Decision**: Use direct bash scripts for automatic reindex operations (session start, post-modification hooks) instead of invoking the semantic-search-indexer agent.

**Key Rationale**:
- **5x faster**: 2.7s vs 14.6s (performance critical for background operations)
- **$0 cost**: vs $144/year per 10 developers (high-frequency operations)
- **Reliable**: Deterministic, predictable behavior (no surprises in background)
- **Offline**: Works without internet (developer on plane scenario)
- **Safe**: Won't exceed hook timeout (9s buffer vs risky timeout)

**Agent Use**: Reserved for manual operations where intelligence and rich output add value.

**Documents**:
- [Full ADR](./ADR-001-direct-script-vs-agent-for-auto-reindex.md) - Complete analysis with benchmarks, cost projections, testing
- [Quick Reference](./auto-reindex-design-quick-reference.md) - TL;DR, code examples, FAQs

---

## When to Use What

### ✅ Direct Script (Automatic Operations)

**Use for:**
- Session start reindex
- Post-file-modification reindex (Write/Edit/NotebookEdit)
- Hook-based operations
- Background maintenance
- High-frequency tasks (>5/day)

**Characteristics:**
- Fast (2.7s)
- Free ($0)
- Predictable
- Works offline

### ✅ Agent (Manual Operations)

**Use for:**
- User explicitly requests reindex
- First-time setup
- Troubleshooting
- Index diagnostics
- Manual full reindex

**Characteristics:**
- Intelligent (adaptive)
- Interactive (can ask questions)
- Rich output (progress, stats)
- User-friendly explanations

---

## Quick Reference

**Question**: When should I use direct script vs agent?

**Answer**:
- **Background/automatic** → Direct script (speed, cost, reliability)
- **User-invoked/manual** → Agent (intelligence, interaction, rich output)

**Example**:
- Session start reindex → Script ✓ (2.7s, silent, free)
- User types "reindex my project" → Agent ✓ (10-20s, detailed output, $0.02)

---

## Performance Benchmarks

| Operation | Direct Script | Agent | Difference |
|-----------|---------------|-------|------------|
| Execution Time | 2.7s | 14.6s | 5.4x faster |
| Annual Cost (10 devs) | $0 | $144 | $144 savings |
| Works Offline | ✅ Yes | ❌ No | Critical for travel |
| Hook Timeout Risk | ✅ Safe (9s buffer) | ⚠️ Risky (variable) | Safety critical |

---

## Related Documentation

**Implementation**:
- `.claude/utils/reindex_manager.py` - Direct script execution logic
- `.claude/agents/semantic-search-indexer.md` - Agent definition
- `.claude/hooks/session-start-index.py` - Session start hook
- `.claude/hooks/post-tool-use-track-research.py` - Post-write hook

**Testing**:
- `docs/guides/incremental-reindex-validation.md` - Validation results
- `docs/testing/incremental-reindex-agent-test.md` - Agent testing

**Configuration**:
- `docs/configuration/configuration-guide.md` - Reindex configuration options

---

## Contributing

When adding new ADRs:

1. Use sequential numbering: `ADR-XXX-title.md`
2. Follow standard ADR format:
   - Context
   - Decision
   - Rationale
   - Consequences
   - Alternatives Considered
3. Create quick reference if complex
4. Update this README
5. Reference in `.claude/CLAUDE.md` and `README.md`

---

**Last Updated**: 2025-12-03
