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
    IntelligentSearcher, CodeIndexManager = setup()

    # Import CodeEmbedder
    import sys
    from pathlib import Path
    INSTALL_DIR = Path.home() / ".local" / "share" / "claude-context-local"
    sys.path.insert(0, str(INSTALL_DIR))
    from embeddings.embedder import CodeEmbedder

    parser = argparse.ArgumentParser(description="Search code semantically")
    parser.add_argument('--query', required=True, help='Natural language search query')
    parser.add_argument('--k', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--storage-dir', type=Path,
                        default=Path.cwd() / ".code-search-index",
                        help='Index storage directory')
    args = parser.parse_args()

    try:
        # Create index manager and embedder
        index_manager = CodeIndexManager(storage_dir=str(args.storage_dir))
        embedder = CodeEmbedder()  # Uses default model

        # Create searcher with required dependencies
        searcher = IntelligentSearcher(index_manager=index_manager, embedder=embedder)

        # Perform search
        results = searcher.search(query=args.query, k=args.k)

        # Format results for output
        formatted_results = {
            "query": args.query,
            "k": args.k,
            "results": results
        }
        success(formatted_results)
    except FileNotFoundError as e:
        error_exit("Index not found",
                   suggestion="Run indexing first or check storage-dir path",
                   path=str(args.storage_dir))
    except Exception as e:
        error_exit(str(e), suggestion="Verify index integrity and global installation")

if __name__ == "__main__":
    main()
