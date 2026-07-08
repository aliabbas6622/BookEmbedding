"""
API Key Manager - handles multiple API keys with rotation, health checks, quotas, and retries
"""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class APIKey:
    """Represents an API key with metadata"""
    key: str
    provider: str
    name: str
    created_at: float = field(default_factory=time.time)
    is_active: bool = True
    quota_limit: Optional[int] = None
    quota_used: int = 0
    last_used: Optional[float] = None
    last_health_check: Optional[float] = None
    is_healthy: bool = True
    cooldown_until: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def reset_quota(self):
        """Reset quota usage"""
        self.quota_used = 0
    
    def can_use(self) -> bool:
        """Check if key can be used"""
        if not self.is_active:
            return False
        
        if not self.is_healthy:
            return False
        
        if self.cooldown_until and time.time() < self.cooldown_until:
            return False
        
        if self.quota_limit and self.quota_used >= self.quota_limit:
            return False
        
        return True
    
    def record_usage(self):
        """Record key usage"""
        self.last_used = time.time()
        self.quota_used += 1
    
    def enter_cooldown(self, duration_seconds: int = 60):
        """Put key in cooldown"""
        self.cooldown_until = time.time() + duration_seconds
    
    def record_failure(self):
        """Record a failure and potentially enter cooldown"""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.is_healthy = False
            self.enter_cooldown(300)  # 5 minute cooldown
    
    def record_success(self):
        """Record a success"""
        self.retry_count = 0
        self.is_healthy = True
        self.cooldown_until = None


class APIKeyManager:
    """Manages multiple API keys with rotation and health monitoring"""
    
    def __init__(self):
        self._keys: Dict[str, List[APIKey]] = {}  # provider -> list of keys
        self._current_key_index: Dict[str, int] = {}  # provider -> current key index
    
    def add_key(
        self,
        key: str,
        provider: str,
        name: str,
        quota_limit: Optional[int] = None,
        max_retries: int = 3
    ) -> APIKey:
        """Add a new API key"""
        api_key = APIKey(
            key=key,
            provider=provider,
            name=name,
            quota_limit=quota_limit,
            max_retries=max_retries
        )
        
        if provider not in self._keys:
            self._keys[provider] = []
            self._current_key_index[provider] = 0
        
        self._keys[provider].append(api_key)
        return api_key
    
    def remove_key(self, provider: str, key: str) -> bool:
        """Remove an API key"""
        if provider not in self._keys:
            return False
        
        for i, api_key in enumerate(self._keys[provider]):
            if api_key.key == key:
                self._keys[provider].pop(i)
                # Adjust current index if needed
                if self._current_key_index.get(provider, 0) >= len(self._keys[provider]):
                    self._current_key_index[provider] = 0
                return True
        
        return False
    
    def get_available_key(self, provider: str) -> Optional[APIKey]:
        """Get an available API key using round-robin rotation"""
        if provider not in self._keys or not self._keys[provider]:
            return None
        
        keys = self._keys[provider]
        start_index = self._current_key_index.get(provider, 0)
        
        # Try each key starting from current index
        for i in range(len(keys)):
            index = (start_index + i) % len(keys)
            key = keys[index]
            
            if key.can_use():
                self._current_key_index[provider] = index
                return key
        
        # No available keys
        return None
    
    def rotate_key(self, provider: str):
        """Manually rotate to next key for a provider"""
        if provider in self._keys and self._keys[provider]:
            current = self._current_key_index.get(provider, 0)
            self._current_key_index[provider] = (current + 1) % len(self._keys[provider])
    
    def record_usage(self, provider: str, key: str):
        """Record successful usage of a key"""
        if provider in self._keys:
            for api_key in self._keys[provider]:
                if api_key.key == key:
                    api_key.record_usage()
                    api_key.record_success()
                    break
    
    def record_failure(self, provider: str, key: str):
        """Record failed usage of a key"""
        if provider in self._keys:
            for api_key in self._keys[provider]:
                if api_key.key == key:
                    api_key.record_failure()
                    # Automatically rotate to next key
                    self.rotate_key(provider)
                    break
    
    def get_keys_for_provider(self, provider: str) -> List[APIKey]:
        """Get all keys for a provider"""
        return self._keys.get(provider, [])
    
    def get_all_providers(self) -> List[str]:
        """Get list of all providers with keys"""
        return list(self._keys.keys())
    
    async def health_check(self, provider: str, check_func) -> Dict[str, bool]:
        """
        Perform health check on all keys for a provider
        
        Args:
            provider: Provider name
            check_func: Async function that takes a key and returns bool
        """
        results = {}
        if provider not in self._keys:
            return results
        
        for api_key in self._keys[provider]:
            try:
                is_healthy = await check_func(api_key.key)
                api_key.is_healthy = is_healthy
                api_key.last_health_check = time.time()
                results[api_key.name] = is_healthy
            except Exception:
                api_key.is_healthy = False
                api_key.last_health_check = time.time()
                results[api_key.name] = False
        
        return results
    
    def get_stats(self, provider: str) -> Dict[str, Any]:
        """Get statistics for a provider's keys"""
        if provider not in self._keys:
            return {"total_keys": 0}
        
        keys = self._keys[provider]
        return {
            "total_keys": len(keys),
            "active_keys": sum(1 for k in keys if k.is_active),
            "healthy_keys": sum(1 for k in keys if k.is_healthy),
            "keys_in_cooldown": sum(1 for k in keys if k.cooldown_until and time.time() < k.cooldown_until),
            "quota_exhausted": sum(1 for k in keys if k.quota_limit and k.quota_used >= k.quota_limit),
            "total_quota_used": sum(k.quota_used for k in keys),
            "total_quota_limit": sum(k.quota_limit or 0 for k in keys)
        }
    
    def reset_all_quotas(self, provider: str):
        """Reset all quotas for a provider"""
        if provider in self._keys:
            for key in self._keys[provider]:
                key.reset_quota()
    
    def activate_key(self, provider: str, key: str) -> bool:
        """Activate a key"""
        if provider in self._keys:
            for api_key in self._keys[provider]:
                if api_key.key == key:
                    api_key.is_active = True
                    return True
        return False
    
    def deactivate_key(self, provider: str, key: str) -> bool:
        """Deactivate a key"""
        if provider in self._keys:
            for api_key in self._keys[provider]:
                if api_key.key == key:
                    api_key.is_active = False
                    return True
        return False
