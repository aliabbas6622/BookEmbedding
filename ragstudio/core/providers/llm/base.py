"""
Base class for LLM providers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate text from a prompt
        
        Args:
            prompt: Input prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Chat with the LLM using conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name being used"""
        pass
    
    async def correct_ocr_text(
        self,
        ocr_text: str,
        document_type: Optional[str] = None
    ) -> str:
        """
        Correct OCR errors in text
        
        Args:
            ocr_text: Raw OCR extracted text
            document_type: Optional document type for context
            
        Returns:
            Corrected text
        """
        system_prompt = """You are an OCR text correction assistant. 
        Your task is to fix common OCR errors while preserving the original meaning and structure.
        Common issues to fix:
        - Misrecognized characters (e.g., '0' vs 'O', '1' vs 'l')
        - Broken words due to line breaks
        - Missing or extra spaces
        - Punctuation errors
        
        Do not change the content meaning, only fix OCR artifacts."""
        
        prompt = f"""Please correct the following OCR-extracted text:

{ocr_text}

Corrected version:"""
        
        return await self.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=max_tokens
        )
