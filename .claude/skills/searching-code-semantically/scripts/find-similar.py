#!/usr/bin/env python3
"""Find code chunks similar to a reference chunk."""

import sys
from pathlib import Path

# Add scripts directory to path for utils import (CC#1)
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))

import argparse
from utils import setup, error_exit, success

def main():
    """Find similar code chunks by chunk ID."""
    IntelligentSearcher, _ = setup()

    parser = argparse.ArgumentParser(description="Find similar code chunks")
    parser.add_argument('--chunk-id', required=True, help='Reference chunk ID')
    parser.add_argument('--k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--storage-dir', type=Path,
                        default=Path.cwd() / ".code-search-index",
                        help='Index storage directory')
    args = parser.parse_args()

    try:
        searcher = IntelligentSearcher(storage_dir=str(args.storage_dir))
        results = searcher.find_similar_to_chunk(chunk_id=args.chunk_id, k=args.k)
        success(results)
    except FileNotFoundError:
        error_exit("Index not found", suggestion="Check storage-dir path")
    except Exception as e:
        error_exit(str(e))

if __name__ == "__main__":
    main()
