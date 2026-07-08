"""
Base class for embedding providers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmbeddingProvider(ABC):
    """Base class for embedding providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            List of floats representing the embedding vector
        """
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            emb = await self.embed(text)
            embeddings.append(emb)
        return embeddings
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of generated embeddings"""
        pass
