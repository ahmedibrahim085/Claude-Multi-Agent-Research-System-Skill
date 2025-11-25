#!/usr/bin/env python3
"""
Configuration Loader

Loads configuration from .claude/config.json with environment variable overrides.
Provides sensible defaults if config file doesn't exist.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json with environment variable overrides.

    Priority:
    1. Environment variables (highest)
    2. config.json values
    3. Hardcoded defaults (lowest)
    """

    # Default configuration
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
        },
        "file_naming": {
            "research_note_format": "{subtopic-slug}.md",
            "report_format": "{topic-slug}_{timestamp}.md",
            "timestamp_format": "%Y%m%d-%H%M%S"
        }
    }

    # Try to load from config.json
    config_path = Path('.claude/config.json')
    if config_path.exists():
        try:
            with config_path.open('r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Merge with defaults (file config overrides defaults)
                config = {**default_config, **file_config}
        except (json.JSONDecodeError, IOError):
            config = default_config
    else:
        config = default_config

    # Environment variable overrides (highest priority)
    env_overrides = {
        'RESEARCH_NOTES_DIR': ('paths', 'research_notes'),
        'REPORTS_DIR': ('paths', 'reports'),
        'LOGS_DIR': ('paths', 'logs'),
        'STATE_DIR': ('paths', 'state'),
        'MAX_PARALLEL_RESEARCHERS': ('research', 'max_parallel_researchers'),
        'LOGGING_ENABLED': ('logging', 'enabled'),
    }

    for env_var, (section, key) in env_overrides.items():
        value = os.getenv(env_var)
        if value is not None:
            # Type conversion for specific keys
            if key in ['max_parallel_researchers']:
                value = int(value)
            elif key in ['enabled', 'log_tool_calls', 'require_synthesis_delegation', 'quality_gates_enabled']:
                value = value.lower() in ('true', '1', 'yes')

            config[section][key] = value

    return config


def get_path(path_type: str) -> str:
    """Get a configured path by type (research_notes, reports, logs, state)"""
    config = load_config()
    return config['paths'].get(path_type, f'files/{path_type}')


def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration"""
    config = load_config()
    return config.get('logging', {})


def get_research_config() -> Dict[str, Any]:
    """Get research configuration"""
    config = load_config()
    return config.get('research', {})
