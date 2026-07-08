"""
Chunking stage - splits text into chunks for embedding
"""
from typing import Dict, Any, Optional, List

from src.pipeline.base import PipelineStage, PipelineContext


class ChunkingStage(PipelineStage):
    """Splits text into overlapping chunks"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("chunking", config)
        self.chunk_size = config.get("chunk_size", 512)
        self.chunk_overlap = config.get("chunk_overlap", 50)
        self.min_chunk_size = config.get("min_chunk_size", 50)
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute chunking"""
        text = context.get("cleaned_text")
        
        if not text:
            context.add_error("No cleaned text available. Run text_cleaning first.")
            return context
        
        # Create chunks
        chunks = self._split_text(text)
        
        # Store chunks
        context.set("chunks", chunks)
        context.set("chunk_count", len(chunks))
        
        return context
    
    def _split_text(self, text: str) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks"""
        chunks = []
        
        # Simple character-based chunking
        # In production, you might want sentence-aware or token-aware chunking
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings in the overlap region
                overlap_start = max(start, end - self.chunk_overlap)
                
                # Find last sentence ending before end
                for punct in ['.', '!', '?', '\n']:
                    last_pos = text.rfind(punct, overlap_start, end)
                    if last_pos > start:
                        end = last_pos + 1
                        break
            
            chunk_text = text[start:end].strip()
            
            # Only add chunks that meet minimum size
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "metadata": {
                        "chunk_size": len(chunk_text)
                    }
                })
                chunk_index += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start < 0:
                start = end
        
        return chunks
