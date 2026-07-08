"""
Base class for OCR providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class OCRProvider(ABC):
    """Base class for OCR providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    async def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a document
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with 'text' and optional 'metadata'
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list:
        """Get list of supported file formats"""
        pass
