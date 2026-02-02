"""
Production-Ready Caching Layer with TTL, LRU Eviction, and Persistence

A high-performance, thread-safe caching solution for reducing database load
in high-traffic web applications.

Features:
- Time-to-Live (TTL) with per-item and default configuration
- LRU (Least Recently Used) eviction strategy
- Optional file-based persistence
- Comprehensive error handling and edge case management
- Full test suite with 14+ test cases
"""

import time
import json
import os
from typing import Any, Optional, Dict, List
from collections import OrderedDict
from threading import Lock
from dataclasses import dataclass
import sys


@dataclass
class CacheEntry:
    """
    Represents a single cache entry with metadata.
    
    Attributes:
        key: Cache key
        value: Stored value
        created_at: Timestamp when entry was created
        expires_at: Timestamp when entry expires (None = never expires)
        last_accessed: Timestamp of last access (for LRU)
    """
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    last_accessed: float
    
    def is_expired(self) -> bool:
        """Check if entry has expired based on current time."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def update_access_time(self) -> None:
        """Update the last accessed timestamp to current time."""
        self.last_accessed = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize entry to dictionary for persistence."""
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'last_accessed': self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Deserialize entry from dictionary."""
        return cls(
            key=data['key'],
            value=data['value'],
            created_at=data['created_at'],
            expires_at=data['expires_at'],
            last_accessed=data['last_accessed']
        )


class CacheConfig:
    """
    Configuration for Cache instance.
    
    Attributes:
        max_size: Maximum number of entries (must be positive)
        default_ttl: Default time-to-live in seconds (None = no expiration)
        storage_file: Path to persistence file (None = no persistence)
        enable_persistence: Enable/disable persistence
        auto_cleanup: Automatically remove expired entries on access
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl: Optional[float] = None,
        storage_file: Optional[str] = None,
        enable_persistence: bool = True,
        auto_cleanup: bool = True
    ):
        # Validate max_size
        if max_size <= 0:
            raise ValueError(f"max_size must be positive, got {max_size}")
        
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.storage_file = storage_file
        self.enable_persistence = enable_persistence and storage_file is not None
        self.auto_cleanup = auto_cleanup


