"""
TurboVec Vector Index Provider
A simple, fast in-memory vector index using numpy for similarity search
Suitable for prototyping and small to medium datasets
"""
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

from providers.vector_index.base import VectorIndexProvider, SearchResult


class TurboVec(VectorIndexProvider):
    """
    TurboVec - A lightweight in-memory vector index
    Uses cosine similarity for nearest neighbor search
    """
    
    def __init__(self):
        self.index_name: str = ""
        self.dimension: int = 0
        self._vectors: Optional[np.ndarray] = None
        self._ids: List[str] = []
        self._metadata: List[Dict[str, Any]] = []
        self._initialized = False
    
    @property
    def name(self) -> str:
        return "turbovec"
    
    def initialize(self, index_name: str, dimension: int,
                   config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize TurboVec index"""
        try:
            self.index_name = index_name
            self.dimension = dimension
            self._vectors = np.zeros((0, dimension), dtype=np.float32)
            self._ids = []
            self._metadata = []
            self._initialized = True
            return True
        except Exception:
            self._initialized = False
            return False
    
    def is_available(self) -> bool:
        """Check if TurboVec is available"""
        return self._initialized
    
    def add_vectors(self, vectors: List[List[float]], ids: List[str],
                    metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """Add vectors to the index"""
        if not self._initialized:
            raise RuntimeError("TurboVec not initialized")
        
        if len(vectors) != len(ids):
            raise ValueError("Number of vectors must match number of IDs")
        
        if metadata and len(metadata) != len(ids):
            raise ValueError("Number of metadata entries must match number of IDs")
        
        # Validate dimensions
        for i, vec in enumerate(vectors):
            if len(vec) != self.dimension:
                raise ValueError(f"Vector {i} has dimension {len(vec)}, expected {self.dimension}")
        
        try:
            # Convert to numpy and normalize
            new_vectors = np.array(vectors, dtype=np.float32)
            new_vectors = new_vectors / (np.linalg.norm(new_vectors, axis=1, keepdims=True) + 1e-8)
            
            # Append to existing vectors
            self._vectors = np.vstack([self._vectors, new_vectors])
            self._ids.extend(ids)
            
            if metadata:
                self._metadata.extend(metadata)
            else:
                self._metadata.extend([{} for _ in ids])
            
            return True
        except Exception as e:
            return False
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """Search for similar vectors using cosine similarity"""
        if not self._initialized or len(self._ids) == 0:
            return []
        
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension {len(query_vector)} doesn't match index dimension {self.dimension}")
        
        try:
            # Normalize query vector
            query_norm = np.array(query_vector, dtype=np.float32)
            query_norm = query_norm / (np.linalg.norm(query_norm) + 1e-8)
            
            # Compute cosine similarities (dot product of normalized vectors)
            similarities = np.dot(self._vectors, query_norm)
            
            # Get top-k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0:  # Only include positive similarities
                    results.append(SearchResult(
                        id=self._ids[idx],
                        score=float(similarities[idx]),
                        metadata=self._metadata[idx].copy()
                    ))
            
            return results
        except Exception as e:
            return []
    
    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by ID"""
        if not self._initialized:
            return False
        
        try:
            # Find indices to delete
            delete_mask = np.array([id_ in ids for id_ in self._ids])
            
            # Keep only non-deleted items
            self._vectors = self._vectors[~delete_mask]
            self._ids = [id_ for id_, deleted in zip(self._ids, delete_mask) if not deleted]
            self._metadata = [m for m, deleted in zip(self._metadata, delete_mask) if not deleted]
            
            return True
        except Exception:
            return False
    
    def get_document_count(self) -> int:
        """Get number of documents in the index"""
        return len(self._ids)
    
    def save(self, path: Optional[str] = None) -> bool:
        """Save index to disk"""
        if not self._initialized:
            return False
        
        try:
            if path is None:
                path = f"{self.index_name}.pkl"
            
            data = {
                'index_name': self.index_name,
                'dimension': self.dimension,
                'vectors': self._vectors,
                'ids': self._ids,
                'metadata': self._metadata
            }
            
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            
            return True
        except Exception:
            return False
    
    def load(self, path: Optional[str] = None) -> bool:
        """Load index from disk"""
        try:
            if path is None:
                path = f"{self.index_name}.pkl"
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.index_name = data['index_name']
            self.dimension = data['dimension']
            self._vectors = data['vectors']
            self._ids = data['ids']
            self._metadata = data['metadata']
            self._initialized = True
            
            return True
        except Exception:
            self._initialized = False
            return False
