#!/usr/bin/env python3
"""
Multi-Agent Research System Setup

Optional interactive setup script for customizing your installation.

The SessionStart hook handles basic setup automatically, so this script is
OPTIONAL - only run it if you want to customize paths or verify your setup.

Usage:
    python3 setup.py           # Interactive setup
    python3 setup.py --verify  # Just verify, don't change anything
    python3 setup.py --repair  # Auto-repair issues without prompts
    python3 setup.py --help    # Show help
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print a header with styling"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print("=" * len(text))


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes/no question"""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{question} [{default_str}]: ").strip().lower()

    if not response:
        return default
    return response in ('y', 'yes')


def get_project_root() -> Path:
    """Get project root directory"""
    return Path(__file__).parent.absolute()


def load_config() -> Dict[str, Any]:
    """Load config.json or return defaults"""
    project_root = get_project_root()
    config_path = project_root / '.claude' / 'config.json'

    default_config = {
        "paths": {
            "research_notes": "files/research_notes",
            "reports": "files/reports",
            "logs": "logs",
            "state": "logs/state"
        },
        "logging": {
            "enabled": True,
            "format": "flat",
            "session_id_format": "session_%Y%m%d_%H%M%S",
            "log_tool_calls": True
        },
        "research": {
            "max_parallel_researchers": 4,
            "default_model": "sonnet",
            "require_synthesis_delegation": True,
            "quality_gates_enabled": True
        }
    }

    if config_path.exists():
        try:
            with config_path.open('r') as f:
                return json.load(f)
        except Exception as e:
            print_warning(f"Failed to load config.json: {e}")
            return default_config

    return default_config


def save_config(config: Dict[str, Any]) -> None:
    """Save config to config.json"""
    project_root = get_project_root()
    config_path = project_root / '.claude' / 'config.json'

    # Ensure .claude directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with config_path.open('w') as f:
        json.dump(config, f, indent=2)

    print_success(f"Configuration saved to {config_path}")


