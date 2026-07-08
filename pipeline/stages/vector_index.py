"""Vector Index stage for storing and searching embeddings."""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from pipeline.stages.base import PipelineStage as Stage, PipelineContext as StageContext, StageResult, StageStatus


class VectorIndexProvider:
    """Base interface for vector index providers."""
    
    def add(self, vectors: List[np.ndarray], metadata: List[Dict[str, Any]]) -> None:
        raise NotImplementedError
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        raise NotImplementedError
    
    def save(self, path: str) -> None:
        raise NotImplementedError
    
    def load(self, path: str) -> None:
        raise NotImplementedError


class TurboVecIndex(VectorIndexProvider):
    """Simple in-memory vector index using cosine similarity."""
    
    def __init__(self):
        self.vectors: List[np.ndarray] = []
        self.metadata: List[Dict[str, Any]] = []
        self._normalized_vectors: List[np.ndarray] = []
    
    def _normalize(self, vector: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def add(self, vectors: List[np.ndarray], metadata: List[Dict[str, Any]]) -> None:
        for vec, meta in zip(vectors, metadata):
            self.vectors.append(vec)
            self.metadata.append(meta)
            self._normalized_vectors.append(self._normalize(vec))
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if not self.vectors:
            return []
        
        query_norm = self._normalize(query_vector)
        
        # Calculate cosine similarities
        similarities = []
        for i, vec_norm in enumerate(self._normalized_vectors):
            sim = np.dot(query_norm, vec_norm)
            similarities.append((i, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        results = []
        for idx, sim in similarities[:top_k]:
            results.append((self.metadata[idx].copy(), float(sim)))
        
        return results
    
    def save(self, path: str) -> None:
        import pickle
        data = {
            'vectors': [v.tolist() for v in self.vectors],
            'metadata': self.metadata
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: str) -> None:
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.vectors = [np.array(v) for v in data['vectors']]
        self.metadata = data['metadata']
        self._normalized_vectors = [self._normalize(v) for v in self.vectors]
    
    def size(self) -> int:
        return len(self.vectors)


class FAISSIndex(VectorIndexProvider):
    """FAISS vector index provider."""
    
    def __init__(self, dimension: int = 384, use_gpu: bool = False):
        self.dimension = dimension
        self.use_gpu = use_gpu
        self._index = None
        self.metadata: List[Dict[str, Any]] = []
    
    @property
    def index(self):
        if self._index is None:
            try:
                import faiss
                if self.use_gpu:
                    res = faiss.StandardGpuResources()
                    self._index = faiss.GpuIndexFlatIP(res, self.dimension)
                else:
                    self._index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
            except ImportError:
                raise ImportError("faiss not installed. Run: pip install faiss-cpu")
        return self._index
    
    def add(self, vectors: List[np.ndarray], metadata: List[Dict[str, Any]]) -> None:
        if not vectors:
            return
        
        # Normalize vectors for cosine similarity
        normalized = []
        for vec in vectors:
            norm = np.linalg.norm(vec)
            if norm > 0:
                normalized.append(vec / norm)
            else:
                normalized.append(vec)
        
        matrix = np.array(normalized, dtype=np.float32)
        self.index.add(matrix)
        self.metadata.extend(metadata)
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        if self.index.ntotal == 0:
            return []
        
        # Normalize query
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_norm = query_vector / norm
        else:
            query_norm = query_vector
        
        query_matrix = np.array([query_norm], dtype=np.float32)
        distances, indices = self.index.search(query_matrix, min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                results.append((self.metadata[idx].copy(), float(dist)))
        
        return results
    
    def save(self, path: str) -> None:
        import faiss
        import pickle
        
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.faiss")
        
        # Save metadata separately
        with open(f"{path}.meta.pkl", 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def load(self, path: str) -> None:
        import faiss
        import pickle
        
        self._index = faiss.read_index(f"{path}.faiss")
        
        with open(f"{path}.meta.pkl", 'rb') as f:
            self.metadata = pickle.load(f)
    
    def size(self) -> int:
        return self.index.ntotal


class VectorIndexStage(Stage):
    """Stage for adding embedded chunks to a vector index."""
    
    def __init__(self, provider: str = 'turbovec', **kwargs):
        super().__init__()
        self.provider_name = provider
        
        if provider == 'turbovec':
            self.vector_provider = TurboVecIndex()
        elif provider == 'faiss':
            dimension = kwargs.get('dimension', 384)
            use_gpu = kwargs.get('use_gpu', False)
            self.vector_provider = FAISSIndex(dimension=dimension, use_gpu=use_gpu)
        else:
            raise ValueError(f"Unknown vector index provider: {provider}")
    
    def execute(self, context: StageContext) -> StageResult:
        """Add embedded chunks to the vector index."""
        try:
            # Get embedded chunks from previous stage
            embedded_chunks = context.data.get('embedded_chunks')
            if not embedded_chunks:
                return StageResult(
                    status=StageStatus.FAILED,
                    message="No embedded chunks found in context",
                    data={}
                )
            
            # Extract vectors and metadata
            vectors = []
            metadata = []
            
            doc_id = context.data.get('doc_metadata', {}).get('id', 'unknown')
            
            for chunk in embedded_chunks:
                # Convert embedding back to numpy array
                embedding = np.array(chunk['embedding'])
                vectors.append(embedding)
                
                # Create metadata for this chunk
                chunk_meta = {
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'doc_id': doc_id,
                    'start_char': chunk.get('start_char', 0),
                    'end_char': chunk.get('end_char', 0),
                    'extra_metadata': chunk.get('metadata', {})
                }
                metadata.append(chunk_meta)
            
            # Add to vector index
            self.vector_provider.add(vectors, metadata)
            
            # Store index info in context
            context.data['vector_index'] = self.vector_provider
            context.data['indexed_count'] = len(vectors)
            
            return StageResult(
                status=StageStatus.COMPLETED,
                message=f"Indexed {len(vectors)} vectors",
                data={
                    'indexed_count': len(vectors),
                    'provider': self.provider_name,
                    'total_size': self.vector_provider.size()
                }
            )
            
        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                message=f"Vector indexing failed: {str(e)}",
                data={}
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get stage configuration."""
        return {
            'stage_type': 'vector_index',
            'provider': self.provider_name
        }
    
    def get_index(self) -> VectorIndexProvider:
        """Get the vector index provider."""
        return self.vector_provider
