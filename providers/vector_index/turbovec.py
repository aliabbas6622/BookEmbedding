"""
TurboVec - Simple in-memory vector index provider
"""
import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict

from providers.vector_index.base import VectorIndexProvider


class TurboVec(VectorIndexProvider):
    """Simple in-memory vector index using cosine similarity"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.metric = config.get("metric", "cosine")
        self._indexes: Dict[str, Dict] = defaultdict(lambda: {
            "vectors": [],
            "metadata": [],
            "dimension": None
        })
    
    async def initialize(self, index_name: str) -> bool:
        """Initialize an index"""
        if index_name not in self._indexes:
            self._indexes[index_name] = {
                "vectors": [],
                "metadata": [],
                "dimension": None
            }
        self._initialized = True
        return True
    
    async def add_vector(self, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """Add a vector to the default index"""
        return await self.add_vector_to_index("default", vector, metadata)
    
    async def add_vector_to_index(
        self,
        index_name: str,
        vector: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """Add a vector to a specific index"""
        if index_name not in self._indexes:
            await self.initialize(index_name)
        
        index = self._indexes[index_name]
        
        # Check dimension consistency
        if index["dimension"] is None:
            index["dimension"] = len(vector)
        elif index["dimension"] != len(vector):
            raise ValueError(
                f"Vector dimension {len(vector)} doesn't match "
                f"index dimension {index['dimension']}"
            )
        
        index["vectors"].append(np.array(vector))
        index["metadata"].append(metadata)
        
        return True
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in the default index"""
        return await self.search_index("default", query_vector, top_k, filter_metadata)
    
    async def search_index(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a specific index"""
        if index_name not in self._indexes:
            return []
        
        index = self._indexes[index_name]
        vectors = index["vectors"]
        metadata_list = index["metadata"]
        
        if not vectors:
            return []
        
        query_array = np.array(query_vector)
        
        # Calculate similarities
        similarities = []
        for i, vec in enumerate(vectors):
            # Apply metadata filter if provided
            if filter_metadata:
                meta = metadata_list[i]
                if not all(meta.get(k) == v for k, v in filter_metadata.items()):
                    continue
            
            # Calculate cosine similarity
            sim = self._cosine_similarity(query_array, vec)
            similarities.append((i, sim))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k results
        results = []
        for idx, score in similarities[:top_k]:
            results.append({
                "id": idx,
                "score": float(score),
                "metadata": metadata_list[idx]
            })
        
        return results
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    async def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        if index_name in self._indexes:
            del self._indexes[index_name]
        return True
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get statistics for an index"""
        if index_name not in self._indexes:
            return {"error": "Index not found"}
        
        index = self._indexes[index_name]
        return {
            "name": index_name,
            "vector_count": len(index["vectors"]),
            "dimension": index["dimension"],
            "metric": self.metric
        }
