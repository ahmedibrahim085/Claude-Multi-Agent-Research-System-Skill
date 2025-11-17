# Session Logging System

## Overview

This project implements comprehensive session logging based on the reference implementation from [claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent).

All tool calls made by the orchestrator and subagents are automatically logged to provide:
- **Audit trails** for compliance and verification
- **Debugging** capabilities when workflows fail
- **Performance analysis** to optimize agent behavior

## Log Directory Structure

```
logs/
└── session_YYYYMMDD_HHMMSS/
    ├── transcript.txt      # Human-readable tool call log
    └── tool_calls.jsonl    # Structured JSON log
```

### Session Naming

Session directories are named with timestamps: `session_20251117_143022`
- Format: `session_YYYYMMDD_HHMMSS`
- Automatically created when session starts
- Each session gets its own isolated directory

## Log Files

### transcript.txt (Human-Readable)

**Purpose**: Easy-to-read audit trail for debugging and verification

**Format**:
```
Research Agent Session Log
Session ID: session_20251117_143022
Started: 2025-11-17T14:30:22.000Z
================================================================================

[14:30:25] ORCHESTRATOR → Task ✅
  Input: {
    "subagent_type": "researcher",
    "description": "Research container architecture",
    "prompt": "..."
  }
  Output: Success (2.4 KB)
  Duration: 1250ms
────────────────────────────────────────────────────────────────────────────────

[14:31:10] RESEARCHER-1 → WebSearch ✅
  Input: {
    "query": "super-app container architecture mobile"
  }
  Output: Success (15.2 KB)
  Duration: 450ms
────────────────────────────────────────────────────────────────────────────────

[14:32:05] RESEARCHER-1 → Write ✅
  Input: {
    "file_path": "files/research_notes/container-architecture.md",
    "content": "..."
  }
  Output: Success (1.1 KB)
  Duration: 25ms
────────────────────────────────────────────────────────────────────────────────
```

**Features**:
- Timestamps for each tool call
- Agent identification (ORCHESTRATOR, RESEARCHER-1, RESEARCHER-2, REPORT-WRITER)
- Tool name with success indicator (✅/❌)
- Truncated input (first 500 chars to avoid bloat)
- Output size in human-readable format (KB, MB)
- Duration in milliseconds

### tool_calls.jsonl (Structured)

**Purpose**: Machine-readable log for programmatic analysis

**Format**: JSON Lines (one JSON object per line)
```json
{"ts":"2025-11-17T14:30:25.123Z","agent":"ORCHESTRATOR","tool":"Task","input":{"subagent_type":"researcher","description":"Research container architecture","prompt":"..."},"success":true,"output_size":2458,"duration_ms":1250}
{"ts":"2025-11-17T14:31:10.456Z","agent":"RESEARCHER-1","tool":"WebSearch","input":{"query":"super-app container architecture mobile"},"success":true,"output_size":15582,"duration_ms":450}
{"ts":"2025-11-17T14:32:05.789Z","agent":"RESEARCHER-1","tool":"Write","input":{"file_path":"files/research_notes/container-architecture.md","content":"..."},"success":true,"output_size":1125,"duration_ms":25}
```

**Fields**:
- `ts`: ISO 8601 timestamp
- `agent`: Agent identifier (ORCHESTRATOR, RESEARCHER-1, etc.)
- `tool`: Tool name (Task, WebSearch, Write, Read, Glob, etc.)
- `input`: Complete tool input parameters
- `success`: Boolean indicating if tool call succeeded
- `output_size`: Size of tool output in bytes
- `duration_ms`: Execution duration in milliseconds

## Agent Identification

The logging system identifies agents using the following logic:

### ORCHESTRATOR
- Agent that spawns researchers via Task tool
- Coordinates workflow phases
- Does NOT have Write tool access when multi-agent-researcher skill is active

### RESEARCHER-1, RESEARCHER-2, RESEARCHER-3, ...
- Numbered based on order of research note creation
- Perform WebSearch and Write to `files/research_notes/`
- Each gets unique identifier (RESEARCHER-1, RESEARCHER-2, etc.)

### REPORT-WRITER
- Agent that synthesizes findings
- Reads all research notes via Read/Glob
- Writes synthesis report to `files/reports/`

### Detection Heuristics

1. **Environment variable**: `CLAUDE_AGENT_TYPE` (if SDK provides it)
2. **File paths**: Writing to `files/research_notes/` → researcher, `files/reports/` → report-writer
3. **Tool usage**: Task tool → orchestrator, WebSearch → researcher
4. **Session phase**: Synthesis phase active → report-writer

## Implementation

### Hooks

**SessionStart Hook** (`.claude/hooks/session-start-restore-research.ts`):
- Initializes log directory on session start
- Creates `transcript.txt` and `tool_calls.jsonl`
- Prints session log directory path

**PostToolUse Hook** (`.claude/hooks/post-tool-use-track-research.ts`):
- Fires after EVERY tool call
- Logs to both transcript.txt and tool_calls.jsonl
- Continues workflow even if logging fails (non-blocking)