class Cache:
    """
    Production-ready cache with TTL, LRU eviction, and persistence.
    
    Thread-safe implementation suitable for high-traffic applications.
    Handles edge cases gracefully with comprehensive error handling.
    
    Example:
        >>> config = CacheConfig(max_size=1000, default_ttl=3600)
        >>> cache = Cache(config)
        >>> cache.set('user:123', {'name': 'Alice', 'age': 30})
        >>> user = cache.get('user:123')
    """
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize cache with given configuration.
        
        Args:
            config: Cache configuration (uses defaults if None)
        """
        self.config = config or CacheConfig()
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        # Load from persistence if available
        if self.config.enable_persistence:
            self._load_from_storage()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """
        Set a value in the cache with optional TTL.
        
        Args:
            key: Cache key (must be non-empty string)
            value: Value to store (will be serialized for persistence)
            ttl: Time to live in seconds (overrides default_ttl, None = use default)
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            ValueError: If key is empty or invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        
        with self._lock:
            try:
                # Remove expired entries if auto_cleanup is enabled
                if self.config.auto_cleanup:
                    self._cleanup_expired()
                
                # Determine effective TTL
                effective_ttl = ttl if ttl is not None else self.config.default_ttl
                
                # Check if we need to evict (key doesn't exist and at capacity)
                if key not in self._cache and len(self._cache) >= self.config.max_size:
                    # Try to evict expired entries first
                    self._cleanup_expired()
                    
                    # If still at capacity, evict LRU
                    if len(self._cache) >= self.config.max_size:
                        self._evict_lru()
                
                # Calculate expiration time
                current_time = time.time()
                expires_at = current_time + effective_ttl if effective_ttl is not None else None
                
                # Create entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=current_time,
                    expires_at=expires_at,
                    last_accessed=current_time
                )
                
                # Remove old entry if exists (to update position)
                if key in self._cache:
                    del self._cache[key]
                
                # Add to cache
                self._cache[key] = entry
                
                # Persist to storage
                if self.config.enable_persistence:
                    self._save_to_storage()
                
                return True
            
            except Exception as e:
                print(f"Error setting cache key '{key}': {e}", file=sys.stderr)
                return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
        
        Returns:
            Cached value or default
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return default
            
            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                
                if self.config.enable_persistence:
                    self._save_to_storage()
                
                return default
            
            # Update access time and stats
            entry.update_access_time()
            self._stats['hits'] += 1
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            
            return entry.value
    
    def has(self, key: str) -> bool:
        """
        Check if key exists and is not expired.
        
        Args:
            key: Cache key
        
        Returns:
            True if key exists and not expired
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return False
            
            if entry.is_expired():
                del self._cache[key]
                self._stats['expirations'] += 1
                
                if self.config.enable_persistence:
                    self._save_to_storage()
                
                return False
            
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                
                if self.config.enable_persistence:
                    self._save_to_storage()
                
                return True
            
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            
            if self.config.enable_persistence:
                self._save_to_storage()
    
    def size(self) -> int:
        """
        Get current cache size (excluding expired entries).
        
        Returns:
            Number of valid (non-expired) entries
        """
        with self._lock:
            if self.config.auto_cleanup:
                self._cleanup_expired()
            return len(self._cache)
    
    def keys(self) -> List[str]:
        """
        Get all keys (excluding expired entries).
        
        Returns:
            List of cache keys
        """
        with self._lock:
            if self.config.auto_cleanup:
                self._cleanup_expired()
            return list(self._cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics including hits, misses, etc.
        """
        with self._lock:
            if self.config.auto_cleanup:
                self._cleanup_expired()
            
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.config.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.2f}%",
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations']
            }
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry (internal method)."""
        if not self._cache:
            return
        
        # Find entry with oldest last_accessed time
        lru_key = min(self._cache.keys(), 
                      key=lambda k: self._cache[k].last_accessed)
        
        del self._cache[lru_key]
        self._stats['evictions'] += 1
    
    def _cleanup_expired(self) -> int:
        """
        Remove all expired entries (internal method).
        
        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expirations'] += 1
        
        if expired_keys and self.config.enable_persistence:
            self._save_to_storage()
        
        return len(expired_keys)
    
    def _save_to_storage(self) -> None:
        """Save cache to file (internal method)."""
        if not self.config.storage_file:
            return
        
        try:
            data = {
                'version': '1.0',
                'timestamp': time.time(),
                'entries': [entry.to_dict() for entry in self._cache.values()]
            }
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.config.storage_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Atomic rename
            os.replace(temp_file, self.config.storage_file)
        
        except Exception as e:
            print(f"Error saving cache to storage: {e}", file=sys.stderr)
    
    def _load_from_storage(self) -> None:
        """Load cache from file (internal method)."""
        if not self.config.storage_file or not os.path.exists(self.config.storage_file):
            return
        
        try:
            with open(self.config.storage_file, 'r') as f:
                data = json.load(f)
            
            # Validate data structure
            if not isinstance(data, dict) or 'entries' not in data:
                print("Invalid cache data format", file=sys.stderr)
                return
            
            current_time = time.time()
            loaded_count = 0
            
            for entry_data in data['entries']:
                try:
                    entry = CacheEntry.from_dict(entry_data)
                    
                    # Skip expired entries
                    if entry.expires_at and current_time > entry.expires_at:
                        continue
                    
                    self._cache[entry.key] = entry
                    loaded_count += 1
                
                except Exception as e:
                    print(f"Error loading cache entry: {e}", file=sys.stderr)
                    continue
            
            print(f"Loaded {loaded_count} entries from cache storage")
        
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in cache file: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error loading cache from storage: {e}", file=sys.stderr)


# ============================================================================
# COMPREHENSIVE TEST SUITE
# ============================================================================

