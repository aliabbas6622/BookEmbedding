"""
Stage 3: Text Cleaning and Preprocessing
Cleans and preprocesses extracted text
"""
import re
from typing import Dict, Any, List

from pipeline.stages.base import PipelineStage, StageResult, PipelineContext


class TextCleaningStage(PipelineStage):
    """Stage 3: Clean and preprocess extracted text"""
    
    @property
    def name(self) -> str:
        return "text_cleaning"
    
    @property
    def description(self) -> str:
        return "Clean and preprocess extracted text"
    
    @property
    def required_inputs(self) -> List[str]:
        return ["extracted_text"]
    
    @property
    def outputs(self) -> List[str]:
        return ["cleaned_text"]
    
    def __init__(self, remove_extra_whitespace: bool = True,
                 remove_special_chars: bool = False,
                 normalize_unicode: bool = True):
        self.remove_extra_whitespace = remove_extra_whitespace
        self.remove_special_chars = remove_special_chars
        self.normalize_unicode = normalize_unicode
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute text cleaning stage"""
        from datetime import datetime
        started_at = datetime.now()
        
        try:
            extracted_text = context.get("extracted_text")
            if not extracted_text:
                return StageResult(
                    success=False,
                    message="No extracted text found",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            cleaned_texts = []
            
            for item in extracted_text:
                text = item.get("text", "")
                file_path = item.get("file_path", "")
                
                # Apply cleaning operations
                cleaned = self._clean_text(text)
                
                cleaned_texts.append({
                    "file_path": file_path,
                    "original_text": text,
                    "cleaned_text": cleaned,
                    "original_length": len(text),
                    "cleaned_length": len(cleaned)
                })
            
            context.set("cleaned_text", cleaned_texts)
            
            total_original = sum(ct["original_length"] for ct in cleaned_texts)
            total_cleaned = sum(ct["cleaned_length"] for ct in cleaned_texts)
            
            return StageResult(
                success=True,
                message=f"Cleaned {len(cleaned_texts)} text(s), reduced from {total_original} to {total_cleaned} characters",
                data={"cleaned_text": cleaned_texts},
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            return StageResult(
                success=False,
                message=f"Text cleaning failed: {str(e)}",
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
    
    def _clean_text(self, text: str) -> str:
        """Apply cleaning operations to text"""
        if not text:
            return ""
        
        cleaned = text
        
        # Normalize unicode characters
        if self.normalize_unicode:
            import unicodedata
            cleaned = unicodedata.normalize('NFKC', cleaned)
        
        # Remove extra whitespace
        if self.remove_extra_whitespace:
            # Replace multiple spaces with single space
            cleaned = re.sub(r' +', ' ', cleaned)
            # Replace multiple newlines with double newline
            cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
            # Strip leading/trailing whitespace from each line
            cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
        
        # Remove special characters (optional)
        if self.remove_special_chars:
            cleaned = re.sub(r'[^\w\s\.\,\!\?\;\:\'\"]', '', cleaned)
        
        # Remove page break markers
        cleaned = re.sub(r'---\s*PAGE\s*BREAK\s*---', '\n\n', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
