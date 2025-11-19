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

**SessionStart Hook** (Optional):
- **Matcher**: (leave empty)
- **Command**: `tsx .claude/hooks/session-start-restore-research.ts`
- **Description**: Restore incomplete research sessions on restart

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

- Matches user prompts against skill-rules.json for BOTH skills
- **Research Keywords**: "research", "investigate", "analyze", "explore", "study", etc. (37+ keywords)
- **Planning Keywords**: "plan", "design", "build", "architect", "specs", "requirements", etc. (90+ keywords)
- **Pattern Matching**: Regex patterns like "(build|create)\\s+(a|an|the)?\\s*(app|system|feature)"
- Injects enforcement reminder into Claude's context BEFORE prompt is processed
- Helps ensure automatic skill activation
- Can detect multiple skills in single prompt (e.g., "research and design")

### PostToolUse

- Tracks Write operations to research_notes/ and reports/
- Updates state.json with phase completions
- Records which agent performed each phase
- Validates quality gates
- Emits warnings on violations

### SessionStart (Optional)

- Checks for incomplete research sessions
- Injects resumption context if found
- Lists available research notes
- Suggests next steps

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