### Logger Module

**Session Logger** (`.claude/utils/session-logger.ts`):
- Core logging functionality
- Agent identification logic
- File formatting utilities
- Session ID generation

## Usage

### Viewing Logs

**Human-readable transcript**:
```bash
cat logs/session_20251117_143022/transcript.txt
```

**Structured JSON log**:
```bash
cat logs/session_20251117_143022/tool_calls.jsonl | jq
```

### Analyzing Logs

**Count tool calls by agent**:
```bash
cat logs/session_*/tool_calls.jsonl | jq -r '.agent' | sort | uniq -c
```

**Find failed tool calls**:
```bash
cat logs/session_*/tool_calls.jsonl | jq 'select(.success == false)'
```

**Calculate average duration per tool**:
```bash
cat logs/session_*/tool_calls.jsonl | jq -r '.tool' | sort | uniq -c
```

**See which researcher wrote which notes**:
```bash
grep "RESEARCHER.*Write" logs/session_*/transcript.txt
```

## Debugging Workflows

### Scenario: Synthesis Not Working

**Check transcript**:
```bash
# Did orchestrator spawn report-writer?
grep "ORCHESTRATOR.*Task.*report-writer" logs/session_*/transcript.txt

# Or did orchestrator write synthesis directly (violation)?
grep "ORCHESTRATOR.*Write.*files/reports" logs/session_*/transcript.txt
```

### Scenario: Researcher Failed

**Check failed tool calls**:
```bash
# Find which researcher failed
cat logs/session_*/tool_calls.jsonl | jq 'select(.success == false) | {agent, tool, input}'

# Check transcript for error details
grep "❌ FAILED" logs/session_*/transcript.txt
```

### Scenario: Performance Issues

**Check tool durations**:
```bash
# Find slow tool calls (>5 seconds)
cat logs/session_*/tool_calls.jsonl | jq 'select(.duration_ms > 5000) | {agent, tool, duration_ms}'

# Average WebSearch duration
cat logs/session_*/tool_calls.jsonl | jq 'select(.tool == "WebSearch") | .duration_ms' | awk '{sum+=$1; count++} END {print sum/count " ms"}'
```

## Git Ignore

Session logs are **NOT committed to git** (`.gitignore` configured):

```gitignore
# Session logs (generated by hooks)
logs/
```

Only the `.gitignore` file inside `logs/` is tracked:

```
logs/
└── .gitignore  # Tracked
```

## Comparison to Reference Implementation

| Feature | Reference (Python SDK) | This Implementation (Claude Code) |
|---------|----------------------|-----------------------------------|
| **Directory structure** | `logs/session_YYYYMMDD_HHMMSS/` | ✅ Same |
| **transcript.txt** | Human-readable log | ✅ Implemented |
| **tool_calls.jsonl** | Structured JSON log | ✅ Implemented |
| **Agent identification** | Via `parent_tool_use_id` | Via heuristics + file paths |
| **Hook registration** | Python SDK `HookMatcher` | TypeScript hooks in `.claude/hooks/` |
| **Session tracking** | SDK-managed | Manual session ID generation |

### Key Differences

1. **Agent identification**: Reference uses `parent_tool_use_id` from SDK; we use heuristics based on file paths and tool usage
2. **Language**: Reference is Python; we use TypeScript for Claude Code compatibility
3. **Hook system**: Reference uses SDK hook registration; we use Claude Code's file-based hooks

## Troubleshooting

### Logs not being created

**Check hook is enabled**:
```bash
# Verify hooks are executable
ls -la .claude/hooks/

# Check settings.json has hooks configured
cat .claude/settings.json | grep -A 10 "hooks"
```

**Check for errors**:
```bash
# Hooks log errors to stderr, check Claude Code output
```

### Agent misidentification

**Check detection logic** in `.claude/utils/session-logger.ts`:
- Environment variable: `CLAUDE_AGENT_TYPE`
- File paths: `files/research_notes/` vs `files/reports/`
- Tool usage patterns

**Manual override**: Set `CLAUDE_AGENT_TYPE` environment variable if SDK provides it

### Performance impact

**Hooks are non-blocking**: If logging fails, workflow continues
**Output size**: Large outputs are truncated in transcript.txt (500 char limit)
**File I/O**: Append-only writes, minimal overhead

## Future Enhancements

1. **Parent tool use ID**: When Claude Code SDK provides `parent_tool_use_id`, use it for precise agent tracking
2. **Log rotation**: Implement automatic cleanup of old session logs
3. **Analytics dashboard**: Web UI to visualize session logs
4. **Performance metrics**: Automated performance reports per session
5. **Error aggregation**: Summary of all errors across sessions

## References

- [claude-agent-sdk-demos/research-agent](https://github.com/anthropics/claude-agent-sdk-demos/tree/main/research-agent) - Reference implementation
- [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk) - Official blog post
- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks) - Hook system docs
