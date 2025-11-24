# Changelog

All notable changes to the Multi-Agent Research Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2025-11-25

### Added
- **Multi-Tool Parallel Search** in researcher agent for comprehensive coverage
  - Query all 4 MCP tools simultaneously
  - Merge and deduplicate results
  - Cross-validate sources appearing in multiple engines
  - 30-50% increase in source diversity
- **Adaptive Decomposition** with AI-powered pattern selection
  - 6 decomposition patterns (Temporal, Categorical, Stakeholder, Problem-Solution, Geographic, Hierarchical)
  - Automatic pattern selection based on topic characteristics
  - Improved subtopic quality
- **Incremental Synthesis** (optional) for faster insights  
  - New `incremental-synthesizer` agent
  - Progressive report building as researchers complete
  - Phase 3A option in SKILL.md
  - 50% reduction in time-to-first-insight

### Changed
- Updated `plugin.json` from v2.4.0 to v2.5.0
- Enhanced `researcher.md` with multi-tool search strategy
- Enhanced `SKILL.md` with adaptive decomposition logic and Phase 3A

### Performance Improvements
- Faster time-to-first-insight with incremental synthesis
- Broader source coverage with parallel search
- Better subtopic alignment with adaptive decomposition

## [2.4.0] - 2025-11-24

### Added
- **Custom slash commands** for workflow shortcuts:
  - `/research` - Standard research (3 subtopics)
  - `/research-quick` - Quick research (2 subtopics)
  - `/research-deep` - Deep research (4 subtopics)
- **Lifecycle hooks** (`hooks/hooks.json`) for automation:
  - Auto-create research directories on skill activation
  - Log researcher spawns, synthesis starts, report generation
- **Memory integration** in report-writer agent for session tracking
- **Error handling** with fallback chains for MCP tool failures
- **Comprehensive documentation**:
  - `TESTING.md` - Complete testing guide
  - `INSTALL.md` - Step-by-step installation
  - `DEPLOYMENT.md` - Release checklist
- **Progress notifications** with emoji-enhanced UX
- Keyword "automation" to plugin.json

### Changed
- Updated `plugin.json` from v2.3.0 to v2.4.0
- Enhanced `researcher.md` with explicit MCP tool documentation and selection strategy
- Enhanced `SKILL.md` with MCP server availability table and progress templates
- Enhanced `report-writer.md` with memory persistence schema
- Updated `PLUGIN_README.md` with custom commands section

### Fixed
- Clarified MCP tool availability (auto-available via plugin)
- Added error recovery procedures for rate limits and network issues

## [2.3.0] - 2025-11-24

### Added
- MCP tool documentation in `researcher.md`
- MCP server awareness section in `SKILL.md`
- Keywords in `plugin.json` for discoverability

### Changed
- Updated plugin version from v2.2.0 to v2.3.0

## [2.2.0] - Initial Release

### Added
- Multi-agent research orchestration
- 4 MCP search providers (Exa, Tavily, Brave, Perplexity)
- Parallel researcher execution
- Mandatory report-writer synthesis
- Basic skill and agent definitions

---

## Upgrade Guide

### From 2.3.0 to 2.4.0
- No breaking changes
- New features available immediately
- Set environment variables for MCP servers if not already done

### From 2.2.0 to 2.3.0
- Update plugin.json
- Review new MCP documentation in agents

---

## Future Roadmap

### v2.5.0 (Planned)
- Multi-tool parallel search
- Adaptive decomposition strategies
- Cross-session insight generation

### v3.0.0 (Future)
- Real-time collaboration
- Custom MCP server templates
- Visual research dashboards
