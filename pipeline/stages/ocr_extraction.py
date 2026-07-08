"""
Stage 2: OCR Text Extraction
Extracts text from PDF files using configured OCR provider
"""
from pathlib import Path
from typing import Dict, Any, List

from pipeline.stages.base import PipelineStage, StageResult, PipelineContext
from providers.ocr.base import OCRProvider


class OCRExtractionStage(PipelineStage):
    """Stage 2: Extract text from PDFs using OCR"""
    
    @property
    def name(self) -> str:
        return "ocr_extraction"
    
    @property
    def description(self) -> str:
        return "Extract text from PDF files using OCR"
    
    @property
    def required_inputs(self) -> List[str]:
        return ["validated_files"]
    
    @property
    def outputs(self) -> List[str]:
        return ["extracted_text", "ocr_results"]
    
    def __init__(self, ocr_provider: OCRProvider):
        self.ocr_provider = ocr_provider
    
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute OCR extraction stage"""
        from datetime import datetime
        started_at = datetime.now()
        
        try:
            # Initialize OCR provider if needed
            if not self.ocr_provider.is_available():
                if not self.ocr_provider.initialize():
                    return StageResult(
                        success=False,
                        message="OCR provider initialization failed",
                        started_at=started_at,
                        completed_at=datetime.now()
                    )
            
            validated_files = context.get("validated_files")
            if not validated_files:
                return StageResult(
                    success=False,
                    message="No validated files found",
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            extracted_texts = []
            ocr_results = []
            
            for file_path_str in validated_files:
                file_path = Path(file_path_str)
                
                try:
                    # Extract text using OCR
                    ocr_result = self.ocr_provider.extract_text(file_path)
                    
                    extracted_texts.append({
                        "file_path": file_path_str,
                        "text": ocr_result.text,
                        "confidence": ocr_result.confidence
                    })
                    
                    ocr_results.append({
                        "file_path": file_path_str,
                        "text": ocr_result.text,
                        "pages": ocr_result.pages,
                        "confidence": ocr_result.confidence
                    })
                    
                except Exception as e:
                    context.add_error(f"OCR failed for {file_path}: {str(e)}")
                    extracted_texts.append({
                        "file_path": file_path_str,
                        "text": "",
                        "error": str(e)
                    })
            
            if not extracted_texts:
                return StageResult(
                    success=False,
                    message="No text extracted from any files",
                    error="; ".join(context.errors),
                    started_at=started_at,
                    completed_at=datetime.now()
                )
            
            context.set("extracted_text", extracted_texts)
            context.set("ocr_results", ocr_results)
            
            total_chars = sum(len(et["text"]) for et in extracted_texts)
            
            return StageResult(
                success=True,
                message=f"Extracted text from {len(extracted_texts)} file(s), {total_chars} characters",
                data={
                    "extracted_text": extracted_texts,
                    "ocr_results": ocr_results
                },
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            return StageResult(
                success=False,
                message=f"OCR extraction failed: {str(e)}",
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
