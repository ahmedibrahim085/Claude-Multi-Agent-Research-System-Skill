#!/usr/bin/env python3
"""
Incremental Reindex - Fixed version with IndexIDMap2

This script provides incremental indexing with proper vector removal support
by using FAISS IndexIDMap2 wrapper. It extracts working code from MCP and
adds the IndexIDMap2 fix to prevent the "list index out of range" bug.

Architecture:
- Uses MCP's change detection (Merkle tree, ChangeDetector)
- Uses MCP's chunking and embedding
- Implements FIXED IndexManager with IndexIDMap2
- Implements FIXED IncrementalIndexer using the fixed manager
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import time

# Add MCP to path
sys.path.insert(0, str(Path.home() / ".local/share/claude-context-local"))

# Import working MCP components
try:
    from merkle.merkle_dag import MerkleDAG
    from merkle.change_detector import ChangeDetector, FileChanges
    from merkle.snapshot_manager import SnapshotManager
    from chunking.multi_language_chunker import MultiLanguageChunker
    from embeddings.embedder import CodeEmbedder
    from common_utils import get_storage_dir
    import faiss
    import numpy as np
except ImportError as e:
    print(json.dumps({
        'success': False,
        'error': f'Failed to import dependencies: {e}',
        'hint': 'Ensure MCP server is installed at ~/.local/share/claude-context-local'
    }, indent=2), file=sys.stderr)
    sys.exit(1)


class FixedCodeIndexManager:
    """
    Fixed index manager using IndexIDMap2 for proper removal support.

    KEY FIX: Wraps IndexFlatIP with IndexIDMap2 to enable remove_ids()
    without ID shifting. This fixes the MCP bug where metadata and FAISS
    become desynchronized during incremental updates.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_name = self.project_path.name

        # Storage paths
        storage_dir = get_storage_dir()
        project_hash = hashlib.md5(str(self.project_path).encode()).hexdigest()[:8]
        self.index_dir = storage_dir / "projects" / f"{self.project_name}_{project_hash}" / "index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # Metadata storage
        self.metadata_db = {}  # chunk_id -> metadata
        self.id_mapping = {}   # chunk_id -> int64_id
        self.next_id = 0       # Counter for new IDs

        # FAISS index with IndexIDMap2 wrapper (THE FIX)
        self.dimension = 768  # embeddinggemma-300m dimension
        base_index = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap2(base_index)

        # Load existing index if available
        self._load_index()

    def _load_index(self):
        """Load existing index from disk"""
        index_path = self.index_dir / "code.index"
        metadata_path = self.index_dir / "metadata.json"

        if index_path.exists() and metadata_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                with open(metadata_path) as f:
                    data = json.load(f)
                    self.metadata_db = data.get('metadata', {})
                    self.id_mapping = {k: int(v) for k, v in data.get('id_mapping', {}).items()}
                    self.next_id = data.get('next_id', 0)
            except Exception as e:
                print(f"Warning: Failed to load existing index: {e}", file=sys.stderr)

    def save_index(self):
        """Save index to disk"""
        index_path = self.index_dir / "code.index"
        metadata_path = self.index_dir / "metadata.json"

        faiss.write_index(self.index, str(index_path))

        with open(metadata_path, 'w') as f:
            json.dump({
                'metadata': self.metadata_db,
                'id_mapping': self.id_mapping,
                'next_id': self.next_id
            }, f)

    def add_embeddings(self, embedding_results):
        """Add embeddings to index with stable IDs"""
        if not embedding_results:
            return

        vectors = []
        ids = []

        for result in embedding_results:
            chunk_id = result.chunk_id

            # Assign new ID if not exists
            if chunk_id not in self.id_mapping:
                self.id_mapping[chunk_id] = self.next_id
                self.next_id += 1

            faiss_id = self.id_mapping[chunk_id]

            vectors.append(result.embedding)
            ids.append(faiss_id)

            # Store metadata
            self.metadata_db[chunk_id] = {
                'metadata': result.metadata,
                'chunk_id': chunk_id,
                'faiss_id': faiss_id
            }

        # Add to FAISS
        vectors_array = np.array(vectors, dtype=np.float32)
        ids_array = np.array(ids, dtype=np.int64)
        self.index.add_with_ids(vectors_array, ids_array)

    def remove_file_chunks(self, file_path: str, project_name: Optional[str] = None) -> int:
        """
        Remove all chunks from a specific file.

        NOW WORKS PROPERLY: Uses IndexIDMap2.remove_ids() to actually
        remove vectors from FAISS, preventing metadata/FAISS desync.
        """
        chunks_to_remove = []
        ids_to_remove = []

        # Find chunks to remove
        for chunk_id, metadata_entry in list(self.metadata_db.items()):
            metadata = metadata_entry['metadata']
            chunk_file = metadata.get('file_path') or metadata.get('relative_path')

            if chunk_file and (file_path in chunk_file or chunk_file in file_path):
                if project_name and metadata.get('project_name') != project_name:
                    continue

                chunks_to_remove.append(chunk_id)
                if chunk_id in self.id_mapping:
                    ids_to_remove.append(self.id_mapping[chunk_id])

        # Remove from FAISS using IndexIDMap2 (THE FIX WORKS HERE)
        if ids_to_remove:
            ids_array = np.array(ids_to_remove, dtype=np.int64)
            self.index.remove_ids(ids_array)

        # Remove from metadata and ID mapping
        for chunk_id in chunks_to_remove:
            del self.metadata_db[chunk_id]
            if chunk_id in self.id_mapping:
                del self.id_mapping[chunk_id]

        return len(chunks_to_remove)

    def clear_index(self):
        """Clear entire index"""
        base_index = faiss.IndexFlatIP(self.dimension)
        self.index = faiss.IndexIDMap2(base_index)
        self.metadata_db = {}
        self.id_mapping = {}
        self.next_id = 0

    def get_index_size(self) -> int:
        """Get number of vectors in index"""
        return self.index.ntotal


