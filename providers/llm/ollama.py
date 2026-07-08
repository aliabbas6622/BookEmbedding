"""
Ollama LLM Provider Implementation
Supports local Ollama models
"""
import requests
from typing import List, Dict, Any, Optional, Generator

from providers.llm.base import LLMProvider, LLMMessage, LLMResponse


class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local model inference"""
    
    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.base_url = "http://localhost:11434"
        self._initialized = False
        self._api_key: Optional[str] = None
    
    @property
    def name(self) -> str:
        return "ollama"
    
    def initialize(self, api_key: Optional[str] = None,
                   base_url: Optional[str] = None,
                   model: Optional[str] = None) -> bool:
        """Initialize Ollama provider"""
        if base_url:
            self.base_url = base_url.rstrip('/')
        if model:
            self.model = model
        self._api_key = api_key
        
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                self._initialized = True
                return True
        except (requests.RequestException, Exception):
            pass
        
        self._initialized = False
        return False
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        if not self._initialized:
            return self.initialize()
        return self._initialized
    
    def get_supported_models(self) -> List[str]:
        """Get list of available Ollama models"""
        if not self.is_available():
            return []
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model.get("name", "") for model in data.get("models", [])]
        except Exception:
            pass
        return []
    
    def generate(self, messages: List[LLMMessage],
                 temperature: float = 0.7,
                 max_tokens: Optional[int] = None,
                 **kwargs) -> LLMResponse:
        """Generate a response using Ollama"""
        if not self.is_available():
            raise RuntimeError("Ollama is not available")
        
        # Convert messages to Ollama format
        ollama_messages = [msg.to_dict() for msg in messages]
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options
        if "options" in kwargs:
            payload["options"].update(kwargs["options"])
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            content = result.get("message", {}).get("content", "")
            
            return LLMResponse(
                content=content,
                model=self.model,
                usage=result.get("usage", {}),
                raw_response=result
            )
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {str(e)}")
    
    def generate_stream(self, messages: List[LLMMessage],
                        temperature: float = 0.7,
                        max_tokens: Optional[int] = None,
                        **kwargs) -> Generator[str, None, None]:
        """Generate a streaming response using Ollama"""
        if not self.is_available():
            raise RuntimeError("Ollama is not available")
        
        # Convert messages to Ollama format
        ollama_messages = [msg.to_dict() for msg in messages]
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            with requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        import json
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama streaming request failed: {str(e)}")
