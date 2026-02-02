"""
Caching System with TTL, LRU Eviction, and Persistence
"""

import time
import json
import os
from collections import OrderedDict
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class CacheEntry:
    """Represents a single cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float]
    last_accessed: float
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return self.expires_at is not None and time.time() > self.expires_at
    
    def update_access_time(self) -> None:
        """Update the last accessed timestamp"""
        self.last_accessed = time.time()


class Cache:
    """
    A configurable cache with TTL, LRU eviction, and persistence.
    
    Features:
    - TTL (Time To Live) support per entry
    - LRU (Least Recently Used) eviction
    - Persistent storage to disk
    - Configurable max size and default TTL
    """
    
    def __init__(
        self,
        max_size: int = 100,
        default_ttl: Optional[float] = None,
        storage_file: Optional[str] = None,
        enable_persistence: bool = True
    ):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of entries (default: 100)
            default_ttl: Default time-to-live in seconds (default: None = no expiration)
            storage_file: Path to persistence file (default: None)
            enable_persistence: Enable/disable persistence (default: True)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.storage_file = storage_file
        self.enable_persistence = enable_persistence and storage_file is not None
        
        # Using OrderedDict to maintain insertion order for LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Load from file if exists
        if self.enable_persistence and os.path.exists(self.storage_file):
            self._load_from_storage()
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
            ttl: Time to live in seconds (overrides default_ttl)
        """
        # Use provided TTL or default
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        # Remove expired entries first
        self._cleanup_expired()
        
        # Check if we need to evict (and key doesn't already exist)
        if key not in self._cache and len(self._cache) >= self.max_size:
            self._evict_lru()
        
        # Calculate expiration time
        current_time = time.time()
        expires_at = current_time + effective_ttl if effective_ttl else None
        
        # Create new entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=current_time,
            expires_at=expires_at,
            last_accessed=current_time
        )
        
        # Remove old entry if exists (to update position in OrderedDict)
        if key in self._cache:
            del self._cache[key]
        
        # Add to cache
        self._cache[key] = entry
        
        # Persist to storage
        if self.enable_persistence:
            self._save_to_storage()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        entry = self._cache.get(key)
        
        if entry is None:
            return default
        
        # Check if expired
        if entry.is_expired():
            del self._cache[key]
            if self.enable_persistence:
                self._save_to_storage()
            return default
        
        # Update access time
        entry.update_access_time()
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        
        return entry.value
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            if self.enable_persistence:
                self._save_to_storage()
            return True
        return False
    
    def has(self, key: str) -> bool:
        """
        Check if key exists and is not expired.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists and not expired
        """
        entry = self._cache.get(key)
        if not entry:
            return False
        
        if entry.is_expired():
            del self._cache[key]
            if self.enable_persistence:
                self._save_to_storage()
            return False
        
        return True
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        if self.enable_persistence:
            self._save_to_storage()
    
    def size(self) -> int:
        """Get current cache size (excluding expired entries)."""
        self._cleanup_expired()
        return len(self._cache)
    
    def keys(self) -> List[str]:
        """Get all keys (excluding expired entries)."""
        self._cleanup_expired()
        return list(self._cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        self._cleanup_expired()
        current_time = time.time()
        
        entries = []
        for key, entry in self._cache.items():
            entries.append({
                'key': key,
                'age': current_time - entry.created_at,
                'time_since_access': current_time - entry.last_accessed,
                'ttl': entry.expires_at - current_time if entry.expires_at else None
            })
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'entries': entries
        }
    
    def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return
        
        # First entry in OrderedDict is least recently used
        self._cache.popitem(last=False)
    
    def _cleanup_expired(self) -> None:
        """Remove all expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys and self.enable_persistence:
            self._save_to_storage()
    
    def _save_to_storage(self) -> None:
        """Save cache to file."""
        if not self.storage_file:
            return
        
        try:
            data = {
                'entries': [
                    {
                        'key': entry.key,
                        'value': entry.value,
                        'created_at': entry.created_at,
                        'expires_at': entry.expires_at,
                        'last_accessed': entry.last_accessed
                    }
                    for entry in self._cache.values()
                ]
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving cache to file: {e}")
    
    def _load_from_storage(self) -> None:
        """Load cache from file."""
        if not self.storage_file:
            return
        
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            current_time = time.time()
            
            for entry_data in data.get('entries', []):
                # Skip expired entries
                if entry_data['expires_at'] and current_time > entry_data['expires_at']:
                    continue
                
                entry = CacheEntry(
                    key=entry_data['key'],
                    value=entry_data['value'],
                    created_at=entry_data['created_at'],
                    expires_at=entry_data['expires_at'],
                    last_accessed=entry_data['last_accessed']
                )
                
                self._cache[entry.key] = entry
        except Exception as e:
            print(f"Error loading cache from file: {e}")


# ============================================================================
# TEST SUITE
# ============================================================================

class CacheTestSuite:
    """Comprehensive test suite for the Cache class"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_storage_file = 'test_cache.json'
    
    def assert_test(self, condition: bool, test_name: str, message: str = "") -> None:
        """Assert a test condition and track results"""
        if condition:
            self.passed += 1
            print(f"✅ PASS: {test_name}")
        else:
            self.failed += 1
            print(f"❌ FAIL: {test_name}")
            if message:
                print(f"   {message}")
    
    def cleanup(self) -> None:
        """Clean up test files"""
        if os.path.exists(self.test_storage_file):
            os.remove(self.test_storage_file)
    
    def run_all_tests(self) -> None:
        """Run all test cases"""
        print('🧪 Running Cache Test Suite\n')
        print('=' * 60)
        
        self.cleanup()
        
        self.test1_basic_set_get()
        self.test2_ttl_expiration()
        self.test3_lru_eviction()
        self.test4_persistence()
        self.test5_update_existing_key()
        self.test6_delete_operation()
        self.test7_has_method()
        self.test8_clear_cache()
        self.test9_multiple_expired_entries()
        self.test10_full_cache_with_ttl()
        self.test11_edge_cases()
        self.test12_access_order_lru()
        
        self.cleanup()
        self.print_summary()
    
    def test1_basic_set_get(self) -> None:
        """Test 1: Basic set and get operations"""
        cache = Cache(enable_persistence=False)
        cache.set('key1', 'value1')
        cache.set('key2', {'name': 'test'})
        
        self.assert_test(
            cache.get('key1') == 'value1',
            'Test 1a: Basic set/get string',
            f"Expected 'value1', got '{cache.get('key1')}'"
        )
        
        self.assert_test(
            cache.get('key2') == {'name': 'test'},
            'Test 1b: Basic set/get object',
            f"Expected dict with name='test'"
        )
    
    def test2_ttl_expiration(self) -> None:
        """Test 2: TTL expiration"""
        cache = Cache(enable_persistence=False)
        cache.set('temp', 'expires soon', ttl=0.1)  # 100ms TTL
        
        before_expire = cache.get('temp')
        time.sleep(0.15)  # Wait 150ms
        after_expire = cache.get('temp')
        
        self.assert_test(
            before_expire == 'expires soon' and after_expire is None,
            'Test 2: TTL expiration',
            f"Before: '{before_expire}', After: '{after_expire}'"
        )
    
    def test3_lru_eviction(self) -> None:
        """Test 3: LRU eviction when cache is full"""
        cache = Cache(max_size=3, enable_persistence=False)
        
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        # Access 'a' to make it recently used
        cache.get('a')
        
        # Add new item, 'b' should be evicted (least recently used)
        cache.set('d', 4)
        
        self.assert_test(
            cache.has('a') and cache.has('c') and cache.has('d') and not cache.has('b'),
            'Test 3: LRU eviction',
            f"Expected 'b' to be evicted. Has a:{cache.has('a')}, b:{cache.has('b')}, c:{cache.has('c')}, d:{cache.has('d')}"
        )
    
    def test4_persistence(self) -> None:
        """Test 4: Persistence to file"""
        self.cleanup()
        
        cache1 = Cache(storage_file=self.test_storage_file)
        cache1.set('persist1', 'value1')
        cache1.set('persist2', 'value2')
        
        # Create new cache instance - should load from storage
        cache2 = Cache(storage_file=self.test_storage_file)
        
        self.assert_test(
            cache2.get('persist1') == 'value1' and cache2.get('persist2') == 'value2',
            'Test 4: Persistence',
            f"Expected both values to persist. Got: '{cache2.get('persist1')}', '{cache2.get('persist2')}'"
        )
    
    def test5_update_existing_key(self) -> None:
        """Test 5: Updating existing key"""
        cache = Cache(enable_persistence=False)
        cache.set('update', 'old')
        cache.set('update', 'new')
        
        self.assert_test(
            cache.get('update') == 'new' and cache.size() == 1,
            'Test 5: Update existing key',
            f"Expected 'new' with size 1. Got '{cache.get('update')}' with size {cache.size()}"
        )
    
    def test6_delete_operation(self) -> None:
        """Test 6: Delete operation"""
        cache = Cache(enable_persistence=False)
        cache.set('delete_me', 'value')
        
        deleted = cache.delete('delete_me')
        still_exists = cache.has('delete_me')
        
        self.assert_test(
            deleted and not still_exists,
            'Test 6: Delete operation',
            f"Expected deleted=True, exists=False. Got deleted={deleted}, exists={still_exists}"
        )
    
    def test7_has_method(self) -> None:
        """Test 7: Has method with expiration"""
        cache = Cache(enable_persistence=False)
        cache.set('check', 'value', ttl=0.1)
        
        exists_before = cache.has('check')
        time.sleep(0.15)
        exists_after = cache.has('check')
        
        self.assert_test(
            exists_before and not exists_after,
            'Test 7: Has method with expiration',
            f"Expected True then False. Got {exists_before} then {exists_after}"
        )
    
    def test8_clear_cache(self) -> None:
        """Test 8: Clear cache"""
        cache = Cache(enable_persistence=False)
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        cache.clear()
        
        self.assert_test(
            cache.size() == 0 and not cache.has('a') and not cache.has('b'),
            'Test 8: Clear cache',
            f"Expected size 0. Got {cache.size()}"
        )
    
    def test9_multiple_expired_entries(self) -> None:
        """Test 9: Multiple expired entries cleanup"""
        cache = Cache(enable_persistence=False)
        cache.set('exp1', 'v1', ttl=0.1)
        cache.set('exp2', 'v2', ttl=0.1)
        cache.set('keep', 'v3')  # No TTL
        
        time.sleep(0.15)
        size = cache.size()
        
        self.assert_test(
            size == 1 and cache.has('keep'),
            'Test 9: Multiple expired entries cleanup',
            f"Expected size 1 with 'keep' remaining. Got size {size}"
        )
    
    def test10_full_cache_with_ttl(self) -> None:
        """Test 10: Full cache with TTL"""
        cache = Cache(max_size=2, enable_persistence=False)
        cache.set('a', 1, ttl=0.1)  # Will expire
        cache.set('b', 2)
        
        time.sleep(0.15)
        
        # 'a' should be expired, so adding 'c' shouldn't require eviction
        cache.set('c', 3)
        
        self.assert_test(
            not cache.has('a') and cache.has('b') and cache.has('c') and cache.size() == 2,
            'Test 10: Full cache with TTL',
            f"Expected a=False, b=True, c=True, size=2. Got size={cache.size()}"
        )
    
    def test11_edge_cases(self) -> None:
        """Test 11: Edge cases"""
        cache = Cache(enable_persistence=False)
        
        # Get non-existent key
        non_existent = cache.get('does_not_exist')
        
        # Delete non-existent key
        deleted_non_existent = cache.delete('does_not_exist')
        
        # Empty cache operations
        cache.clear()
        size_empty = cache.size()
        keys_empty = cache.keys()
        
        self.assert_test(
            non_existent is None and 
            not deleted_non_existent and 
            size_empty == 0 and 
            len(keys_empty) == 0,
            'Test 11: Edge cases',
            'Edge case handling failed'
        )
    
    def test12_access_order_lru(self) -> None:
        """Test 12: Access order affects LRU"""
        cache = Cache(max_size=3, enable_persistence=False)
        
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        
        # Access a and b (making c the LRU)
        cache.get('a')
        cache.get('b')
        
        # Add d, should evict c
        cache.set('d', 4)
        
        self.assert_test(
            cache.has('a') and cache.has('b') and cache.has('d') and not cache.has('c'),
            'Test 12: Access order affects LRU',
            f"Expected c to be evicted. Has a:{cache.has('a')}, b:{cache.has('b')}, c:{cache.has('c')}, d:{cache.has('d')}"
        )
    
    def print_summary(self) -> None:
        """Print test summary"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print('\n' + '=' * 60)
        print('📊 TEST SUMMARY')
        print('=' * 60)
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print('=' * 60)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print('🚀 Cache System Example Usage\n')
    
    # Create cache with configuration
    my_cache = Cache(
        max_size=5,
        default_ttl=5.0,  # 5 seconds
        storage_file='my_app_cache.json',
        enable_persistence=True
    )
    
    # Set values with different TTLs
    my_cache.set('user:1', {'name': 'Alice', 'age': 30})
    my_cache.set('session:abc', 'active', ttl=3.0)  # 3 second TTL
    my_cache.set('config', {'theme': 'dark', 'lang': 'en'})
    
    # Get values
    print('user:1 =', my_cache.get('user:1'))
    print('session:abc =', my_cache.get('session:abc'))
    
    # Check cache stats
    print('\nCache Stats:', my_cache.get_stats())
    
    # Run test suite
    print('\n\n')
    test_suite = CacheTestSuite()
    test_suite.run_all_tests()
    
    # Cleanup example cache file
    if os.path.exists('my_app_cache.json'):
        os.remove('my_app_cache.json')