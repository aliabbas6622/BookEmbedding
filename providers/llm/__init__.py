"""LLM providers module"""
from providers.llm.base import LLMProvider, LLMMessage, LLMResponse
from providers.llm.ollama import OllamaProvider

__all__ = ['LLMProvider', 'LLMMessage', 'LLMResponse', 'OllamaProvider']

# Registry of available LLM providers
LLM_PROVIDERS = {
    "ollama": OllamaProvider
}


def get_llm_provider(provider_name: str, **kwargs):
    """Factory function to get an LLM provider instance"""
    if provider_name not in LLM_PROVIDERS:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
    
    provider_class = LLM_PROVIDERS[provider_name]
    return provider_class(**kwargs)
