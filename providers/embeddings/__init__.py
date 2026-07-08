"""Embedding providers module"""
from providers.embeddings.base import EmbeddingProvider, EmbeddingResult
from providers.embeddings.sentence_transformers import SentenceTransformersEmbedding

__all__ = ['EmbeddingProvider', 'EmbeddingResult', 'SentenceTransformersEmbedding']

# Registry of available embedding providers
EMBEDDING_PROVIDERS = {
    "sentence_transformers": SentenceTransformersEmbedding
}


def get_embedding_provider(provider_name: str, **kwargs):
    """Factory function to get an embedding provider instance"""
    if provider_name not in EMBEDDING_PROVIDERS:
        raise ValueError(f"Unknown embedding provider: {provider_name}")
    
    provider_class = EMBEDDING_PROVIDERS[provider_name]
    return provider_class(**kwargs)