class FixedIncrementalIndexer:
    """
    Incremental indexer using the fixed IndexManager.

    Extracts MCP's change detection logic but uses our fixed index manager
    to avoid the incremental update bug.
    """

    def __init__(self, project_path: str):
        self.project_path = str(Path(project_path).resolve())
        self.project_name = Path(project_path).name

        # Initialize components
        self.indexer = FixedCodeIndexManager(self.project_path)
        self.embedder = CodeEmbedder()
        self.chunker = MultiLanguageChunker(self.project_path)
        self.snapshot_manager = SnapshotManager()
        self.change_detector = ChangeDetector(self.snapshot_manager)

    def needs_reindex(self, max_age_minutes: float = 60) -> bool:
        """Check if reindex is needed based on age"""
        if not self.snapshot_manager.has_snapshot(self.project_path):
            return True

        age = self.snapshot_manager.get_snapshot_age(self.project_path)
        if age and age > max_age_minutes * 60:
            return True

        return self.change_detector.quick_check(self.project_path)

    def incremental_index(self, force_full: bool = False):
        """Perform incremental indexing with proper removal support"""
        start_time = time.time()

        try:
            # Check if we should do full index
            if force_full or not self.snapshot_manager.has_snapshot(self.project_path):
                return self._full_index(start_time)

            # Detect changes using Merkle tree
            changes, current_dag = self.change_detector.detect_changes_from_snapshot(self.project_path)

            if not changes.has_changes():
                return {
                    'success': True,
                    'no_changes': True,
                    'time_taken': round(time.time() - start_time, 2)
                }

            # Process changes (now with working remove_file_chunks!)
            chunks_removed = self._remove_old_chunks(changes)
            chunks_added = self._add_new_chunks(changes)

            # Update snapshot
            self.snapshot_manager.save_snapshot(current_dag, {
                'project_name': self.project_name,
                'incremental_update': True,
                'files_added': len(changes.added),
                'files_removed': len(changes.removed),
                'files_modified': len(changes.modified)
            })

            # Save index
            self.indexer.save_index()

            return {
                'success': True,
                'incremental': True,
                'files_added': len(changes.added),
                'files_removed': len(changes.removed),
                'files_modified': len(changes.modified),
                'chunks_added': chunks_added,
                'chunks_removed': chunks_removed,
                'total_chunks': self.indexer.get_index_size(),
                'time_taken': round(time.time() - start_time, 2)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time_taken': round(time.time() - start_time, 2)
            }

    def _full_index(self, start_time: float):
        """Perform full indexing"""
        try:
            # Clear existing
            self.indexer.clear_index()

            # Build DAG
            dag = MerkleDAG(self.project_path)
            dag.build()
            all_files = dag.get_all_files()

            # Filter supported files
            supported_files = [f for f in all_files if self.chunker.is_supported(f)]

            # Chunk all files
            all_chunks = []
            for file_path in supported_files:
                full_path = Path(self.project_path) / file_path
                try:
                    chunks = self.chunker.chunk_file(str(full_path))
                    if chunks:
                        all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Warning: Failed to chunk {file_path}: {e}", file=sys.stderr)

            # Embed all chunks
            all_embedding_results = []
            if all_chunks:
                try:
                    all_embedding_results = self.embedder.embed_chunks(all_chunks)
                    for chunk, embedding_result in zip(all_chunks, all_embedding_results):
                        embedding_result.metadata['project_name'] = self.project_name
                        embedding_result.metadata['content'] = chunk.content
                except Exception as e:
                    print(f"Warning: Embedding failed: {e}", file=sys.stderr)

            # Add to index
            if all_embedding_results:
                self.indexer.add_embeddings(all_embedding_results)

            # Save snapshot
            self.snapshot_manager.save_snapshot(dag, {
                'project_name': self.project_name,
                'full_index': True,
                'total_files': len(all_files),
                'supported_files': len(supported_files),
                'chunks_indexed': len(all_embedding_results)
            })

            # Save index
            self.indexer.save_index()

            return {
                'success': True,
                'full_index': True,
                'files_indexed': len(supported_files),
                'chunks_added': len(all_embedding_results),
                'total_chunks': self.indexer.get_index_size(),
                'time_taken': round(time.time() - start_time, 2)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time_taken': round(time.time() - start_time, 2)
            }

    def _remove_old_chunks(self, changes: FileChanges) -> int:
        """Remove chunks for deleted and modified files"""
        files_to_remove = changes.removed + changes.modified
        chunks_removed = 0

        for file_path in files_to_remove:
            removed = self.indexer.remove_file_chunks(file_path, self.project_name)
            chunks_removed += removed

        return chunks_removed

    def _add_new_chunks(self, changes: FileChanges) -> int:
        """Add chunks for new and modified files"""
        files_to_index = changes.added + changes.modified
        supported_files = [f for f in files_to_index if self.chunker.is_supported(f)]

        chunks_to_embed = []
        for file_path in supported_files:
            full_path = Path(self.project_path) / file_path
            try:
                chunks = self.chunker.chunk_file(str(full_path))
                if chunks:
                    chunks_to_embed.extend(chunks)
            except Exception as e:
                print(f"Warning: Failed to chunk {file_path}: {e}", file=sys.stderr)

        all_embedding_results = []
        if chunks_to_embed:
            try:
                all_embedding_results = self.embedder.embed_chunks(chunks_to_embed)
                for chunk, embedding_result in zip(chunks_to_embed, all_embedding_results):
                    embedding_result.metadata['project_name'] = self.project_name
                    embedding_result.metadata['content'] = chunk.content
            except Exception as e:
                print(f"Warning: Embedding failed: {e}", file=sys.stderr)

        if all_embedding_results:
            self.indexer.add_embeddings(all_embedding_results)

        return len(all_embedding_results)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Incremental reindex with IndexIDMap2 fix'
    )
    parser.add_argument('project_path', help='Path to project directory')
    parser.add_argument('--full', action='store_true', help='Force full reindex')
    parser.add_argument('--max-age', type=float, default=60,
                       help='Max age in minutes before auto-reindex (default: 60)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check if reindex is needed, don\'t execute')

    args = parser.parse_args()

    try:
        indexer = FixedIncrementalIndexer(args.project_path)

        if args.check_only:
            needs_reindex = indexer.needs_reindex(args.max_age)
            result = {
                'needs_reindex': needs_reindex,
                'max_age_minutes': args.max_age
            }
        else:
            # Check if reindex needed (unless --full forced)
            if not args.full and not indexer.needs_reindex(args.max_age):
                result = {
                    'success': True,
                    'skipped': True,
                    'reason': f'Index age < {args.max_age} minutes',
                    'time_taken': 0
                }
            else:
                result = indexer.incremental_index(force_full=args.full)

        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get('success', True) else 1)

    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
