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
- **Command**: `tsx .claude/hooks/user-prompt-submit-skill-activation.ts`
- **Description**: Auto-activate multi-agent-researcher skill for research tasks

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
            "command": "tsx .claude/hooks/user-prompt-submit-skill-activation.ts"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "tsx .claude/hooks/post-tool-use-track-research.ts"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "tsx .claude/hooks/session-start-restore-research.ts"
          }
        ]
      }
    ]
  }
}
```

## Installing tsx

If `tsx` is not installed:

```bash
npm install -g tsx
```

Or use `ts-node`:

```bash
npm install -g ts-node
```

Then update hook commands to use `ts-node` instead of `tsx`.

## Testing Hooks

### Test UserPromptSubmit Hook

```bash
echo '{"user_prompt":"research quantum computing","session_id":"test"}' | tsx .claude/hooks/user-prompt-submit-skill-activation.ts
```

Expected output: Enforcement message about research workflow

### Test PostToolUse Hook

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"files/reports/test.md"}}' | tsx .claude/hooks/post-tool-use-track-research.ts
```

Expected: Updates state.json (when state exists)

## Troubleshooting

### Hook Not Executing

1. Check hook is executable: `ls -la .claude/hooks/*.ts`
2. Run manually to see errors: `tsx .claude/hooks/[hook-name].ts`
3. Check Claude Code logs for hook execution

### TypeScript Errors

If hooks fail with TypeScript errors:
- Ensure `tsx` is installed globally
- Or configure to use `node --loader ts-node/esm` instead

### State File Not Created

- PostToolUse hook creates state on first Write operation
- UserPromptSubmit only injects messages, doesn't create state
- State creation happens when research workflow actually executes

## Hook Behavior

### UserPromptSubmit

- Matches user prompts against skill-rules.json
- Keywords: "research", "investigate", "analyze", etc.
- Injects enforcement reminder into Claude's context
- Helps ensure skill activation

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

After configuration, when you type a prompt like "research machine learning", you should see:

```
🔒 WORKFLOW ENFORCEMENT ACTIVATED

Detected: Research task keywords in your prompt
Required Skill: multi-agent-researcher
...
```

This confirms hooks are working correctly.
