"""Chunking stage for splitting text into manageable chunks."""

from typing import Dict, Any, List
from pipeline.stages.base import PipelineStage as Stage, PipelineContext as StageContext, StageResult, StageStatus


class ChunkingStrategy:
    """Base class for chunking strategies."""
    
    def chunk(self, text: str, **kwargs) -> List[Dict[str, Any]]:
        raise NotImplementedError


class FixedSizeChunking(ChunkingStrategy):
    """Split text into fixed-size chunks with overlap."""
    
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, **kwargs) -> List[Dict[str, Any]]:
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text) and chunk_text[-1] not in '.!?':
                # Find last sentence boundary
                for boundary in ['.', '!', '?']:
                    last_boundary = chunk_text.rfind(boundary)
                    if last_boundary > self.chunk_size // 2:
                        end = start + last_boundary + 1
                        chunk_text = text[start:end]
                        break
            
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text.strip(),
                'start_char': start,
                'end_char': end,
                'metadata': {}
            })
            
            chunk_id += 1
            start = end - self.overlap if end < len(text) else len(text)
        
        return chunks


class SemanticChunking(ChunkingStrategy):
    """Split text based on semantic boundaries (paragraphs, sections)."""
    
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 1024):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk(self, text: str, **kwargs) -> List[Dict[str, Any]]:
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 0
        start_char = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            if current_length + para_length > self.max_chunk_size and current_length >= self.min_chunk_size:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_char': start_char,
                    'end_char': start_char + len(chunk_text),
                    'metadata': {'paragraphs': len(current_chunk)}
                })
                chunk_id += 1
                start_char += len(chunk_text)
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_char': start_char,
                'end_char': start_char + len(chunk_text),
                'metadata': {'paragraphs': len(current_chunk)}
            })
        
        return chunks


class ChunkingStage(Stage):
    """Stage for chunking cleaned text into smaller units."""
    
    def __init__(self, strategy: str = 'fixed', **kwargs):
        super().__init__()
        self.strategy_name = strategy
        
        if strategy == 'fixed':
            chunk_size = kwargs.get('chunk_size', 512)
            overlap = kwargs.get('overlap', 50)
            self.strategy = FixedSizeChunking(chunk_size=chunk_size, overlap=overlap)
        elif strategy == 'semantic':
            min_size = kwargs.get('min_chunk_size', 100)
            max_size = kwargs.get('max_chunk_size', 1024)
            self.strategy = SemanticChunking(min_chunk_size=min_size, max_chunk_size=max_size)
        else:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
    
    def execute(self, context: StageContext) -> StageResult:
        """Execute chunking on cleaned text."""
        try:
            # Get cleaned text from previous stage
            cleaned_text = context.data.get('cleaned_text')
            if not cleaned_text:
                return StageResult(
                    status=StageStatus.FAILED,
                    message="No cleaned text found in context",
                    data={}
                )
            
            # Apply chunking strategy
            chunks = self.strategy.chunk(cleaned_text)
            
            # Store chunks in context
            context.data['chunks'] = chunks
            context.data['chunk_count'] = len(chunks)
            
            # Update document metadata
            doc_metadata = context.data.get('doc_metadata', {})
            doc_metadata['chunk_count'] = len(chunks)
            context.data['doc_metadata'] = doc_metadata
            
            return StageResult(
                status=StageStatus.COMPLETED,
                message=f"Created {len(chunks)} chunks",
                data={
                    'chunks': chunks,
                    'chunk_count': len(chunks),
                    'strategy': self.strategy_name
                }
            )
            
        except Exception as e:
            return StageResult(
                status=StageStatus.FAILED,
                message=f"Chunking failed: {str(e)}",
                data={}
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get stage configuration."""
        return {
            'stage_type': 'chunking',
            'strategy': self.strategy_name
        }
