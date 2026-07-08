"""
Base class for vector index providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorIndexProvider(ABC):
    """Base class for vector index providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self, index_name: str) -> bool:
        """
        Initialize the vector index
        
        Args:
            index_name: Name of the index to create/use
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def add_vector(self, vector: List[float], metadata: Dict[str, Any]) -> bool:
        """
        Add a vector to the index
        
        Args:
            vector: Embedding vector
            metadata: Associated metadata
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of results with vectors, metadata, and scores
        """
        pass
    
    @abstractmethod
    async def delete_index(self, index_name: str) -> bool:
        """Delete an index"""
        pass
