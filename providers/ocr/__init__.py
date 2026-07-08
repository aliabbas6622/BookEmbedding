"""OCR providers module"""
from providers.ocr.base import OCRProvider, OCRResult
from providers.ocr.tesseract import TesseractOCR

__all__ = ['OCRProvider', 'OCRResult', 'TesseractOCR']

# Registry of available OCR providers
OCR_PROVIDERS = {
    "tesseract": TesseractOCR
}


def get_ocr_provider(provider_name: str, **kwargs):
    """Factory function to get an OCR provider instance"""
    if provider_name not in OCR_PROVIDERS:
        raise ValueError(f"Unknown OCR provider: {provider_name}")
    
    provider_class = OCR_PROVIDERS[provider_name]
    return provider_class(**kwargs)
