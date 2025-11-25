#!/bin/bash
# Workflow state management for spec-workflow-orchestrator
# Manages state file: logs/state/spec-workflow-state.json

set -euo pipefail

STATE_FILE="logs/state/spec-workflow-state.json"
STATE_DIR="logs/state"

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# Initialize empty state if doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    echo '{}' > "$STATE_FILE"
fi

# Function: Set workflow state
# Usage: workflow_state.sh set <project-slug> <mode> [user-input]
set_state() {
    local project_slug="$1"
    local mode="$2"
    local user_input="${3:-}"
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Create state JSON
    cat > "$STATE_FILE" <<EOF
{
  "project_slug": "$project_slug",
  "mode": "$mode",
  "user_input": "$user_input",
  "timestamp": "$timestamp",
  "status": "active"
}
EOF

    echo "✅ State saved: $project_slug ($mode)"
}

# Function: Get workflow state value
# Usage: workflow_state.sh get <key>
get_state() {
    local key="$1"

    if [ ! -f "$STATE_FILE" ]; then
        echo ""
        return 1
    fi

    # Use Python for JSON parsing (works on macOS and Linux)
    python3 -c "
import json
import sys
try:
    with open('$STATE_FILE', 'r') as f:
        data = json.load(f)
    print(data.get('$key', ''))
except:
    sys.exit(1)
"
}

# Function: Clear workflow state
# Usage: workflow_state.sh clear
clear_state() {
    cat > "$STATE_FILE" <<EOF
{
  "status": "cleared",
  "cleared_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    echo "✅ State cleared"
}

# Function: Display current state
# Usage: workflow_state.sh show
show_state() {
    if [ ! -f "$STATE_FILE" ]; then
        echo "No state file found"
        return 1
    fi

    echo "Current Workflow State:"
    echo "────────────────────────"
    cat "$STATE_FILE" | python3 -m json.tool
}

# Main command dispatch
COMMAND="${1:-}"

case "$COMMAND" in
    set)
        if [ $# -lt 3 ]; then
            echo "Usage: workflow_state.sh set <project-slug> <mode> [user-input]"
            exit 1
        fi
        set_state "$2" "$3" "${4:-}"
        ;;
    get)
        if [ $# -lt 2 ]; then
            echo "Usage: workflow_state.sh get <key>"
            exit 1
        fi
        get_state "$2"
        ;;
    clear)
        clear_state
        ;;
    show)
        show_state
        ;;
    *)
        echo "Workflow State Management"
        echo "Usage: workflow_state.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  set <project-slug> <mode> [user-input]  - Set workflow state"
        echo "  get <key>                                - Get state value"
        echo "  show                                     - Display current state"
        echo "  clear                                    - Clear state"
        echo ""
        echo "Modes: fresh | refinement"
        exit 1
        ;;
esac
