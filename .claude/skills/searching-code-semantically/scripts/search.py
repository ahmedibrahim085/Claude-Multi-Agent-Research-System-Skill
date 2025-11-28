#!/usr/bin/env python3
"""Search code semantically using natural language queries."""

import sys
from pathlib import Path

# Add scripts directory to path for utils import (CC#1)
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

import argparse
from utils import setup, error_exit, success

def main():
    """Execute semantic code search."""
    IntelligentSearcher, _ = setup()

    parser = argparse.ArgumentParser(description="Search code semantically")
    parser.add_argument('--query', required=True, help='Natural language search query')
    parser.add_argument('--k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--storage-dir', type=Path,
                        default=Path.cwd() / ".code-search-index",
                        help='Index storage directory')
    args = parser.parse_args()

    try:
        searcher = IntelligentSearcher(storage_dir=str(args.storage_dir))
        results = searcher.search(query=args.query, k=args.k)
        success(results)
    except FileNotFoundError as e:
        error_exit("Index not found",
                   suggestion="Run indexing first or check storage-dir path",
                   path=str(args.storage_dir))
    except Exception as e:
        error_exit(str(e), suggestion="Verify index integrity and global installation")

if __name__ == "__main__":
    main()
