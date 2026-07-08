"""
Provider interface for LLM (Large Language Model)
All LLM providers must implement this interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator


class LLMMessage:
    """Represents a chat message"""
    
    def __init__(self, role: str, content: str):
        self.role = role  # "system", "user", or "assistant"
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMResponse:
    """Represents LLM response"""
    
    def __init__(self, content: str, model: str = "", 
                 usage: Optional[Dict[str, int]] = None,
                 raw_response: Optional[Any] = None):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.raw_response = raw_response
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage
        }


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name"""
        pass
    
    @abstractmethod
    def initialize(self, api_key: Optional[str] = None, 
                   base_url: Optional[str] = None,
                   model: Optional[str] = None) -> bool:
        """
        Initialize the LLM provider
        
        Args:
            api_key: API key if required
            base_url: Base URL for API endpoint
            model: Default model to use
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def generate(self, messages: List[LLMMessage], 
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None,
                 **kwargs) -> LLMResponse:
        """
        Generate a response from the LLM
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific arguments
            
        Returns:
            LLMResponse with generated content
        """
        pass
    
    @abstractmethod
    def generate_stream(self, messages: List[LLMMessage],
                        temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> Generator[str, None, None]:
        """
        Generate a streaming response from the LLM
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific arguments
            
        Yields:
            Chunks of generated text
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready to use"""
        pass
    
    def get_supported_models(self) -> List[str]:
        """Return list of supported models"""
        return []
