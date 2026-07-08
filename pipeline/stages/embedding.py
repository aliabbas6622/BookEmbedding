"""Embedding stage for generating vector embeddings from text chunks."""

from typing import Dict, Any, List
import numpy as np
from pipeline.stages.base import PipelineStage as Stage, PipelineContext as StageContext, StageResult, StageStatus


class EmbeddingProvider:
    """Base interface for embedding providers."""
    
    def embed(self, texts: List[str]) -> List[np.ndarray]:
        raise NotImplementedError
    
    def get_dimension(self) -> int:
        raise NotImplementedError


class SentenceTransformerEmbeddings(EmbeddingProvider):
    """Sentence Transformers embedding provider."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._model = None
        self._dimension = None
    
    @property
    def model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                # Get dimension by running a test embedding
                test_embed = self._model.encode(['test'])
                self._dimension = len(test_embed[0])
            except ImportError:
                raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        return self._model
    
    def embed(self, texts: List[str]) -> List[np.ndarray]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [embeddings[i] for i in range(len(texts))]
    
    def get_dimension(self) -> int:
        if self._dimension is None:
            _ = self.model  # Initialize to get dimension
        return self._dimension


class MockEmbeddings(EmbeddingProvider):
    """Mock embedding provider for testing."""
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
    
    def embed(self, texts: List[str]) -> List[np.ndarray]:
        # Generate random embeddings for testing
        return [np.random.randn(self.dimension) for _ in texts]
    
    def get_dimension(self) -> int:
        return self.dimension


class EmbeddingStage(Stage):
    """Stage for generating embeddings from text chunks."""
    
    def __init__(self, provider: str = 'mock', **kwargs):
        super().__init__()
        self.provider_name = provider
        
        if provider == 'sentence_transformer':
            model_name = kwargs.get('model_name', 'all-MiniLM-L6-v2')
            self.embedding_provider = SentenceTransformerEmbeddings(model_name=model_name)
        elif provider == 'mock':
            dimension = kwargs.get('dimension', 384)
            self.embedding_provider = MockEmbeddings(dimension=dimension)
        else:
            raise ValueError(f"Unknown embedding provider: {provider}")
    
    def execute(self, context: StageContext) -> StageResult:
        """Generate embeddings for all chunks."""
        try:
            # Get chunks from previous stage
            chunks = context.data.get('chunks')
            if not chunks:
                return StageResult(
                    status=StageStatus.FAILED,
                    message="No chunks found in context",
                    data={}
                )
            
            # Extract texts from chunks
            texts = [chunk['text'] for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.embedding_provider.embed(texts)
            
            # Attach embeddings to chunks
            embedded_chunks = []
            for i, chunk in enumerate(chunks):
                embedded_chunk = chunk.copy()
                embedded_chunk['embedding'] = embeddings[i].tolist()  # Convert to list for JSON serialization
                embedded_chunks.append(embedded_chunk)
            
            # Store in context
            context.data['embedded_chunks'] = embedded_chunks
            context.data['embedding_dimension'] = self.embedding_provider.get_dimension()
            
            return StageResult(
                status=StageStatus.COMPLETED,
                message=f"Generated embeddings for {len(embedded_chunks)} chunks",
                data={
                    'embedded_chunks': embedded_chunks,
                    'chunk_count': len(embedded_chunks),
                    'embedding_dimension': self.embedding_provider.get_dimension(),
                    'provider': self.provider_name
                }
            )
            
        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                message=f"Embedding generation failed: {str(e)}",
                data={}
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get stage configuration."""
        return {
            'stage_type': 'embedding',
            'provider': self.provider_name
        }
