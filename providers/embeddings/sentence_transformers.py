"""
Sentence Transformers embedding provider
"""
from typing import List, Dict, Any, Optional

from providers.embeddings.base import EmbeddingProvider


class SentenceTransformersEmbedder(EmbeddingProvider):
    """Sentence Transformers embedding provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.model_name = self.config.get("model_name", "all-MiniLM-L6-v2")
        self.device = self.config.get("device", "cpu")
        self._model = None
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except ImportError:
                self._model = None
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        self._load_model()
        
        if self._model is None:
            # Mock embedding for testing
            return self._mock_embed(text)
        
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def _mock_embed(self, text: str) -> List[float]:
        """Mock embedding for when dependencies are not installed"""
        # Generate a deterministic mock embedding based on text hash
        import hashlib
        dim = 384  # Common dimension for sentence transformers
        
        hash_bytes = hashlib.sha256(text.encode()).digest()
        hash_int = int.from_bytes(hash_bytes[:16], 'big')
        
        # Generate pseudo-random but deterministic embedding
        embedding = []
        for i in range(dim):
            seed = hash_int + i
            value = (seed % 10000) / 10000.0 - 0.5  # Range: [-0.5, 0.5]
            embedding.append(float(value))
        
        # Normalize
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        self._load_model()
        
        if self._model is None:
            # Mock embeddings
            return [self._mock_embed(text) for text in texts]
        
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        # Common dimensions for popular models
        model_dims = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "paraphrase-multilingual-MiniLM-L12-v2": 384,
        }
        return model_dims.get(self.model_name, 384)
