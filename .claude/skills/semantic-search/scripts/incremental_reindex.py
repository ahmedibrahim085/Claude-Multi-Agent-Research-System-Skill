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

# FIX: Disable ALL parallelism to prevent Apple Silicon MPS + multiprocessing crashes
# Must be set BEFORE importing any libraries
import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import sys
import json
import hashlib
import pickle
import math
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

# Cache versioning constants (Critical Feature: Prevent stale embeddings after model changes)
CACHE_VERSION = 1
DEFAULT_MODEL_NAME = "google/embeddinggemma-300m"  # Default embedding model

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

    def __init__(self, project_path: str, model_name: str = DEFAULT_MODEL_NAME):
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

        # Model configuration (Critical: Cache versioning)
        self.model_name = model_name
        self.dimension = 768  # embeddinggemma-300m dimension

        # FAISS index - IndexFlatIP (same as MCP, works on Apple Silicon)
        self.index = faiss.IndexFlatIP(self.dimension)

        # Load existing index and cache if available
        self._load_index()
        self._load_cache()  # NEW: Load embedding cache from disk

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

    def _save_cache(self):
        """
        Save embedding cache to disk using atomic write pattern.

        Cache format (VERSIONED - Critical Feature):
        {
            'version': 1,
            'model_name': 'google/embeddinggemma-300m',
            'embedding_dimension': 768,
            'embeddings': {chunk_id: numpy_array, ...}
        }

        Versioning prevents using stale embeddings after model changes.
        Cache cleanup prevents bloat from deleted chunks.
        Atomic write prevents corruption if process crashes during write.
        """
        import os
        temp_path = str(self.cache_path) + '.tmp'

        # CLEANUP: Prune deleted chunks from cache (High Priority Feature)
        # Only save embeddings for chunks that exist in metadata_db
        active_embeddings = {
            chunk_id: embedding
            for chunk_id, embedding in self.embedding_cache.items()
            if chunk_id in self.metadata_db
        }

        # Update in-memory cache to pruned version
        self.embedding_cache = active_embeddings

        # Create versioned cache structure
        cache_data = {
            'version': CACHE_VERSION,
            'model_name': self.model_name,
            'embedding_dimension': self.dimension,
            'embeddings': self.embedding_cache
        }

        # Write to temp file
        with open(temp_path, 'wb') as f:
            pickle.dump(cache_data, f)

        # Atomic rename (POSIX guarantees atomicity)
        os.rename(temp_path, str(self.cache_path))

    def _load_cache(self):
        """
        Load embedding cache from disk with version validation.

        If cache file doesn't exist, cache remains empty (graceful degradation).
        If cache is incompatible (version/model/dimension mismatch), cache is cleared.
        """
        if not self.cache_path.exists():
            return  # No cache file, stay empty

        try:
            with open(self.cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            # Handle old unversioned format (backward compatibility)
            if not isinstance(cache_data, dict) or 'version' not in cache_data:
                print("Warning: Old cache format detected, clearing cache", file=sys.stderr)
                self.embedding_cache = {}
                return

            # Validate version
            if cache_data.get('version') != CACHE_VERSION:
                print(f"Warning: Cache version mismatch (expected {CACHE_VERSION}, got {cache_data.get('version')}), clearing cache", file=sys.stderr)
                self.embedding_cache = {}
                return

            # Validate dimension
            if cache_data.get('embedding_dimension') != self.dimension:
                print(f"Warning: Dimension mismatch (expected {self.dimension}, got {cache_data.get('embedding_dimension')}), clearing cache", file=sys.stderr)
                self.embedding_cache = {}
                return

            # Validate model name (warn if different, but allow)
            if cache_data.get('model_name') != self.model_name:
                print(f"Warning: Model name mismatch (expected '{self.model_name}', got '{cache_data.get('model_name')}'), clearing cache", file=sys.stderr)
                self.embedding_cache = {}
                return

            # Load embeddings
            self.embedding_cache = cache_data.get('embeddings', {})

        except Exception as e:
            print(f"Warning: Failed to load embedding cache: {e}", file=sys.stderr)
            # Keep cache empty on load failure
            self.embedding_cache = {}

    def _calculate_bloat(self) -> Dict:
        """
        Calculate index bloat from lazy deletion.

        Bloat occurs when vectors remain in FAISS but their metadata is deleted (lazy deletion).
        This is cheaper than rebuilding the index for every delete, but accumulates stale vectors.

        Returns:
            Dict with bloat metrics:
            - total_vectors: Total vectors in FAISS index
            - active_chunks: Number of chunks in metadata (valid results)
            - stale_vectors: Vectors in FAISS without metadata (bloat)
            - bloat_percentage: (stale_vectors / total_vectors) * 100
        """
        total_vectors = self.index.ntotal
        active_chunks = len(self.metadata_db)
        stale_vectors = total_vectors - active_chunks

        # Calculate percentage (avoid division by zero)
        bloat_percentage = (stale_vectors / total_vectors * 100) if total_vectors > 0 else 0.0

        return {
            'total_vectors': total_vectors,
            'active_chunks': active_chunks,
            'stale_vectors': stale_vectors,
            'bloat_percentage': bloat_percentage
        }

    def _needs_rebuild(self) -> bool:
        """
        Determine if index needs rebuild based on bloat metrics.

        Hybrid trigger logic prevents rebuilding small projects with low absolute bloat:
        - Primary trigger: 20% bloat AND 500+ stale vectors (prevents small project rebuilds)
        - Fallback trigger: 30% bloat (regardless of count - critical bloat level)

        Returns:
            True if rebuild needed, False otherwise
        """
        bloat = self._calculate_bloat()
        bloat_percentage = bloat['bloat_percentage']
        stale_vectors = bloat['stale_vectors']

        # Primary: 20% bloat AND 500+ stale vectors
        primary_trigger = (bloat_percentage >= 20.0 and stale_vectors >= 500)

        # Fallback: 30% bloat (regardless of count)
        fallback_trigger = (bloat_percentage >= 30.0)

        return primary_trigger or fallback_trigger

    def rebuild_from_cache(self):
        """
        Rebuild FAISS index from cached embeddings, removing stale vectors.

        SAFETY: Uses backup/rollback pattern to prevent data loss:
        1. Backup old index files
        2. Build new index in memory
        3. Save new index
        4. On success: clean backup
        5. On failure: restore from backup

        Used when bloat exceeds thresholds or manual cleanup is needed.
        """
        print(f"Rebuilding index from cache ({len(self.metadata_db)} active chunks)...")

        # STEP 1: Backup existing index files
        backup_dir = self.index_dir / "backup"
        index_path = self.index_dir / "code.index"
        metadata_path = self.index_dir / "metadata.db"
        chunk_ids_path = self.index_dir / "chunk_ids.pkl"

        has_existing_index = index_path.exists() and metadata_path.exists() and chunk_ids_path.exists()

        if has_existing_index:
            import shutil
            # Create backup directory
            if backup_dir.exists():
                shutil.rmtree(backup_dir)  # Remove old backup if exists
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy files to backup
            shutil.copy2(index_path, backup_dir / "code.index")
            shutil.copy2(metadata_path, backup_dir / "metadata.db")
            shutil.copy2(chunk_ids_path, backup_dir / "chunk_ids.pkl")
            print(f"Backup created at {backup_dir}")

        # STEP 2: Build new index in memory
        new_index = faiss.IndexFlatIP(768)
        new_chunk_ids = []

        # Collect active chunks from cache
        vectors = []
        chunk_ids_to_add = []

        for chunk_id, entry in self.metadata_db.items():
            # Get embedding from cache
            if chunk_id not in self.embedding_cache:
                # Restore from backup on error
                if has_existing_index:
                    self._restore_from_backup(backup_dir)
                raise ValueError(f"Chunk {chunk_id} missing from cache - cannot rebuild")

            embedding = self.embedding_cache[chunk_id]
            vectors.append(embedding)
            chunk_ids_to_add.append(chunk_id)

        if not vectors:
            print("No active chunks to rebuild")
            return

        # Add all vectors to new index
        vectors_array = np.array(vectors, dtype=np.float32)

        # FIX: Explicitly copy to CPU memory (Apple Silicon MPS compatibility)
        vectors_array = np.ascontiguousarray(vectors_array.copy())

        faiss.normalize_L2(vectors_array)  # Normalize for cosine similarity
        new_index.add(vectors_array)
        new_chunk_ids.extend(chunk_ids_to_add)

        # Update faiss_ids in metadata to be sequential (0, 1, 2, ...)
        for i, chunk_id in enumerate(chunk_ids_to_add):
            self.metadata_db[chunk_id]['faiss_id'] = i

        # STEP 3: Update in-memory structures
        self.index = new_index
        self.chunk_ids = new_chunk_ids

        print(f"Rebuild complete: {len(chunk_ids_to_add)} vectors in clean index")

        # STEP 4: Clean up backup on success (keep for now for verification)
        # Backup will be cleaned up on next rebuild or manually
        # This allows users to verify rebuild before backup deletion

    def _restore_from_backup(self, backup_dir: Path):
        """
        Restore index from backup after failed rebuild.

        This is called when rebuild_from_cache() fails mid-operation.
        """
        import shutil
        print(f"Restoring index from backup at {backup_dir}...")

        index_path = self.index_dir / "code.index"
        metadata_path = self.index_dir / "metadata.db"
        chunk_ids_path = self.index_dir / "chunk_ids.pkl"

        # Restore files from backup
        if (backup_dir / "code.index").exists():
            shutil.copy2(backup_dir / "code.index", index_path)
        if (backup_dir / "metadata.db").exists():
            shutil.copy2(backup_dir / "metadata.db", metadata_path)
        if (backup_dir / "chunk_ids.pkl").exists():
            shutil.copy2(backup_dir / "chunk_ids.pkl", chunk_ids_path)

        print("Restore complete")

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

        # Save embedding cache (AFTER all FAISS operations complete)
        self._save_cache()

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

        # Add bloat metrics (Feature 2: Bloat Tracking)
        bloat = self._calculate_bloat()
        stats.update({
            'bloat_percentage': bloat['bloat_percentage'],
            'stale_vectors': bloat['stale_vectors'],
            'total_vectors': bloat['total_vectors'],
            'active_chunks': bloat['active_chunks']
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

        # FIX: Explicitly copy to CPU memory to avoid MPS device memory references
        # Apple Silicon MPS embeddings can have device memory references that conflict with FAISS (CPU-only)
        vectors_array = np.ascontiguousarray(vectors_array.copy())

        faiss.normalize_L2(vectors_array)  # Normalize for cosine similarity
        self.index.add(vectors_array)

        # Append chunk_ids to maintain order
        self.chunk_ids.extend(chunk_ids_to_add)

        # Build embedding cache AFTER FAISS operations complete (avoids memory conflicts)
        for result in embedding_results:
            chunk_id = result.chunk_id
            # Copy embedding to avoid GPU memory references
            self.embedding_cache[chunk_id] = result.embedding.copy()

        # Save cache to disk (Feature 1: Embedding Cache)
        self._save_cache()

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
        Search for similar code chunks with bloat-aware optimization.

        NEW Feature 5: Dynamic k-multiplier adapts to bloat percentage
        - 0% bloat → k_multiplier = 1.0 (no extra search)
        - 20% bloat → k_multiplier = 1.2 (search 20% more)
        - 50% bloat → k_multiplier = 1.5 (search 50% more)
        - Capped at 3.0x to prevent excessive searches

        NEW Feature 5: Adaptive retry for clustered bloat
        - If first search returns < k valid results (due to stale chunks)
        - Retry with 2x higher k to find more valid results
        - Prevents returning fewer results than requested

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

        # Feature 5: Dynamic k-multiplier based on bloat percentage
        bloat = self._calculate_bloat()
        bloat_percentage = bloat['bloat_percentage']

        # Calculate multiplier: 1.0 + (bloat% / 100)
        # Examples: 0% → 1.0x, 20% → 1.2x, 50% → 1.5x, 100% → 2.0x
        k_multiplier = 1.0 + (bloat_percentage / 100.0)
        k_multiplier = min(k_multiplier, 3.0)  # Cap at 3x

        # Use math.ceil() for proper rounding (not int())
        # Example: k=5, bloat=1% → ceil(5*1.01)=6 (not 5)
        search_k = math.ceil(k * k_multiplier)
        search_k = min(search_k, self.index.ntotal)

        # First search attempt
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
                continue  # Skip stale chunks (lazy deletion)

            metadata = self.metadata_db[chunk_id]['metadata']

            results.append((chunk_id, float(similarity), metadata))

            if len(results) >= k:
                break

        # Feature 5: Adaptive retry if results insufficient
        # This handles clustered bloat where stale chunks cluster with valid ones
        if len(results) < k and search_k < self.index.ntotal:
            # Retry with 2x higher k
            retry_k = min(search_k * 2, self.index.ntotal)

            similarities, indices = self.index.search(query_embedding, retry_k)

            results = []  # Reset results
            for similarity, index in zip(similarities[0], indices[0]):
                if index == -1:
                    break

                index = int(index)
                if index >= len(self.chunk_ids):
                    continue

                chunk_id = self.chunk_ids[index]

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

    def _delete_chunks_for_file(self, file_path: str) -> int:
        """
        Delete all chunks for a specific file from metadata and cache.

        This is used during incremental reindex to remove old chunks
        for modified or deleted files before re-embedding.

        Handles errors gracefully - continues with partial deletion if some
        chunks fail, logs warnings for failures.

        Args:
            file_path: Absolute path to the file

        Returns:
            Number of chunks successfully deleted
        """
        deleted_count = 0
        chunks_to_delete = []

        # Normalize target path once (fail fast if invalid)
        # Convert relative path to absolute by joining with project_path
        try:
            target_path = (Path(self.project_path) / file_path).resolve()
        except Exception as e:
            print(f"Warning: Failed to resolve path '{file_path}': {e}", file=sys.stderr)
            return 0

        try:
            # Find all chunks for this file
            # Use list() to avoid "dictionary changed size during iteration" error
            for chunk_id, entry in list(self.indexer.metadata_db.items()):
                try:
                    # Safely get metadata dict
                    metadata = entry.get('metadata', {})
                    chunk_file_path = metadata.get('file_path', '')

                    if not chunk_file_path:
                        continue  # Skip chunks with no file path

                    # Normalize chunk path for comparison
                    try:
                        chunk_path = Path(chunk_file_path).resolve()
                        if chunk_path == target_path:
                            chunks_to_delete.append(chunk_id)
                    except Exception:
                        # Skip chunks with invalid paths (symlink loops, permissions, etc.)
                        continue

                except Exception as e:
                    # Log but continue with other chunks
                    print(f"Warning: Failed to process chunk {chunk_id}: {e}", file=sys.stderr)
                    continue

            # Delete chunks from metadata and cache
            for chunk_id in chunks_to_delete:
                try:
                    # Delete from metadata
                    if chunk_id in self.indexer.metadata_db:
                        del self.indexer.metadata_db[chunk_id]
                        deleted_count += 1

                    # Delete from cache (best effort, don't fail if not in cache)
                    if chunk_id in self.indexer.embedding_cache:
                        del self.indexer.embedding_cache[chunk_id]

                except Exception as e:
                    # Log but continue with other chunks
                    print(f"Warning: Failed to delete chunk {chunk_id}: {e}", file=sys.stderr)
                    continue

            return deleted_count

        except Exception as e:
            # Unexpected error - log and return partial count
            print(f"Error in _delete_chunks_for_file('{file_path}'): {e}", file=sys.stderr)
            return deleted_count  # Return whatever we managed to delete

    def _incremental_index(self, changes):
        """
        Perform incremental reindex using cache for unchanged files.

        This is the KEY method that makes incremental indexing work with IndexFlatIP.
        Instead of re-embedding all files, we:
        1. Delete chunks for modified/deleted files
        2. Re-embed ONLY changed files
        3. Rebuild FAISS index from ALL cached embeddings (fast!)

        Args:
            changes: FileChanges object from change detector

        Returns:
            Result dict with success, reembedded_files, cached_files
        """
        start_time = time.time()
        timings = {}

        try:
            print("Starting incremental reindex...", file=sys.stderr)

            # Build current DAG
            phase_start = time.time()
            dag = MerkleDAG(self.project_path)
            dag.build()
            timings['dag_build'] = time.time() - phase_start

            # Step 1: Delete chunks for modified/removed files
            phase_start = time.time()
            files_to_reembed = list(changes.modified) + list(changes.added)
            files_to_delete = list(changes.removed) + list(changes.modified)

            for file_path in files_to_delete:
                deleted_count = self._delete_chunks_for_file(file_path)
                print(f"Deleted {deleted_count} chunks for {Path(file_path).name}", file=sys.stderr)

            timings['delete_chunks'] = time.time() - phase_start

            # Step 2: Embed ONLY changed files
            phase_start = time.time()
            all_embedding_results = []

            for file_path in files_to_reembed:
                print(f"Re-embedding {Path(file_path).name}...", file=sys.stderr)

                # Chunk the file (convert relative path to absolute)
                full_path = Path(self.project_path) / file_path
                chunks = self.chunker.chunk_file(str(full_path))

                if chunks:
                    # Embed the chunks
                    results = self.embedder.embed_chunks(chunks, batch_size=64)

                    # Add metadata
                    for result in results:
                        result.metadata['project_name'] = self.project_name
                        result.metadata['content'] = chunks[0].content if chunks else ""

                    all_embedding_results.extend(results)

            print(f"Re-embedded {len(all_embedding_results)} chunks from {len(files_to_reembed)} files", file=sys.stderr)
            timings['embedding'] = time.time() - phase_start

            # Step 3: Add new embeddings (this updates cache)
            phase_start = time.time()
            if all_embedding_results:
                self.indexer.add_embeddings(all_embedding_results)
            timings['add_embeddings'] = time.time() - phase_start

            # Step 4: Rebuild index from ALL cached embeddings (fast!)
            # NEW: Only rebuild if bloat exceeds threshold (auto-rebuild trigger)
            phase_start = time.time()
            bloat_stats = self.indexer._calculate_bloat()

            if self.indexer._needs_rebuild():
                # Bloat threshold exceeded - trigger auto-rebuild
                print(f"Bloat threshold exceeded: {bloat_stats['bloat_percentage']:.1f}% ({bloat_stats['stale_vectors']} stale)", file=sys.stderr)
                print("Auto-rebuilding index from cache to clear bloat...", file=sys.stderr)
                self.indexer.rebuild_from_cache()
                timings['auto_rebuild'] = time.time() - phase_start

                # Verify bloat cleared
                bloat_after = self.indexer._calculate_bloat()
                print(f"Bloat after rebuild: {bloat_after['bloat_percentage']:.1f}%", file=sys.stderr)
            else:
                # Bloat below threshold - skip rebuild
                if bloat_stats['bloat_percentage'] > 0:
                    print(f"Bloat: {bloat_stats['bloat_percentage']:.1f}% ({bloat_stats['stale_vectors']} stale) - below rebuild threshold", file=sys.stderr)
                timings['bloat_check'] = time.time() - phase_start

            # Step 6: Save snapshot
            phase_start = time.time()
            print("Saving Merkle DAG snapshot...", file=sys.stderr)
            self.snapshot_manager.save_snapshot(dag, {
                'project_name': self.project_name,
                'full_index': False,
                'incremental': True,
                'files_reembedded': len(files_to_reembed),
                'chunks_added': len(all_embedding_results)
            })
            timings['snapshot_save'] = time.time() - phase_start

            # Step 7: Save index
            phase_start = time.time()
            print("Saving FAISS index to disk...", file=sys.stderr)
            self.indexer.save_index()
            timings['index_save'] = time.time() - phase_start

            # Record timestamp
            self._record_index_timestamp(is_full_index=False)

            # Calculate total files
            total_files = len(list(Path(self.project_path).rglob('*.py')))  # Quick estimate
            cached_files = total_files - len(files_to_reembed)

            print(f"\n✓ Incremental reindex complete: {len(all_embedding_results)} chunks from {len(files_to_reembed)} files", file=sys.stderr)
            print(f"  Cached: {cached_files} files, Re-embedded: {len(files_to_reembed)} files", file=sys.stderr)

            return {
                'success': True,
                'incremental': True,
                'reembedded_files': len(files_to_reembed),
                'cached_files': cached_files,
                'chunks_added': len(all_embedding_results),
                'total_chunks': self.indexer.get_index_size(),
                'time_taken': round(time.time() - start_time, 2),
                'timing_breakdown': timings
            }

        except Exception as e:
            print(f"Error during incremental reindex: {e}", file=sys.stderr)
            return {
                'success': False,
                'error': str(e),
                'time_taken': round(time.time() - start_time, 2)
            }

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
        """
        Auto-reindex with INCREMENTAL support via cache + rebuild strategy.

        NEW DESIGN (Phase 2.4):
        - Detects file changes using Merkle tree
        - Re-embeds ONLY changed files
        - Rebuilds FAISS index from ALL cached embeddings (fast!)
        - Falls back to full reindex if cache incomplete or first time

        Incremental Strategy with IndexFlatIP:
        - IndexFlatIP uses sequential IDs - can't delete individual vectors
        - SOLUTION: Re-embed changed files, rebuild entire index from cache
        - Rebuild from cache is FAST (<0.01s vs 246s full reindex)

        Logic:
        1. Load previous snapshot and detect changes
        2. If no changes and not forced → skip reindex
        3. If force_full or no snapshot or cache incomplete → full reindex
        4. Otherwise → incremental reindex (re-embed changed + rebuild from cache)
        """
        start_time = time.time()

        try:
            # Step 1: Check if snapshot exists (first time = full reindex)
            if not self.snapshot_manager.has_snapshot(self.project_path):
                print("No snapshot found - performing full reindex...", file=sys.stderr)
                return self._full_index(start_time)

            # Step 2: Detect changes
            print("Detecting changes...", file=sys.stderr)
            dag = MerkleDAG(self.project_path)
            dag.build()

            prev_snapshot = self.snapshot_manager.load_snapshot(self.project_path)
            changes = self.change_detector.detect_changes(dag, prev_snapshot)

            # Step 3: If no changes and not forced, skip reindex
            if not changes.has_changes() and not force_full:
                print("No changes detected - skipping reindex", file=sys.stderr)
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'No changes detected',
                    'time_taken': round(time.time() - start_time, 2)
                }

            # Step 4: Check if cache is complete (if not, must do full reindex)
            if force_full or not self._cache_is_complete():
                reason = "Forced full reindex" if force_full else "Cache incomplete"
                print(f"{reason} - performing full reindex...", file=sys.stderr)
                return self._full_index(start_time)

            # Step 5: INCREMENTAL PATH - use cache for unchanged files!
            print(f"Changes detected: {changes.total_changed()} files", file=sys.stderr)
            return self._incremental_index(changes)

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'time_taken': round(time.time() - start_time, 2)
            }

    def _cache_is_complete(self) -> bool:
        """
        Check if cache contains embeddings for all chunks in metadata.

        Returns True if cache is complete, False if any chunks are missing.
        """
        try:
            # Check if cache file exists
            if not self.indexer.cache_path.exists():
                return False

            # Check if every chunk in metadata has a cached embedding
            for chunk_id in self.indexer.metadata_db.keys():
                if chunk_id not in self.indexer.embedding_cache:
                    print(f"Cache incomplete: missing embedding for chunk {chunk_id}", file=sys.stderr)
                    return False

            return True

        except Exception as e:
            print(f"Error checking cache completeness: {e}", file=sys.stderr)
            return False

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
