"""
Tesseract OCR provider implementation
"""
from typing import Dict, Any, Optional
from pathlib import Path

from providers.ocr.base import OCRProvider


class TesseractOCR(OCRProvider):
    """Tesseract OCR provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config or {})
        self.lang = self.config.get("lang", "eng")
        self.psm = self.config.get("psm", 3)  # Page segmentation mode
    
    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract"""
        try:
            # Try to use pytesseract if available
            try:
                import pytesseract
                from pdf2image import convert_from_path
                
                # Convert PDF to images
                images = convert_from_path(file_path)
                
                # Extract text from each page
                texts = []
                for i, image in enumerate(images):
                    text = pytesseract.image_to_string(
                        image,
                        lang=self.lang,
                        config=f'--psm {self.psm}'
                    )
                    texts.append(f"--- Page {i+1} ---\n{text}")
                
                full_text = "\n\n".join(texts)
                
                return {
                    "text": full_text,
                    "metadata": {
                        "provider": "tesseract",
                        "lang": self.lang,
                        "pages": len(images),
                        "file": file_path
                    }
                }
                
            except ImportError:
                # Fallback: mock extraction for testing
                return await self._mock_extraction(file_path)
                
        except Exception as e:
            return {
                "text": "",
                "metadata": {"error": str(e)}
            }
    
    async def _mock_extraction(self, file_path: str) -> Dict[str, Any]:
        """Mock extraction for when dependencies are not installed"""
        return {
            "text": f"[Mock OCR] Extracted text from {file_path}. Install pytesseract and pdf2image for real OCR.",
            "metadata": {
                "provider": "tesseract",
                "mock": True,
                "file": file_path
            }
        }
    
    def get_supported_formats(self) -> list:
        """Get supported file formats"""
        return [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