class CacheTestSuite:
    """
    Comprehensive test suite for production cache implementation.
    
    Tests all core functionality, edge cases, and error handling.
    """
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []
        self.test_storage_file = 'test_cache_storage.json'
    
    def cleanup(self) -> None:
        """Clean up test files."""
        if os.path.exists(self.test_storage_file):
            os.remove(self.test_storage_file)
        
        temp_file = self.test_storage_file + '.tmp'
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    def assert_test(self, condition: bool, test_name: str, 
                   expected: str, actual: str) -> None:
        """Record test result with details."""
        if condition:
            self.passed += 1
            status = "✅ PASS"
        else:
            self.failed += 1
            status = "❌ FAIL"
        
        self.test_results.append({
            'name': test_name,
            'status': status,
            'expected': expected,
            'actual': actual
        })
        
        print(f"{status}: {test_name}")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        print()
    
    def run_all_tests(self) -> None:
        """Execute all test cases."""
        print("=" * 70)
        print("🧪 PRODUCTION CACHE TEST SUITE")
        print("=" * 70)
        print()
        
        self.cleanup()
        
        # Core functionality tests
        self.test01_basic_set_get()
        self.test02_ttl_expiration()
        self.test03_lru_eviction()
        self.test04_custom_ttl_override()
        self.test05_persistence()
        self.test06_has_method()
        self.test07_delete_method()
        self.test08_clear_method()
        self.test09_size_method()
        self.test10_keys_method()
        
        # Edge case tests
        self.test11_expired_item_returns_none()
        self.test12_updating_existing_key()
        self.test13_lru_eviction_order()
        self.test14_persistence_disabled()
        self.test15_invalid_inputs()
        self.test16_zero_max_size()
        
        self.cleanup()
        self.print_summary()
    
    def test01_basic_set_get(self) -> None:
        """Test 1: Basic set and get operations"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('key1', 'value1')
        cache.set('key2', {'name': 'test', 'age': 30})
        
        result1 = cache.get('key1')
        result2 = cache.get('key2')
        
        self.assert_test(
            result1 == 'value1' and result2 == {'name': 'test', 'age': 30},
            "Test 1: Basic set and get",
            "key1='value1', key2={'name': 'test', 'age': 30}",
            f"key1='{result1}', key2={result2}"
        )
    
    def test02_ttl_expiration(self) -> None:
        """Test 2: TTL expiration with setTimeout"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('temp', 'expires soon', ttl=0.2)  # 200ms TTL
        
        before = cache.get('temp')
        time.sleep(0.3)  # Wait 300ms
        after = cache.get('temp')
        
        self.assert_test(
            before == 'expires soon' and after is None,
            "Test 2: TTL expiration",
            "Before='expires soon', After=None",
            f"Before='{before}', After={after}"
        )
    
    def test03_lru_eviction(self) -> None:
        """Test 3: LRU eviction when cache is full"""
        cache = Cache(CacheConfig(max_size=3, enable_persistence=False))
        
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        # Access 'a' to make it recently used
        cache.get('a')
        
        # Add 'd', should evict 'b' (least recently used)
        cache.set('d', 4)
        
        has_a = cache.has('a')
        has_b = cache.has('b')
        has_c = cache.has('c')
        has_d = cache.has('d')
        
        self.assert_test(
            has_a and not has_b and has_c and has_d,
            "Test 3: LRU eviction when full",
            "a=True, b=False (evicted), c=True, d=True",
            f"a={has_a}, b={has_b}, c={has_c}, d={has_d}"
        )
    
    def test04_custom_ttl_override(self) -> None:
        """Test 4: Custom TTL override"""
        config = CacheConfig(default_ttl=10.0, enable_persistence=False)
        cache = Cache(config)
        
        cache.set('default', 'uses default ttl')
        cache.set('custom', 'custom ttl', ttl=0.2)
        
        time.sleep(0.3)
        
        default_exists = cache.has('default')
        custom_exists = cache.has('custom')
        
        self.assert_test(
            default_exists and not custom_exists,
            "Test 4: Custom TTL override",
            "default=True, custom=False (expired)",
            f"default={default_exists}, custom={custom_exists}"
        )
    
    def test05_persistence(self) -> None:
        """Test 5: Persistence to storage"""
        self.cleanup()
        
        # Create cache and add data
        config1 = CacheConfig(storage_file=self.test_storage_file)
        cache1 = Cache(config1)
        cache1.set('persist1', 'value1')
        cache1.set('persist2', {'data': 'value2'})
        
        # Create new cache instance - should load from storage
        config2 = CacheConfig(storage_file=self.test_storage_file)
        cache2 = Cache(config2)
        
        result1 = cache2.get('persist1')
        result2 = cache2.get('persist2')
        
        self.assert_test(
            result1 == 'value1' and result2 == {'data': 'value2'},
            "Test 5: Persistence",
            "persist1='value1', persist2={'data': 'value2'}",
            f"persist1='{result1}', persist2={result2}"
        )
    
    def test06_has_method(self) -> None:
        """Test 6: has() method"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('exists', 'value')
        
        has_exists = cache.has('exists')
        has_missing = cache.has('missing')
        
        self.assert_test(
            has_exists and not has_missing,
            "Test 6: has() method",
            "exists=True, missing=False",
            f"exists={has_exists}, missing={has_missing}"
        )
    
    def test07_delete_method(self) -> None:
        """Test 7: delete() method"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('delete_me', 'value')
        
        deleted = cache.delete('delete_me')
        still_exists = cache.has('delete_me')
        delete_missing = cache.delete('not_there')
        
        self.assert_test(
            deleted and not still_exists and not delete_missing,
            "Test 7: delete() method",
            "deleted=True, exists=False, delete_missing=False",
            f"deleted={deleted}, exists={still_exists}, delete_missing={delete_missing}"
        )
    
    def test08_clear_method(self) -> None:
        """Test 8: clear() method"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        size_before = cache.size()
        cache.clear()
        size_after = cache.size()
        
        self.assert_test(
            size_before == 3 and size_after == 0,
            "Test 8: clear() method",
            "size_before=3, size_after=0",
            f"size_before={size_before}, size_after={size_after}"
        )
    
    def test09_size_method(self) -> None:
        """Test 9: size() method"""
        cache = Cache(CacheConfig(enable_persistence=False))
        
        size_empty = cache.size()
        cache.set('a', 1)
        cache.set('b', 2)
        size_two = cache.size()
        cache.delete('a')
        size_one = cache.size()
        
        self.assert_test(
            size_empty == 0 and size_two == 2 and size_one == 1,
            "Test 9: size() method",
            "empty=0, two=2, one=1",
            f"empty={size_empty}, two={size_two}, one={size_one}"
        )
    
    def test10_keys_method(self) -> None:
        """Test 10: keys() method"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        keys = cache.keys()
        
        self.assert_test(
            set(keys) == {'a', 'b', 'c'},
            "Test 10: keys() method",
            "keys=['a', 'b', 'c']",
            f"keys={keys}"
        )
    
    def test11_expired_item_returns_none(self) -> None:
        """Test 11: Edge case - expired item returns None"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('expires', 'value', ttl=0.1)
        
        time.sleep(0.2)
        result = cache.get('expires')
        exists = cache.has('expires')
        size = cache.size()
        
        self.assert_test(
            result is None and not exists and size == 0,
            "Test 11: Expired item returns None",
            "result=None, exists=False, size=0",
            f"result={result}, exists={exists}, size={size}"
        )
    
    def test12_updating_existing_key(self) -> None:
        """Test 12: Edge case - updating existing key"""
        cache = Cache(CacheConfig(enable_persistence=False))
        cache.set('update', 'old')
        cache.set('update', 'new')
        
        result = cache.get('update')
        size = cache.size()
        
        self.assert_test(
            result == 'new' and size == 1,
            "Test 12: Updating existing key",
            "value='new', size=1",
            f"value='{result}', size={size}"
        )
    
    def test13_lru_eviction_order(self) -> None:
        """Test 13: Edge case - LRU eviction order"""
        cache = Cache(CacheConfig(max_size=3, enable_persistence=False))
        
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        # Access 'a' and 'c', making 'b' the LRU
        cache.get('a')
        cache.get('c')
        
        # Add 'd', should evict 'b'
        cache.set('d', 4)
        
        has_a = cache.has('a')
        has_b = cache.has('b')
        has_c = cache.has('c')
        has_d = cache.has('d')
        
        self.assert_test(
            has_a and not has_b and has_c and has_d,
            "Test 13: LRU eviction order (middle item accessed)",
            "a=True, b=False (evicted), c=True, d=True",
            f"a={has_a}, b={has_b}, c={has_c}, d={has_d}"
        )
    
    def test14_persistence_disabled(self) -> None:
        """Test 14: Edge case - persistence disabled"""
        config = CacheConfig(storage_file=self.test_storage_file, 
                           enable_persistence=False)
        cache = Cache(config)
        cache.set('test', 'value')
        
        # File should not be created
        file_exists = os.path.exists(self.test_storage_file)
        
        self.assert_test(
            not file_exists,
            "Test 14: Persistence disabled",
            "file_exists=False",
            f"file_exists={file_exists}"
        )
    
    def test15_invalid_inputs(self) -> None:
        """Test 15: Edge case - invalid inputs"""
        cache = Cache(CacheConfig(enable_persistence=False))
        
        try:
            cache.set('', 'value')  # Empty key
            invalid_handled = False
        except ValueError:
            invalid_handled = True
        
        result = cache.get('nonexistent', default='default_value')
        
        self.assert_test(
            invalid_handled and result == 'default_value',
            "Test 15: Invalid inputs",
            "empty_key_raises_error=True, default_returned=True",
            f"empty_key_raises_error={invalid_handled}, default='{result}'"
        )
    
    def test16_zero_max_size(self) -> None:
        """Test 16: Edge case - invalid max_size"""
        try:
            config = CacheConfig(max_size=0)
            cache = Cache(config)
            error_raised = False
        except ValueError:
            error_raised = True
        
        self.assert_test(
            error_raised,
            "Test 16: Zero/negative max_size raises error",
            "error_raised=True",
            f"error_raised={error_raised}"
        )
    
    def print_summary(self) -> None:
        """Print comprehensive test summary."""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests:   {total}")
        print(f"✅ Passed:     {self.passed}")
        print(f"❌ Failed:     {self.failed}")
        print(f"Success Rate:  {success_rate:.1f}%")
        print("=" * 70)
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if "FAIL" in result['status']:
                    print(f"  - {result['name']}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 PRODUCTION CACHE SYSTEM - EXAMPLE USAGE")
    print("=" * 70)
    print()
    
    # Create production cache configuration
    config = CacheConfig(
        max_size=1000,
        default_ttl=3600.0,  # 1 hour default
        storage_file='production_cache.json',
        enable_persistence=True
    )
    
    cache = Cache(config)
    
    # Example operations
    print("Setting cache entries...")
    cache.set('user:123', {'name': 'Alice', 'email': 'alice@example.com'})
    cache.set('session:abc', 'active', ttl=300.0)  # 5 minute session
    cache.set('config:app', {'theme': 'dark', 'lang': 'en'})
    
    print(f"\nCache size: {cache.size()}")
    print(f"Keys: {cache.keys()}")
    
    print("\nGetting values...")
    print(f"user:123 = {cache.get('user:123')}")
    print(f"session:abc = {cache.get('session:abc')}")
    
    print("\nCache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 70)
    print()
    
    # Run comprehensive test suite
    test_suite = CacheTestSuite()
    test_suite.run_all_tests()
    
    # Cleanup example cache
    if os.path.exists('production_cache.json'):
        os.remove('production_cache.json')