#!/usr/bin/env python3
"""Get code search index status and statistics."""

import sys
from pathlib import Path

# Add scripts directory to path for utils import (CC#1)
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

import argparse
from utils import setup, error_exit, success

def main():
    """Retrieve index status and statistics."""
    _, CodeIndexManager = setup()

    parser = argparse.ArgumentParser(description="Get index status")
    parser.add_argument('--storage-dir', type=Path,
                        default=Path.cwd() / ".code-search-index",
                        help='Index storage directory')
    args = parser.parse_args()

    try:
        manager = CodeIndexManager(storage_dir=str(args.storage_dir))
        stats = manager.get_stats()
        success(stats)
    except FileNotFoundError:
        error_exit("Index not found",
                   suggestion="Project not indexed. Run index_codebase.py first",
                   path=str(args.storage_dir))
    except Exception as e:
        error_exit(str(e))

if __name__ == "__main__":
    main()
