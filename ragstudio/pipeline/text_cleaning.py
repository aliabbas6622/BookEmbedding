"""
Text cleaning stage - cleans and normalizes extracted text
"""
import re
from typing import Dict, Any, Optional

from ragstudio.pipeline.base import PipelineStage, PipelineContext


class TextCleaningStage(PipelineStage):
    """Cleans and normalizes extracted text"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("text_cleaning", config)
        self.remove_extra_whitespace = config.get("remove_extra_whitespace", True)
        self.remove_special_chars = config.get("remove_special_chars", False)
        self.normalize_unicode = config.get("normalize_unicode", True)
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute text cleaning"""
        raw_text = context.get("raw_text")
        
        if not raw_text:
            context.add_error("No raw text available. Run ocr_extraction first.")
            return context
        
        cleaned_text = raw_text
        
        # Remove extra whitespace
        if self.remove_extra_whitespace:
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        
        # Normalize unicode
        if self.normalize_unicode:
            import unicodedata
            cleaned_text = unicodedata.normalize('NFKC', cleaned_text)
        
        # Remove special characters (optional)
        if self.remove_special_chars:
            cleaned_text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\']', '', cleaned_text)
        
        # Strip leading/trailing whitespace
        cleaned_text = cleaned_text.strip()
        
        # Store cleaned text
        context.set("cleaned_text", cleaned_text)
        
        return context
