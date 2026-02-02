import time
import json
import os
from typing import Any, Optional, Dict
from collections import OrderedDict
from dataclasses import dataclass, asdict
from threading import Lock


@dataclass
class CacheConfig:
    """Configuration for the cache"""
    max_size: int = 100
    default_ttl: Optional[float] = None  # seconds, None = no expiration
    persistence_file: Optional[str] = None
    auto_save: bool = True
    eviction_policy: str = "lru"  # lru or fifo


@dataclass
class CacheEntry:
    """Internal representation of a cache entry"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    access_count: int = 0
    last_accessed: float = 0.0


class Cache:
    """
    A configurable cache with TTL, LRU eviction, and persistence.
    
    Features:
    - TTL (Time To Live) support per entry
    - LRU (Least Recently Used) eviction
    - Persistent storage to disk
    - Thread-safe operations
    - Configurable max size
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        
        # Load from persistence if file exists
        if self.config.persistence_file and os.path.exists(self.config.persistence_file):
            self._load_from_disk()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (overrides default_ttl)
        """
        with self._lock:
            current_time = time.time()
            
            # Use provided TTL, fall back to default, or None
            effective_ttl = ttl if ttl is not None else self.config.default_ttl
            expires_at = current_time + effective_ttl if effective_ttl else None
            
            # Check if we need to evict
            if key not in self._store and len(self._store) >= self.config.max_size:
                self._evict()
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                expires_at=expires_at,
                last_accessed=current_time
            )
            
            # Remove old entry if exists (to update position in OrderedDict)
            if key in self._store:
                del self._store[key]
            
            self._store[key] = entry
            
            # Auto-save if enabled
            if self.config.auto_save and self.config.persistence_file:
                self._save_to_disk()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        with self._lock:
            entry = self._store.get(key)
            
            if entry is None:
                return default
            
            # Check if expired
            if entry.expires_at and time.time() > entry.expires_at:
                del self._store[key]
                return default
            
            # Update access info
            entry.last_accessed = time.time()
            entry.access_count += 1
            
            # Move to end for LRU
            self._store.move_to_end(key)
            
            return entry.value
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                if self.config.auto_save and self.config.persistence_file:
                    self._save_to_disk()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._store.clear()
            if self.config.auto_save and self.config.persistence_file:
                self._save_to_disk()
    
    def _evict(self) -> None:
        """Evict the least recently used entry."""
        if not self._store:
            return
        
        # OrderedDict maintains insertion order
        # For LRU, we've been moving accessed items to end
        # So first item is least recently used
        self._store.popitem(last=False)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._store.items()
                if entry.expires_at and current_time > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._store[key]
            
            if expired_keys and self.config.auto_save and self.config.persistence_file:
                self._save_to_disk()
            
            return len(expired_keys)
    
    def _save_to_disk(self) -> None:
        """Save cache to disk."""
        if not self.config.persistence_file:
            return
        
        data = {
            "entries": [
                {
                    "key": entry.key,
                    "value": entry.value,
                    "created_at": entry.created_at,
                    "expires_at": entry.expires_at,
                    "access_count": entry.access_count,
                    "last_accessed": entry.last_accessed
                }
                for entry in self._store.values()
            ]
        }
        
        with open(self.config.persistence_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_from_disk(self) -> None:
        """Load cache from disk."""
        if not self.config.persistence_file:
            return
        
        try:
            with open(self.config.persistence_file, 'r') as f:
                data = json.load(f)
            
            current_time = time.time()
            
            for entry_data in data.get("entries", []):
                # Skip expired entries
                if entry_data["expires_at"] and current_time > entry_data["expires_at"]:
                    continue
                
                entry = CacheEntry(
                    key=entry_data["key"],
                    value=entry_data["value"],
                    created_at=entry_data["created_at"],
                    expires_at=entry_data["expires_at"],
                    access_count=entry_data["access_count"],
                    last_accessed=entry_data["last_accessed"]
                )
                self._store[entry.key] = entry
        except Exception as e:
            print(f"Error loading cache from disk: {e}")
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._store)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._store.values())
            return {
                "size": len(self._store),
                "max_size": self.config.max_size,
                "total_accesses": total_accesses,
                "entries": len(self._store)
            }


# Example usage
if __name__ == "__main__":
    # Create cache with custom config
    config = CacheConfig(
        max_size=5,
        default_ttl=10.0,  # 10 seconds default TTL
        persistence_file="cache.json",
        auto_save=True
    )
    
    cache = Cache(config)
    
    # Set some values
    cache.set("user:1", {"name": "Alice", "age": 30})
    cache.set("user:2", {"name": "Bob", "age": 25})
    cache.set("session:abc", "active", ttl=5.0)  # Custom TTL
    
    # Get values
    print("user:1 =", cache.get("user:1"))
    print("user:2 =", cache.get("user:2"))
    print("session:abc =", cache.get("session:abc"))
    
    # Add more to trigger eviction
    for i in range(3, 8):
        cache.set(f"user:{i}", {"name": f"User{i}", "age": 20 + i})
    
    print("\nAfter adding more entries:")
    print("Cache stats:", cache.stats())
    
    # Wait for expiration
    print("\nWaiting 6 seconds for session to expire...")
    time.sleep(6)
    print("session:abc after expiration =", cache.get("session:abc"))
    
    # Cleanup expired
    removed = cache.cleanup_expired()
    print(f"Cleaned up {removed} expired entries")
    
    print("\nFinal cache stats:", cache.stats())