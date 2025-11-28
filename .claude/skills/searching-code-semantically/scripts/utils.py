#!/usr/bin/env python3
"""
Shared utilities for code search scripts.

Provides:
- Global installation validation and import setup
- Standardized JSON error/success output
- Common error handling patterns
- Auto-detection and use of venv Python
"""

import sys
import json
import os
from pathlib import Path

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

def ensure_venv():
    """
    Ensure script is running in the global installation's venv.
    If not, re-execute the script using the venv Python.

    This allows scripts to work regardless of which Python interpreter
    is used to invoke them.
    """
    # Determine platform-specific venv directory
    if os.name == 'nt':  # Windows
        venv_dir = Path.home() / "AppData" / "Local" / "claude-context-local" / ".venv"
        venv_python = venv_dir / "Scripts" / "python.exe"
    else:  # Linux/macOS
        venv_dir = Path.home() / ".local" / "share" / "claude-context-local" / ".venv"
        venv_python = venv_dir / "bin" / "python"

    # Check if we're already running in the venv using sys.prefix
    # (more reliable than comparing executables which may be symlinks)
    current_prefix = Path(sys.prefix).resolve()
    expected_prefix = venv_dir.resolve()

    if current_prefix != expected_prefix:
        # Not in venv - re-execute using venv Python
        if not venv_python.exists():
            error_exit(
                "Virtual environment not found",
                venv_path=str(venv_python),
                suggestion="Global installation may be incomplete. Reinstall claude-context-local."
            )

        # Re-execute current script with venv Python
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)

def setup():
    """
    Setup imports from global installation.

    Automatically switches to venv Python if not already running in it,
    then imports required modules from global installation.

    Returns:
        tuple: (IntelligentSearcher, CodeIndexManager) classes

    Raises:
        SystemExit: If global installation not found or imports fail
    """
    # Ensure we're running in the venv (will re-exec if needed)
    ensure_venv()

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
        from search.indexer import CodeIndexManager
    except ImportError as e:
        error_exit(f"Failed to import indexing module: {e}",
                   suggestion="Global installation may be corrupted. Reinstall.")

    return IntelligentSearcher, CodeIndexManager
