"""Vector Index providers module"""
from providers.vector_index.base import VectorIndexProvider, SearchResult
from providers.vector_index.turbovec import TurboVec

__all__ = ['VectorIndexProvider', 'SearchResult', 'TurboVec']

# Registry of available vector index providers
VECTOR_INDEX_PROVIDERS = {
    "turbovec": TurboVec
}


def get_vector_index_provider(provider_name: str, **kwargs):
    """Factory function to get a vector index provider instance"""
    if provider_name not in VECTOR_INDEX_PROVIDERS:
        raise ValueError(f"Unknown vector index provider: {provider_name}")
    
    provider_class = VECTOR_INDEX_PROVIDERS[provider_name]
    return provider_class(**kwargs)
