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
    IntelligentSearcher, CodeIndexManager = setup()

    # Import CodeEmbedder
    import sys
    from pathlib import Path
    INSTALL_DIR = Path.home() / ".local" / "share" / "claude-context-local"
    sys.path.insert(0, str(INSTALL_DIR))
    from embeddings.embedder import CodeEmbedder

    parser = argparse.ArgumentParser(description="Find similar code chunks")
    parser.add_argument('--chunk-id', required=True, help='Reference chunk ID')
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

        # Find similar chunks
        results = searcher.find_similar_to_chunk(chunk_id=args.chunk_id, k=args.k)

        # Format results for output
        formatted_results = {
            "chunk_id": args.chunk_id,
            "k": args.k,
            "results": results
        }
        success(formatted_results)
    except FileNotFoundError:
        error_exit("Index not found", suggestion="Check storage-dir path")
    except Exception as e:
        error_exit(str(e))

if __name__ == "__main__":
    main()