def verify_python_version() -> bool:
    """Verify Python version is 3.8+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required (found {version.major}.{version.minor})")
        return False

    print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def verify_claude_code() -> bool:
    """Check if Claude Code is available"""
    # We can't directly check for Claude Code CLI, but we can check if we're in a Claude Code context
    # by looking for .claude directory
    project_root = get_project_root()
    claude_dir = project_root / '.claude'

    if not claude_dir.exists():
        print_warning("Claude Code environment not detected (.claude directory missing)")
        print_info("This is normal if you haven't started Claude Code in this directory yet")
        return False

    print_success("Claude Code environment detected")
    return True


def setup_settings() -> bool:
    """Setup settings.local.json from template"""
    project_root = get_project_root()
    template_path = project_root / '.claude' / 'settings.template.json'
    local_path = project_root / '.claude' / 'settings.local.json'

    if local_path.exists():
        print_info("settings.local.json already exists")
        return True

    if not template_path.exists():
        print_error("settings.template.json not found")
        return False

    # Copy template to local
    shutil.copy(template_path, local_path)
    print_success("Created settings.local.json from template")
    return True


def create_directories(config: Dict[str, Any]) -> None:
    """Create all required directories"""
    project_root = get_project_root()

    for path_key, path_value in config['paths'].items():
        full_path = project_root / path_value
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created directory: {path_value}/")
        else:
            print_info(f"Directory exists: {path_value}/")


def verify_hooks_configured() -> bool:
    """Verify hooks are configured in settings"""
    project_root = get_project_root()
    settings_path = project_root / '.claude' / 'settings.local.json'

    if not settings_path.exists():
        print_warning("settings.local.json not found - hooks not configured")
        return False

    try:
        with settings_path.open('r') as f:
            settings = json.load(f)

        # Check for PostToolUse and SessionStart hooks
        hooks = settings.get('hooks', {})
        has_post_tool = 'PostToolUse' in hooks
        has_session_start = 'SessionStart' in hooks

        if has_post_tool and has_session_start:
            print_success("Hooks configured (PostToolUse, SessionStart)")
            return True
        elif has_post_tool or has_session_start:
            print_warning(f"Partial hooks configuration (missing {'SessionStart' if not has_session_start else 'PostToolUse'})")
            return False
        else:
            print_warning("No hooks configured in settings.local.json")
            return False

    except Exception as e:
        print_error(f"Failed to verify hooks: {e}")
        return False


def prompt_for_custom_paths() -> Dict[str, Any]:
    """Prompt user for custom path configuration"""
    print("\nCustom Path Configuration")
    print("-" * 40)

    config = load_config()

    print("\nPress Enter to keep default values:")

    # Research notes directory
    current = config['paths']['research_notes']
    new_path = input(f"Research notes directory [{current}]: ").strip()
    if new_path:
        config['paths']['research_notes'] = new_path

    # Reports directory
    current = config['paths']['reports']
    new_path = input(f"Synthesis reports directory [{current}]: ").strip()
    if new_path:
        config['paths']['reports'] = new_path

    # Logs directory
    current = config['paths']['logs']
    new_path = input(f"Session logs directory [{current}]: ").strip()
    if new_path:
        config['paths']['logs'] = new_path

    # Max parallel researchers
    current = config['research']['max_parallel_researchers']
    new_val = input(f"Max parallel researchers [{current}]: ").strip()
    if new_val and new_val.isdigit():
        config['research']['max_parallel_researchers'] = int(new_val)

    return config


def interactive_setup() -> bool:
    """Run interactive setup"""
    project_root = get_project_root()

    print_header("Multi-Agent Research System Setup")
    print(f"\nProject root: {project_root}\n")

    all_good = True

    # 1. Check Python version
    print_header("1. Verifying Python")
    if not verify_python_version():
        all_good = False

    # 2. Check Claude Code environment
    print_header("2. Checking Claude Code Environment")
    verify_claude_code()  # Warning only, not critical

    # 3. Setup settings.local.json
    print_header("3. Setting Up Configuration Files")
    if not setup_settings():
        all_good = False

    # 4. Configure paths
    config_path = project_root / '.claude' / 'config.json'
    if not config_path.exists() or ask_yes_no("\nCustomize paths and settings?", default=False):
        config = prompt_for_custom_paths()
        save_config(config)
    else:
        config = load_config()
        print_info("Using existing configuration")

    # 5. Create directories
    print_header("4. Creating Directories")
    create_directories(config)

    # 6. Verify hooks
    print_header("5. Verifying Hooks Configuration")
    verify_hooks_configured()

    # 7. Final status
    print_header("Setup Complete!")

    if all_good:
        print_success("All checks passed")
        print("\n" + Colors.BOLD + "Next steps:" + Colors.RESET)
        print("1. Restart Claude Code to load hooks")
        print("2. Try a research query: 'research quantum computing'")
        print("3. Check logs in: logs/session_*")
    else:
        print_warning("Some checks failed - review messages above")

    return all_good


def verify_only() -> bool:
    """Run verification checks only, don't modify anything"""
    project_root = get_project_root()

    print_header("Verification Mode")
    print(f"Project root: {project_root}\n")

    issues = []

    # Check Python
    print_header("Python Version")
    if not verify_python_version():
        issues.append("Python version too old")

    # Check Claude Code
    print_header("Claude Code Environment")
    if not verify_claude_code():
        issues.append("Claude Code not detected")

    # Check settings.local.json
    print_header("Settings Configuration")
    local_path = project_root / '.claude' / 'settings.local.json'
    if not local_path.exists():
        print_warning("settings.local.json missing")
        issues.append("Missing settings.local.json")
    else:
        print_success("settings.local.json exists")

    # Check config.json
    print_header("Path Configuration")
    config_path = project_root / '.claude' / 'config.json'
    if not config_path.exists():
        print_warning("config.json missing (will use defaults)")
    else:
        print_success("config.json exists")
        config = load_config()

    # Check directories
    print_header("Required Directories")
    config = load_config()
    for path_key, path_value in config['paths'].items():
        full_path = project_root / path_value
        if not full_path.exists():
            print_warning(f"Missing: {path_value}/")
            issues.append(f"Missing directory: {path_value}/")
        else:
            print_success(f"Exists: {path_value}/")

    # Check hooks
    print_header("Hooks Configuration")
    if not verify_hooks_configured():
        issues.append("Hooks not properly configured")

    # Summary
    print_header("Verification Summary")
    if not issues:
        print_success("All checks passed!")
        return True
    else:
        print_error(f"Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  • {issue}")
        print(f"\n{Colors.BOLD}Run 'python3 setup.py' to fix issues{Colors.RESET}")
        return False


def repair_setup() -> bool:
    """Auto-repair setup issues without prompts"""
    project_root = get_project_root()

    print_header("Repair Mode")
    print(f"Project root: {project_root}\n")

    # 1. Setup settings if missing
    if not (project_root / '.claude' / 'settings.local.json').exists():
        print("Repairing settings.local.json...")
        setup_settings()

    # 2. Create config if missing
    config_path = project_root / '.claude' / 'config.json'
    if not config_path.exists():
        print("Creating default config.json...")
        config = load_config()  # Gets defaults
        save_config(config)

    # 3. Create directories
    print("\nCreating missing directories...")
    config = load_config()
    create_directories(config)

    # 4. Verify
    print_header("Verification After Repair")
    return verify_only()


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Research System Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 setup.py           # Interactive setup
  python3 setup.py --verify  # Just check, don't modify
  python3 setup.py --repair  # Auto-fix issues

Note: The SessionStart hook handles basic setup automatically,
so this script is OPTIONAL - only needed for customization.
        """
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify setup without making changes'
    )

    parser.add_argument(
        '--repair',
        action='store_true',
        help='Auto-repair issues without prompts'
    )

    args = parser.parse_args()

    try:
        if args.verify:
            success = verify_only()
        elif args.repair:
            success = repair_setup()
        else:
            success = interactive_setup()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup cancelled by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
