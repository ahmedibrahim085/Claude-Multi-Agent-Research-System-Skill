#!/usr/bin/env python3
"""
Incremental Reindex - SIMPLIFIED with IndexFlatIP (MCP's proven approach)

SIMPLIFICATION: Switched from IndexIDMap2 to IndexFlatIP to fix Apple Silicon
compatibility. IndexIDMap2 was added for incremental reindex support, but that
feature was disabled due to bugs. Now using MCP's simpler IndexFlatIP approach.

Architecture:
- Uses MCP's change detection (Merkle tree, ChangeDetector)
- Uses MCP's chunking and embedding
- Uses MCP's IndexFlatIP (works on Apple Silicon, simpler, proven)
- Full reindex only (same as MCP, no incremental updates)
"""

import sys
import json
import hashlib
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional
import time

# Add project utils to path for lock management
# Script location: PROJECT_ROOT/.claude/skills/semantic-search/scripts/incremental_reindex.py
# So __file__.parent.parent.parent.parent.parent = PROJECT_ROOT
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / '.claude' / 'utils'))

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
    from sqlitedict import SqliteDict  # COPIED from MCP for metadata storage
    import faiss
    import numpy as np
except ImportError as e:
    print(json.dumps({
        'success': False,
        'error': f'Failed to import dependencies: {e}',
        'hint': 'Ensure MCP server is installed at ~/.local/share/claude-context-local'
    }, indent=2), file=sys.stderr)
    sys.exit(1)

# Import lock management from reindex_manager
try:
    import reindex_manager
except ImportError as e:
    print(json.dumps({
        'success': False,
        'error': f'Failed to import reindex_manager: {e}'
    }, indent=2), file=sys.stderr)
    sys.exit(1)


