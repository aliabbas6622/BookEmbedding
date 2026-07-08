"""
OCR extraction stage - extracts text from PDF documents
"""
from typing import Dict, Any, Optional

from ragstudio.pipeline.base import PipelineStage, PipelineContext


class OCRExtractionStage(PipelineStage):
    """Extracts text from documents using OCR"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("ocr_extraction", config)
        self.provider_name = config.get("provider", "tesseract")
        self.provider_config = config.get("provider_config", {})
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute OCR extraction"""
        file_path = context.get("file_path")
        
        if not file_path:
            context.add_error("No file path available. Run upload_validation first.")
            return context
        
        try:
            # Get OCR provider
            provider = self._get_provider()
            
            # Perform OCR
            result = await provider.extract_text(file_path)
            
            # Store extracted text
            context.set("raw_text", result.get("text", ""))
            context.set("ocr_metadata", result.get("metadata", {}))
            
            return context
            
        except Exception as e:
            context.add_error(f"OCR extraction failed: {str(e)}")
            raise
    
    def _get_provider(self):
        """Get OCR provider instance"""
        if self.provider_name == "tesseract":
            from providers.ocr.tesseract import TesseractOCR
            return TesseractOCR(self.provider_config)
        else:
            raise ValueError(f"Unknown OCR provider: {self.provider_name}")
