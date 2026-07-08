"""
Sentence Transformers Embedding Provider
Uses local sentence-transformers models for embeddings
"""
from typing import List, Dict, Any, Optional
import numpy as np

from providers.embeddings.base import EmbeddingProvider, EmbeddingResult


class SentenceTransformersEmbedding(EmbeddingProvider):
    """Sentence Transformers embedding provider using local models"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._initialized = False
        self._dimension = 384  # Default for all-MiniLM-L6-v2
    
    @property
    def name(self) -> str:
        return "sentence_transformers"
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def initialize(self, api_key: Optional[str] = None,
                   base_url: Optional[str] = None,
                   model: Optional[str] = None) -> bool:
        """Initialize sentence transformers model"""
        if model:
            self.model_name = model
        
        try:
            from sentence_transformers import SentenceTransformer
            
            self._model = SentenceTransformer(self.model_name)
            
            # Get dimension from model
            if hasattr(self._model, 'get_sentence_embedding_dimension'):
                self._dimension = self._model.get_sentence_embedding_dimension()
            elif hasattr(self._model, 'encode'):
                # Infer dimension by encoding a test sentence
                test_embedding = self._model.encode(["test"])[0]
                self._dimension = len(test_embedding)
            
            self._initialized = True
            return True
        except ImportError:
            self._initialized = False
            return False
        except Exception as e:
            self._initialized = False
            return False
    
    def is_available(self) -> bool:
        """Check if sentence transformers is available"""
        if not self._initialized:
            return self.initialize()
        return self._initialized and self._model is not None
    
    def embed_text(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings for texts"""
        if not self.is_available():
            raise RuntimeError("Sentence Transformers is not available")
        
        if not texts:
            return EmbeddingResult(embeddings=[], model=self.model_name)
        
        try:
            embeddings = self._model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            # Convert numpy arrays to lists
            embeddings_list = embeddings.tolist()
            
            return EmbeddingResult(
                embeddings=embeddings_list,
                model=self.model_name,
                usage={"input_tokens": sum(len(t.split()) for t in texts)}
            )
        except Exception as e:
            raise RuntimeError(f"Sentence Transformers encoding failed: {str(e)}")
    
    def get_supported_models(self) -> List[str]:
        """Return common sentence transformer models"""
        return [
            "all-MiniLM-L6-v2",
            "all-MiniLM-L12-v2",
            "all-mpnet-base-v2",
            "paraphrase-MiniLM-L6-v2",
            "paraphrase-multilingual-MiniLM-L12-v2"
        ]
