#!/usr/bin/env python3
"""
Shared utilities for code search scripts.

Provides:
- Global installation validation and import setup
- Standardized JSON error/success output
- Common error handling patterns
"""

import sys
import json
import os
from pathlib import Path

def setup():
    """
    Setup imports from global installation.

    Returns:
        tuple: (IntelligentSearcher, CodeIndexManager) classes

    Raises:
        SystemExit: If global installation not found or imports fail
    """
    # Determine platform-specific installation directory
    if os.name == 'nt':  # Windows
        INSTALL_DIR = Path.home() / "AppData" / "Local" / "claude-context-local"
    else:  # Linux/macOS
        INSTALL_DIR = Path.home() / ".local" / "share" / "claude-context-local"

    # Resolve symlinks to real path (CC#3)
    INSTALL_DIR = INSTALL_DIR.resolve()

    if not INSTALL_DIR.exists():
        error_exit(
            "Global installation not found",
            install_path=str(INSTALL_DIR),
            install_cmd="curl -fsSL https://raw.githubusercontent.com/FarhanAliRaza/claude-context-local/main/scripts/install.sh | bash"
        )

    sys.path.insert(0, str(INSTALL_DIR))

    # Import with specific error messages
    try:
        from search.searcher import IntelligentSearcher
    except ImportError as e:
        error_exit(f"Failed to import search module: {e}",
                   suggestion="Global installation may be corrupted. Reinstall.")

    try:
        from indexing.index_manager import CodeIndexManager
    except ImportError as e:
        error_exit(f"Failed to import indexing module: {e}",
                   suggestion="Global installation may be corrupted. Reinstall.")

    return IntelligentSearcher, CodeIndexManager

def error_exit(message, **kwargs):
    """
    Exit with error JSON to stderr.

    Args:
        message: Error message
        **kwargs: Additional fields (suggestion, install_cmd, etc.)
    """
    print(json.dumps(
        {"success": False, "error": message, **kwargs},
        indent=2
    ), file=sys.stderr)
    sys.exit(1)

def success(data):
    """
    Print success JSON to stdout.

    Args:
        data: Result data (must be JSON-serializable)
    """
    print(json.dumps(
        {"success": True, "data": data},
        indent=2
    ))
