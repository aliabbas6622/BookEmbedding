"""
Embedding stage - generates embeddings for text chunks
"""
from typing import Dict, Any, Optional, List

from ragstudio.pipeline.base import PipelineStage, PipelineContext


class EmbeddingStage(PipelineStage):
    """Generates embeddings for text chunks"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("embedding", config)
        self.provider_name = config.get("provider", "sentence_transformers")
        self.provider_config = config.get("provider_config", {})
        self.batch_size = config.get("batch_size", 32)
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute embedding generation"""
        chunks = context.get("chunks")
        
        if not chunks:
            context.add_error("No chunks available. Run chunking first.")
            return context
        
        try:
            # Get embedding provider
            provider = self._get_provider()
            
            # Extract texts
            texts = [chunk["content"] for chunk in chunks]
            
            # Generate embeddings in batches
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch_texts = texts[i:i + self.batch_size]
                batch_embeddings = await provider.embed_batch(batch_texts)
                all_embeddings.extend(batch_embeddings)
            
            # Attach embeddings to chunks
            for chunk, embedding in zip(chunks, all_embeddings):
                chunk["embedding"] = embedding
            
            # Store embedded chunks
            context.set("embedded_chunks", chunks)
            context.set("embedding_dimension", len(all_embeddings[0]) if all_embeddings else 0)
            
            return context
            
        except Exception as e:
            context.add_error(f"Embedding generation failed: {str(e)}")
            raise
    
    def _get_provider(self):
        """Get embedding provider instance"""
        if self.provider_name == "sentence_transformers":
            from providers.embeddings.sentence_transformers import SentenceTransformersEmbedder
            return SentenceTransformersEmbedder(self.provider_config)
        elif self.provider_name == "openai":
            from providers.embeddings.openai import OpenAIEmbedder
            return OpenAIEmbedder(self.provider_config)
        else:
            raise ValueError(f"Unknown embedding provider: {self.provider_name}")
