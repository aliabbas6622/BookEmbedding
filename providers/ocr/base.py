"""
Provider interface for OCR (Optical Character Recognition)
All OCR providers must implement this interface
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional


class OCRResult:
    """Represents OCR extraction result"""
    
    def __init__(self, text: str, confidence: float = 0.0, 
                 bounding_boxes: Optional[List[Dict]] = None,
                 pages: Optional[List[Dict]] = None):
        self.text = text
        self.confidence = confidence
        self.bounding_boxes = bounding_boxes or []
        self.pages = pages or []  # For multi-page documents
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "confidence": self.confidence,
            "bounding_boxes": self.bounding_boxes,
            "pages": self.pages
        }


class OCRProvider(ABC):
    """Abstract base class for OCR providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the OCR provider (load models, etc.)
        Returns True if successful
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> OCRResult:
        """
        Extract text from a PDF or image file
        
        Args:
            file_path: Path to the file
            
        Returns:
            OCRResult containing extracted text and metadata
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready to use"""
        pass
    
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats"""
        return [".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"]