class FixedCodeIndexManager:
    """
    Code index manager using IndexFlatIP (MCP's proven, simple approach).

    SIMPLIFIED from IndexIDMap2: Uses direct IndexFlatIP with sequential IDs.
    Works on Apple Silicon, simpler code, same as MCP. Full reindex only.
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
        self.chunk_ids = []    # Ordered list: position = FAISS index, value = chunk_id

        # Embedding cache - NEW: Store embeddings for rebuild without re-embedding
        self.embedding_cache = {}  # chunk_id -> embedding vector (numpy array)
        self.cache_path = self.index_dir / "embeddings.pkl"

        # FAISS index - IndexFlatIP (same as MCP, works on Apple Silicon)
        self.dimension = 768  # embeddinggemma-300m dimension
        self.index = faiss.IndexFlatIP(self.dimension)

        # Load existing index if available
        self._load_index()

    def _load_index(self):
        """
        Load existing index from disk.

        SIMPLIFIED from IndexIDMap2 version - uses IndexFlatIP (MCP's proven approach).
        """
        index_path = self.index_dir / "code.index"
        metadata_path = self.index_dir / "metadata.db"
        chunk_ids_path = self.index_dir / "chunk_ids.pkl"

        if index_path.exists() and metadata_path.exists() and chunk_ids_path.exists():
            try:
                # Load FAISS index
                self.index = faiss.read_index(str(index_path))

                # Load chunk_ids list (ordered by FAISS index position)
                with open(chunk_ids_path, 'rb') as f:
                    self.chunk_ids = pickle.load(f)

                # Load metadata from SqliteDict
                with SqliteDict(str(metadata_path), flag='r') as db:
                    self.metadata_db = {}
                    for chunk_id, entry in db.items():
                        # Store metadata with index_id for reference
                        self.metadata_db[chunk_id] = {
                            'metadata': entry['metadata'],
                            'chunk_id': chunk_id,
                            'faiss_id': entry['index_id']  # Sequential index position
                        }

            except Exception as e:
                print(f"Warning: Failed to load existing index: {e}", file=sys.stderr)

    def save_index(self):
        """
        Save index to disk - SIMPLIFIED for IndexFlatIP.
        """
        # Save FAISS index
        index_path = self.index_dir / "code.index"
        faiss.write_index(self.index, str(index_path))

        # Save metadata.db using SqliteDict
        metadata_path = self.index_dir / "metadata.db"
        with SqliteDict(str(metadata_path), autocommit=False) as db:
            # Clear existing entries for clean save
            db.clear()

            # Write each chunk's metadata with sequential index_id
            for chunk_id, entry in self.metadata_db.items():
                db[chunk_id] = {
                    'index_id': entry['faiss_id'],  # Sequential position in FAISS index
                    'metadata': entry['metadata']
                }

            db.commit()

        # Save chunk_ids.pkl - ordered list matching FAISS index positions
        # Sort by faiss_id to ensure position i in list = FAISS index i
        sorted_entries = sorted(self.metadata_db.items(), key=lambda x: x[1]['faiss_id'])
        chunk_ids_ordered = [chunk_id for chunk_id, _ in sorted_entries]

        chunk_id_path = self.index_dir / "chunk_ids.pkl"
        with open(chunk_id_path, 'wb') as f:
            pickle.dump(chunk_ids_ordered, f)

        # Save stats.json
        self._update_stats()

    def _update_stats(self):
        """
        Update index statistics.

        COPIED from MCP's CodeIndexManager._update_stats() (lines 344-391)
        ADAPTED to work with our IndexIDMap2 metadata structure.
        """
        stats = {
            'total_chunks': len(self.metadata_db),
            'index_size': self.index.ntotal,
            'embedding_dimension': self.dimension,
            'index_type': type(self.index).__name__
        }

        # Count files (COPIED pattern from MCP lines 359-380)
        file_counts = {}
        folder_counts = {}
        chunk_type_counts = {}

        for chunk_id, entry in self.metadata_db.items():
            metadata = entry['metadata']

            # Count by file (ADAPTED: use file_path from our metadata)
            file_path = metadata.get('file_path', metadata.get('relative_path', 'unknown'))
            file_counts[file_path] = file_counts.get(file_path, 0) + 1

            # Count by folder
            for folder in metadata.get('folder_structure', []):
                folder_counts[folder] = folder_counts.get(folder, 0) + 1

            # Count by chunk type
            chunk_type = metadata.get('type', 'unknown')
            chunk_type_counts[chunk_type] = chunk_type_counts.get(chunk_type, 0) + 1

        stats.update({
            'files_indexed': len(file_counts),
            'top_folders': dict(sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            'chunk_types': chunk_type_counts
        })

        # Save stats.json (COPIED from MCP lines 390-391)
        stats_path = self.index_dir / "stats.json"
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)

    def add_embeddings(self, embedding_results):
        """Add embeddings to index - SIMPLIFIED with IndexFlatIP auto-assigned IDs"""
        if not embedding_results:
            return

        vectors = []
        chunk_ids_to_add = []

        # Get starting index (current size of index)
        start_index = self.index.ntotal

        for result in embedding_results:
            chunk_id = result.chunk_id
            vectors.append(result.embedding)
            chunk_ids_to_add.append(chunk_id)

            # Store metadata with sequential index
            self.metadata_db[chunk_id] = {
                'metadata': result.metadata,
                'chunk_id': chunk_id,
                'faiss_id': start_index + len(chunk_ids_to_add) - 1  # Sequential position
            }

        # Add to FAISS - auto-assigns sequential IDs (start_index, start_index+1, ...)
        vectors_array = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(vectors_array)  # Normalize for cosine similarity
        self.index.add(vectors_array)

        # Append chunk_ids to maintain order
        self.chunk_ids.extend(chunk_ids_to_add)

    def clear_index(self):
        """Clear entire index - SIMPLIFIED for IndexFlatIP"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata_db = {}
        self.chunk_ids = []

    def get_index_size(self) -> int:
        """Get number of vectors in index"""
        return self.index.ntotal

    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Search for similar code chunks - SIMPLIFIED for IndexFlatIP.

        Args:
            query_embedding: Query vector (768 dimensions)
            k: Number of results to return
            filters: Optional filters (not implemented yet)

        Returns:
            List of (chunk_id, similarity_score, metadata) tuples
        """
        # Check if index is empty
        if self.index is None or self.index.ntotal == 0:
            return []

        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)

        # Search in FAISS index
        search_k = min(k * 3, self.index.ntotal)
        similarities, indices = self.index.search(query_embedding, search_k)

        results = []
        for similarity, index in zip(similarities[0], indices[0]):
            if index == -1:  # No more results
                break

            # SIMPLIFIED: Direct array lookup (index is position in chunk_ids list)
            index = int(index)
            if index >= len(self.chunk_ids):
                continue  # Skip if index out of bounds

            chunk_id = self.chunk_ids[index]

            # Get metadata
            if chunk_id not in self.metadata_db:
                continue

            metadata = self.metadata_db[chunk_id]['metadata']

            results.append((chunk_id, float(similarity), metadata))

            if len(results) >= k:
                break

        return results

    def find_similar(
        self,
        chunk_id: str,
        k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[tuple]:
        """
        Find similar chunks to a given chunk - SIMPLIFIED for IndexFlatIP.

        Args:
            chunk_id: ID of the chunk to find similar chunks for
            k: Number of results to return
            filters: Optional filters

        Returns:
            List of (chunk_id, similarity_score, metadata) tuples
        """
        # Get index for this chunk from metadata
        if chunk_id not in self.metadata_db:
            return []

        faiss_index = self.metadata_db[chunk_id]['faiss_id']

        # Reconstruct vector from FAISS
        try:
            vector = self.index.reconstruct(int(faiss_index))
        except Exception:
            return []

        # Search with this vector
        all_results = self.search(vector, k=k+1, filters=filters)  # +1 to account for self

        # Filter out the source chunk itself
        results = [(cid, score, meta) for cid, score, meta in all_results if cid != chunk_id]

        return results[:k]

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict]:
        """
        Get metadata for a specific chunk.

        COPIED pattern from MCP's CodeIndexManager.get_chunk_by_id()

        Args:
            chunk_id: Chunk ID to retrieve

        Returns:
            Metadata dict or None if not found
        """
        if chunk_id not in self.metadata_db:
            return None

        entry = self.metadata_db[chunk_id]
        return entry.get('metadata')


class FixedIncrementalIndexer:
    """
    Incremental indexer using the fixed IndexManager.

    Extracts MCP's change detection logic but uses our fixed index manager
    to avoid the incremental update bug.
    """

    def __init__(self, project_path: str):
        project_path_obj = Path(project_path).resolve()
        self.project_path = str(project_path_obj)
        self.project_name = project_path_obj.name  # FIX: Use resolved path to get correct name

        # Initialize components
        self.indexer = FixedCodeIndexManager(self.project_path)
        self.embedder = CodeEmbedder()
        self.chunker = MultiLanguageChunker(self.project_path)
        self.snapshot_manager = SnapshotManager()
        self.change_detector = ChangeDetector(self.snapshot_manager)

    def needs_reindex(self, max_age_minutes: float = 360) -> bool:
        """Check if reindex is needed based on age"""
        if not self.snapshot_manager.has_snapshot(self.project_path):
            return True

        age = self.snapshot_manager.get_snapshot_age(self.project_path)
        if age and age > max_age_minutes * 60:
            return True

        return self.change_detector.quick_check(self.project_path)

    def _record_index_timestamp(self, is_full_index: bool):
        """Record timestamp after successful index operation"""
        try:
            from datetime import datetime, timezone
            import hashlib

            storage_dir = Path.home() / '.claude_code_search'
            project_path_obj = Path(self.project_path).resolve()
            project_hash = hashlib.md5(str(project_path_obj).encode()).hexdigest()[:8]
            project_dir = storage_dir / 'projects' / f'{self.project_name}_{project_hash}'
            state_file = project_dir / 'index_state.json'

            # Read existing state if it exists
            state = {}
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)

            # Update timestamps
            timestamp = datetime.now(timezone.utc).isoformat()
            if is_full_index:
                state['last_full_index'] = timestamp
            state['last_incremental_index'] = timestamp
            state['project_path'] = str(project_path_obj)

            # Write state
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            # Don't fail indexing if state recording fails
            print(f"Warning: Failed to record index timestamp: {e}", file=sys.stderr)

    def _update_prerequisites_state_after_successful_reindex(self):
        """Update prerequisites state after successful full reindex

        Design Rationale:
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        - Conservative approach: Only update if index actually exists
        - Respects manual_override: Don't update if user manually set state
        - Graceful failure: Don't break indexing if state update fails
        - Closes architectural gap: Hooks were skipping indexing even after
          successful reindex because prerequisites stayed FALSE forever

        Context:
        - Prerequisites file: logs/state/semantic-search-prerequisites.json
        - Read by: reindex_manager.read_prerequisites_state() (hooks use this)
        - Previously ONLY updated by: scripts/check-prerequisites (manual)
        - Gap: After successful reindex, prerequisites never auto-recovered

        Logic:
        1. Verify index file actually exists (conservative check)
        2. Read existing prerequisites state
        3. If manual_override=true → Skip (respect user's manual setting)
        4. Update SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY = true
        5. Update last_checked timestamp
        6. Preserve other state fields

        Args:
            None (uses self.project_path, self.project_name)

        Returns:
            None (prints warning on failure, never raises)
        """
        try:
            from datetime import datetime, timezone
            import hashlib

            # Step 1: Verify index file exists (conservative check)
            storage_dir = Path.home() / '.claude_code_search'
            project_path_obj = Path(self.project_path).resolve()
            project_hash = hashlib.md5(str(project_path_obj).encode()).hexdigest()[:8]
            project_dir = storage_dir / 'projects' / f'{self.project_name}_{project_hash}'
            index_file = project_dir / 'index' / 'code.index'

            if not index_file.exists():
                # Index doesn't exist - don't update prerequisites
                # This should never happen here (called after successful reindex)
                # but being conservative
                return

            # Step 2: Locate prerequisites state file
            prerequisites_state_file = project_path_obj / 'logs' / 'state' / 'semantic-search-prerequisites.json'

            # Step 3: Read existing state (if it exists)
            state = {}
            if prerequisites_state_file.exists():
                try:
                    with open(prerequisites_state_file, 'r') as f:
                        state = json.load(f)
                except Exception:
                    # If file is corrupted, create fresh state
                    state = {}

            # Step 4: Check manual_override - RESPECT user's manual setting
            if state.get('manual_override', False):
                # User manually set state - don't auto-update
                # Silently skip (user explicitly disabled auto-updates)
                return

            # Step 5: Update prerequisites to TRUE
            # Rationale: If full reindex succeeded, core prerequisites must be met
            # (Python libs, dependencies, model, etc. all worked)
            timestamp = datetime.now(timezone.utc).isoformat()

            state['SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY'] = True
            state['last_checked'] = timestamp
            state['last_check_details'] = {
                'total_checks': 1,
                'passed': 1,
                'failed': 0,
                'warnings': 0
            }
            state['manual_override'] = False
            state['notes'] = 'This file tracks semantic-search skill prerequisites status. Set manual_override to true and SEMANTIC_SEARCH_SKILL_PREREQUISITES_READY to true/false to prevent auto-updates. Run scripts/check-prerequisites to auto-update.'

            # Step 6: Write updated state
            prerequisites_state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(prerequisites_state_file, 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            # Don't fail indexing if prerequisites state update fails
            # This is a convenience feature, not critical
            print(f"Warning: Failed to update prerequisites state: {e}", file=sys.stderr)

    def auto_reindex(self, force_full: bool = False):
        """Auto-reindex with IndexFlatIP (always full reindex when called)

        IndexFlatIP Limitation:
        - Uses sequential IDs (0, 1, 2...) - no selective deletion supported
        - Only full reindex possible (clear entire index + rebuild)

        Design:
        - ALWAYS does full reindex when called (3-10 minutes for ~6,000 chunks)
        - Change detection happens in needs_reindex(), not here
        - This function is called only when reindex is needed

        Logic:
        1. If IndexFlatIP detected → force full reindex (always true in current implementation)
        2. If no snapshot exists → force full reindex (first time)
        3. Execute full reindex (clear entire index + rebuild)

        Note: The IndexFlatIP check (line 427-428) makes this function always do full reindex,
        regardless of force_full parameter. Change detection to skip unnecessary reindex
        happens at the caller level (needs_reindex()).
        """
        start_time = time.time()

        try:
            # IndexFlatIP only supports full reindex (no selective deletion)
            # Auto-fallback: Detect this and force full reindex
            if isinstance(self.indexer.index, faiss.IndexFlatIP):
                force_full = True

            # If no snapshot exists, must do full reindex (first time)
            if not self.snapshot_manager.has_snapshot(self.project_path):
                force_full = True

            # If force_full requested, do full reindex immediately
            # Note: With IndexFlatIP, this is always True (lines 427-428), so we always reach here
            if force_full:
                return self._full_index(start_time)

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time_taken': round(time.time() - start_time, 2)
            }

    def _full_index(self, start_time: float):
        """Perform full indexing"""
        try:
            # === BENCHMARKING: Track timing for each phase ===
            timings = {}
            phase_start = time.time()

            # Clear existing
            print("Clearing existing index...", file=sys.stderr)
            self.indexer.clear_index()
            timings['clear_index'] = time.time() - phase_start

            # Build DAG
            phase_start = time.time()
            print("Building file DAG...", file=sys.stderr)
            dag = MerkleDAG(self.project_path)
            dag.build()
            all_files = dag.get_all_files()
            timings['dag_build'] = time.time() - phase_start

            # Filter supported files
            phase_start = time.time()
            supported_files = [f for f in all_files if self.chunker.is_supported(f)]
            timings['file_filtering'] = time.time() - phase_start
            print(f"Found {len(supported_files)}/{len(all_files)} supported files", file=sys.stderr)

            # Chunk all files
            phase_start = time.time()
            print(f"Chunking {len(supported_files)} files...", file=sys.stderr)
            all_chunks = []
            for idx, file_path in enumerate(supported_files, 1):
                full_path = Path(self.project_path) / file_path
                try:
                    chunks = self.chunker.chunk_file(str(full_path))
                    if chunks:
                        all_chunks.extend(chunks)
                    # Progress every 50 files
                    if idx % 50 == 0:
                        print(f"  Chunked {idx}/{len(supported_files)} files ({len(all_chunks)} chunks so far)...", file=sys.stderr)
                except Exception as e:
                    print(f"Warning: Failed to chunk {file_path}: {e}", file=sys.stderr)
            timings['chunking'] = time.time() - phase_start
            print(f"Chunking complete: {len(all_chunks)} chunks from {len(supported_files)} files", file=sys.stderr)

            # Embed all chunks
            all_embedding_results = []
            if all_chunks:
                try:
                    # Use larger batch size (64) for better GPU utilization
                    # MCP default is 32, but modern GPUs can handle more
                    batch_size = 64
                    phase_start = time.time()
                    print(f"Generating embeddings for {len(all_chunks)} chunks (batch_size={batch_size})...", file=sys.stderr)
                    all_embedding_results = self.embedder.embed_chunks(all_chunks, batch_size=batch_size)
                    timings['embedding'] = time.time() - phase_start
                    print(f"Embedding complete: {len(all_embedding_results)} embeddings generated", file=sys.stderr)

                    # Add metadata (project_name + content)
                    phase_start = time.time()
                    for chunk, embedding_result in zip(all_chunks, all_embedding_results):
                        embedding_result.metadata['project_name'] = self.project_name
                        embedding_result.metadata['content'] = chunk.content
                    timings['metadata_add'] = time.time() - phase_start
                except Exception as e:
                    print(f"Warning: Embedding failed: {e}", file=sys.stderr)

            # Add to index
            if all_embedding_results:
                phase_start = time.time()
                print(f"Adding {len(all_embedding_results)} embeddings to FAISS index...", file=sys.stderr)
                self.indexer.add_embeddings(all_embedding_results)
                timings['faiss_add'] = time.time() - phase_start

            # Save snapshot
            phase_start = time.time()
            print("Saving Merkle DAG snapshot...", file=sys.stderr)
            self.snapshot_manager.save_snapshot(dag, {
                'project_name': self.project_name,
                'full_index': True,
                'total_files': len(all_files),
                'supported_files': len(supported_files),
                'chunks_indexed': len(all_embedding_results)
            })
            timings['snapshot_save'] = time.time() - phase_start

            # Save index
            phase_start = time.time()
            print("Saving FAISS index to disk...", file=sys.stderr)
            self.indexer.save_index()
            timings['index_save'] = time.time() - phase_start

            # Record timestamp
            self._record_index_timestamp(is_full_index=True)

            # Update prerequisites state (auto-recovery after successful reindex)
            self._update_prerequisites_state_after_successful_reindex()

            # === BENCHMARKING: Print timing breakdown ===
            total_time = time.time() - start_time
            print("\n" + "="*60, file=sys.stderr)
            print("PERFORMANCE BREAKDOWN", file=sys.stderr)
            print("="*60, file=sys.stderr)
            print(f"{'Phase':<20} {'Time (s)':>10} {'% Total':>10}", file=sys.stderr)
            print("-"*60, file=sys.stderr)
            for phase_name, phase_time in sorted(timings.items(), key=lambda x: -x[1]):
                pct = (phase_time / total_time) * 100
                print(f"{phase_name:<20} {phase_time:>10.2f} {pct:>9.1f}%", file=sys.stderr)
            print("-"*60, file=sys.stderr)
            print(f"{'TOTAL':<20} {total_time:>10.2f} {'100.0%':>10}", file=sys.stderr)
            print("="*60, file=sys.stderr)
            print(f"\n✓ Full reindex complete: {len(all_embedding_results)} chunks indexed", file=sys.stderr)

            return {
                'success': True,
                'full_index': True,
                'files_indexed': len(supported_files),
                'chunks_added': len(all_embedding_results),
                'total_chunks': self.indexer.get_index_size(),
                'time_taken': round(time.time() - start_time, 2),
                'timing_breakdown': timings  # Include detailed timings in result
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time_taken': round(time.time() - start_time, 2)
            }

def main():
    """Main entry point with lock management"""
    import argparse
    from datetime import datetime, timezone

    parser = argparse.ArgumentParser(
        description='Incremental reindex with IndexFlatIP (auto-fallback to full reindex)'
    )
    parser.add_argument('project_path', help='Path to project directory')
    parser.add_argument('--full', action='store_true', help='Force full reindex')
    parser.add_argument('--max-age', type=float, default=360,
                       help='Max age in minutes before auto-reindex (default: 360)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check if reindex is needed, don\'t execute')

    args = parser.parse_args()
    project_path = Path(args.project_path).resolve()

    # Track operation for logging
    operation_id = None
    start_time = datetime.now(timezone.utc).isoformat()
    result = None
    exit_code = 0

    # CRITICAL: Acquire lock to prevent concurrent reindex
    # If lock held by another process, exit immediately with "skipped" status
    # Use kill_if_held=False to skip (not kill) if another reindex is running
    lock_acquired = reindex_manager._acquire_reindex_lock(project_path, kill_if_held=False)

    if not lock_acquired:
        # Another reindex is running, skip silently (no logging needed - parent already logged skip)
        result = {
            'success': True,
            'skipped': True,
            'reason': 'Another reindex process is running',
            'time_taken': 0
        }
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Lock acquired - log operation start (for background processes, parent already logged)
    # But log here too for manual invocations or if parent logging failed
    operation_id = reindex_manager.log_reindex_start(
        trigger='script-direct',  # Will be overridden by parent's log if spawned
        mode='background',
        pid=os.getpid(),
        kill_if_held=False,
        skipped=False
    )

    # Lock acquired - proceed with reindex
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
                result = indexer.auto_reindex(force_full=args.full)

        print(json.dumps(result, indent=2))
        exit_code = 0 if result.get('success', True) else 1

    except Exception as e:
        result = {
            'success': False,
            'error': str(e)
        }
        print(json.dumps(result, indent=2), file=sys.stderr)
        exit_code = 1

    finally:
        # Log operation end (NEW: Forensic diagnostics)
        if operation_id and start_time:
            status = 'completed' if exit_code == 0 else 'failed'
            index_updated = result and result.get('success', False) and not result.get('skipped', False)
            files_changed = result.get('files_changed') if result else None
            error_message = result.get('error') if result and not result.get('success', False) else None

            reindex_manager.log_reindex_end(
                operation_id=operation_id,
                start_timestamp=start_time,
                status=status,
                exit_code=exit_code,
                index_updated=index_updated,
                files_changed=files_changed,
                error_message=error_message
            )

        # CRITICAL: Always release lock, even if reindex failed
        reindex_manager._release_reindex_lock(project_path)

        sys.exit(exit_code)


if __name__ == '__main__':
    main()
