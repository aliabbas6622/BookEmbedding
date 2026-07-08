"""
Provider interface for text embeddings
All embedding providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmbeddingResult:
    """Represents embedding result"""
    
    def __init__(self, embeddings: List[List[float]], model: str = "",
                 usage: Optional[Dict[str, int]] = None):
        self.embeddings = embeddings
        self.model = model
        self.usage = usage or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "embeddings": self.embeddings,
            "model": self.model,
            "usage": self.usage
        }


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension"""
        pass
    
    @abstractmethod
    def initialize(self, api_key: Optional[str] = None,
                   base_url: Optional[str] = None,
                   model: Optional[str] = None) -> bool:
        """
        Initialize the embedding provider
        
        Args:
            api_key: API key if required
            base_url: Base URL for API endpoint
            model: Model to use
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def embed_text(self, texts: List[str]) -> EmbeddingResult:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            EmbeddingResult with embeddings
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready to use"""
        pass
    
    def get_supported_models(self) -> List[str]:
        """Return list of supported models"""
        return []
