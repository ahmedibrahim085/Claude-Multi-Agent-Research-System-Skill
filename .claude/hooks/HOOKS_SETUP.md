# Hooks Setup Guide

This guide explains how to configure the workflow enforcement hooks in Claude Code.

## Prerequisites

- Node.js installed with `tsx` or `ts-node` available
- Claude Code CLI with hooks support
- Hooks must be configured through Claude Code settings

## Hook Configuration

### Option 1: Via Claude Code UI (Recommended)

1. Open Claude Code
2. Type `/hooks` or access Settings → Hooks
3. Add the following configurations:

**UserPromptSubmit Hook**:
- **Matcher**: (leave empty to match all prompts)
- **Command**: `python3 .claude/hooks/user-prompt-submit.py`
- **Description**: Universal skill activation for both multi-agent-researcher and spec-workflow-orchestrator

**PostToolUse Hook**:
- **Matcher**: `Write`
- **Command**: `tsx .claude/hooks/post-tool-use-track-research.ts`
- **Description**: Track research phases and agent assignments

**SessionStart Hook** (Required):
- **Matcher**: (leave empty)
- **Command**: `python3 .claude/hooks/session-start.py`
- **Description**: Auto-reindex semantic search (smart change detection, 6-hour cooldown), session logging initialization, prerequisites checking, skill crash recovery

### Option 2: Via settings.json

If you prefer manual configuration, add to your Claude Code settings.json:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/user-prompt-submit.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use-track-research.py\""
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.py\""
          }
        ]
      }
    ]
  }
}
```

## Prerequisites

Hooks are implemented in Python 3 and require no additional installation beyond Python 3.x which comes pre-installed on macOS and most Linux distributions.

## Testing Hooks

### Test UserPromptSubmit Hook

Test research task detection:
```bash
echo '{"user_prompt":"research quantum computing","session_id":"test"}' | python3 .claude/hooks/user-prompt-submit.py
```

Expected output: Enforcement message about research workflow

Test planning task detection:
```bash
echo '{"user_prompt":"build a local web interface for session logs","session_id":"test"}' | python3 .claude/hooks/user-prompt-submit.py
```

Expected output: Enforcement message about planning workflow

Test dual trigger detection:
```bash
echo '{"user_prompt":"research and design a new authentication system","session_id":"test"}' | python3 .claude/hooks/user-prompt-submit.py
```

Expected output: Both research and planning enforcement messages

### Test PostToolUse Hook

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"files/reports/test.md"}}' | python3 .claude/hooks/post-tool-use-track-research.py
```

Expected: Updates state.json (when state exists)

## Troubleshooting

### Hook Not Executing

1. Check hook is executable: `ls -la .claude/hooks/*.py`
2. Run manually to see errors: `python3 .claude/hooks/[hook-name].py`
3. Check Claude Code logs for hook execution
4. Verify Python 3 is available: `python3 --version`

### Python Errors

If hooks fail with Python errors:
- Ensure Python 3.x is installed: `python3 --version`
- Check utils modules are present: `ls .claude/utils/`
- Run hook manually with test input to see error details

### State File Not Created

- PostToolUse hook creates state on first Write operation
- UserPromptSubmit only injects messages, doesn't create state
- State creation happens when research workflow actually executes

## Hook Behavior

### UserPromptSubmit

- Matches user prompts against skill-rules.json for **ALL THREE skills**
- **Research Keywords**: "research", "investigate", "analyze", "explore", "study", etc. (49+ keywords)
- **Planning Keywords**: "plan", "design", "build", "architect", "specs", "requirements", etc. (119+ keywords)
- **Semantic-Search Keywords**: "search", "find", "locate", "where is", "how does X work", "find similar", etc. (52+ keywords)
- **Pattern Matching**: Regex patterns like "(build|create)\\s+(a|an|the)?\\s*(app|system|feature)"
- **Prerequisites Checking**: Conditionally enforces semantic-search based on prerequisites state file
- Injects enforcement reminder into Claude's context BEFORE prompt is processed
- Helps ensure automatic skill activation (95% reliability vs 70% prompt-only)
- Can detect multiple skills in single prompt (e.g., "research and design") → compound request detection

### PostToolUse

- Tracks Write operations to research_notes/ and reports/
- Updates state.json with phase completions
- Records which agent performed each phase
- Validates quality gates
- Emits warnings on violations

### SessionStart (Required)

- **Auto-reindex semantic search**: Trigger-based logic (startup/resume/clear/compact) with smart change detection
- **6-hour cooldown**: Prevents rapid full reindex spam during frequent restarts
- **Concurrent protection**: PID-based lock files prevent duplicate indexing operations
- **Prerequisites checking**: Validates semantic-search setup, enables conditional enforcement
- **Session logging**: Initializes transcript, tool calls, and state tracking
- **Skill crash recovery**: Detects and handles interrupted skill executions
- **Directory setup**: Creates required directories (logs/, files/research_notes/, files/reports/)
- **Performance**: <20ms overhead (non-blocking, background processes)

## Verification

After configuration, when you type different prompt types, you should see:

**Research prompt** ("research machine learning"):
```
🔒 RESEARCH WORKFLOW ENFORCEMENT ACTIVATED

Detected: Research task keywords in your prompt
Required Skill: multi-agent-researcher
...
```

**Planning prompt** ("build a web interface"):
```
🔒 PLANNING WORKFLOW ENFORCEMENT ACTIVATED

Detected: Planning task keywords in your prompt
Required Skill: spec-workflow-orchestrator
...
```

**Dual prompt** ("research and design authentication"):
```
🔒 RESEARCH WORKFLOW ENFORCEMENT ACTIVATED
...

🔒 PLANNING WORKFLOW ENFORCEMENT ACTIVATED
...
```

This confirms hooks are working correctly.
