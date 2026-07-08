"""
Provider interface for Vector Index
All vector index providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class SearchResult:
    """Represents a search result"""
    
    def __init__(self, id: str, score: float, metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.score = score
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "score": self.score,
            "metadata": self.metadata
        }


class VectorIndexProvider(ABC):
    """Abstract base class for vector index providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name"""
        pass
    
    @abstractmethod
    def initialize(self, index_name: str, dimension: int,
                   config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the vector index
        
        Args:
            index_name: Name of the index
            dimension: Dimension of embeddings
            config: Additional configuration
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def add_vectors(self, vectors: List[List[float]], ids: List[str],
                    metadata: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Add vectors to the index
        
        Args:
            vectors: List of embedding vectors
            ids: List of IDs corresponding to vectors
            metadata: Optional list of metadata dicts
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        """
        Delete vectors by ID
        
        Args:
            ids: List of IDs to delete
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready to use"""
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """Get number of documents in the index"""
        pass
    
    def save(self, path: Optional[str] = None) -> bool:
        """Persist the index to disk"""
        return True
    
    def load(self, path: Optional[str] = None) -> bool:
        """Load index from disk"""
        return True
