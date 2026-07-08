"""
Vector index stage - stores embeddings in vector index
"""
from typing import Dict, Any, Optional, List

from src.pipeline.base import PipelineStage, PipelineContext


class VectorIndexStage(PipelineStage):
    """Stores embeddings in vector index"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("vector_index", config)
        self.provider_name = config.get("provider", "turbovec")
        self.provider_config = config.get("provider_config", {})
        self.index_name = config.get("index_name", "default")
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute vector indexing"""
        embedded_chunks = context.get("embedded_chunks")
        document_id = context.document_id
        
        if not embedded_chunks:
            context.add_error("No embedded chunks available. Run embedding first.")
            return context
        
        try:
            # Get vector index provider
            provider = self._get_provider()
            
            # Initialize index if needed
            await provider.initialize(self.index_name)
            
            # Add vectors to index
            added_count = 0
            for chunk in embedded_chunks:
                embedding = chunk.get("embedding")
                if embedding:
                    metadata = {
                        "document_id": document_id,
                        "chunk_index": chunk.get("chunk_index"),
                        "content": chunk.get("content"),
                        **chunk.get("metadata", {})
                    }
                    
                    await provider.add_vector(
                        vector=embedding,
                        metadata=metadata
                    )
                    added_count += 1
            
            # Store index info
            context.set("index_name", self.index_name)
            context.set("vectors_added", added_count)
            
            return context
            
        except Exception as e:
            context.add_error(f"Vector indexing failed: {str(e)}")
            raise
    
    def _get_provider(self):
        """Get vector index provider instance"""
        if self.provider_name == "turbovec":
            from providers.vector_index.turbovec import TurboVec
            return TurboVec(self.provider_config)
        elif self.provider_name == "faiss":
            from providers.vector_index.faiss import FAISSIndex
            return FAISSIndex(self.provider_config)
        else:
            raise ValueError(f"Unknown vector index provider: {self.provider_name}")
