#!/bin/bash
set -e

# Validate HOME is set
if [ -z "$HOME" ]; then
    echo "Error: HOME environment variable is not set" >&2
    exit 1
fi

# Check installation directory
INSTALL_DIR="$HOME/.local/share/claude-context-local"
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Error: claude-context-local is not installed at $INSTALL_DIR" >&2
    echo "Install with: curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash" >&2
    exit 1
fi

# Find uv executable
UV_CMD=""
for path in \
    "$(which uv 2>/dev/null)" \
    "$HOME/.langflow/uv" \
    "$HOME/.cargo/bin/uv" \
    "$HOME/.local/bin/uv"; do
    if [ -x "$path" ]; then
        UV_CMD="$path"
        break
    fi
done

if [ -z "$UV_CMD" ]; then
    echo "Error: Could not find 'uv' executable" >&2
    echo "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# Set project-local storage directory
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
export CODE_SEARCH_STORAGE="$PROJECT_ROOT/.code-search-index"

# Execute MCP server
exec "$UV_CMD" run --directory "$INSTALL_DIR" python mcp_server/server.py "$@"
