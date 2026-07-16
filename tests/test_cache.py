"""Tests for murgtools.cache module."""

import json
import os
import pickle
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from murgtools import cache
from murgtools.cache import DataCache, CacheMetadata, get_cache, enable_cache, disable_cache, clear_cache


class TestCacheMetadata:
    """Tests for CacheMetadata class."""

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        meta = CacheMetadata(
            created_at=1000000.0,
            data_source='test_source',
            time_range=(100, 200),
            extra_info={'param': 'value'},
        )

        meta_dict = meta.to_dict()
        restored = CacheMetadata.from_dict(meta_dict)

        assert restored.created_at == meta.created_at
        assert restored.data_source == meta.data_source
        assert restored.time_range == meta.time_range
        assert restored.extra_info == meta.extra_info

    def test_is_expired_within_ttl(self):
        """Test that recent entries are not expired."""
        meta = CacheMetadata(created_at=time.time(), data_source='test')
        assert meta.is_expired(ttl_days=180) is False

    def test_is_expired_after_ttl(self):
        """Test that old entries are expired."""
        # Created 200 days ago
        created = time.time() - (200 * 24 * 60 * 60)
        meta = CacheMetadata(created_at=created, data_source='test')
        assert meta.is_expired(ttl_days=180) is True

    def test_is_expired_zero_ttl_never_expires(self):
        """Test that TTL of 0 means never expire."""
        # Created 1000 days ago
        created = time.time() - (1000 * 24 * 60 * 60)
        meta = CacheMetadata(created_at=created, data_source='test')
        assert meta.is_expired(ttl_days=0) is False

    def test_age_days(self):
        """Test age calculation."""
        # Created 10 days ago
        created = time.time() - (10 * 24 * 60 * 60)
        meta = CacheMetadata(created_at=created, data_source='test')
        assert 9.9 < meta.age_days() < 10.1


class TestDataCache:
    """Tests for DataCache class."""

    def setup_method(self):
        """Create a temporary cache directory for each test."""
        self.temp_dir = tempfile.mkdtemp()
        # Reset global cache
        cache._global_cache = None

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        # Reset global cache
        cache._global_cache = None

    def test_cache_disabled_by_default(self):
        """Verify caching is disabled by default."""
        c = DataCache(cache_dir=self.temp_dir)
        assert c.enabled is False

    def test_cache_can_be_enabled(self):
        """Verify caching can be enabled."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)
        assert c.enabled is True

    def test_cache_disabled_returns_fresh_data(self):
        """Verify disabled cache always calls fetch function."""
        c = DataCache(enabled=False, cache_dir=self.temp_dir)
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return {'data': call_count}

        result1 = c.get('source', fetch)
        result2 = c.get('source', fetch)

        assert call_count == 2
        assert result1['data'] == 1
        assert result2['data'] == 2

    def test_cache_enabled_returns_cached_data(self):
        """Verify enabled cache returns cached data."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return {'data': call_count}

        result1 = c.get('source', fetch)
        result2 = c.get('source', fetch)

        assert call_count == 1
        assert result1['data'] == 1
        assert result2['data'] == 1

    def test_force_refresh_bypasses_cache(self):
        """Verify force_refresh fetches fresh data."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return {'data': call_count}

        result1 = c.get('source', fetch)
        result2 = c.get('source', fetch, force_refresh=True)

        assert call_count == 2
        assert result1['data'] == 1
        assert result2['data'] == 2

    def test_different_sources_cached_separately(self):
        """Verify different data sources have separate cache entries."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        result1 = c.get('source1', lambda: 'data1')
        result2 = c.get('source2', lambda: 'data2')

        assert result1 == 'data1'
        assert result2 == 'data2'

    def test_different_time_ranges_cached_separately(self):
        """Verify different time ranges have separate cache entries."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        result1 = c.get('source', lambda: 'data1', time_range=(100, 200))
        result2 = c.get('source', lambda: 'data2', time_range=(200, 300))

        assert result1 == 'data1'
        assert result2 == 'data2'

    def test_expired_cache_returns_fresh_data(self):
        """Verify expired cache entries are refreshed."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir, ttl_days=1)

        # First fetch
        result1 = c.get('source', lambda: 'old_data')

        # Manually make the cache old by modifying metadata
        cache_key = c._generate_cache_key('source')
        _, meta_path = c._get_cache_paths(cache_key)
        with open(meta_path, 'r') as f:
            meta_dict = json.load(f)
        # Set created_at to 10 days ago
        meta_dict['created_at'] = time.time() - (10 * 24 * 60 * 60)
        with open(meta_path, 'w') as f:
            json.dump(meta_dict, f)

        # Second fetch should get fresh data
        result2 = c.get('source', lambda: 'new_data')

        assert result1 == 'old_data'
        assert result2 == 'new_data'

    def test_is_cached(self):
        """Test is_cached method."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        assert c.is_cached('source') is False

        c.get('source', lambda: 'data')

        assert c.is_cached('source') is True

    def test_invalidate(self):
        """Test cache invalidation."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        c.get('source', lambda: 'data1')
        assert c.is_cached('source') is True

        c.invalidate('source')
        assert c.is_cached('source') is False

        result = c.get('source', lambda: 'data2')
        assert result == 'data2'

    def test_clear_all(self):
        """Test clearing all cache entries."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        c.get('source1', lambda: 'data1')
        c.get('source2', lambda: 'data2')

        assert c.is_cached('source1') is True
        assert c.is_cached('source2') is True

        c.clear()

        assert c.is_cached('source1') is False
        assert c.is_cached('source2') is False

    def test_clear_older_than(self):
        """Test clearing entries older than a threshold."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        # Create two entries
        c.get('source1', lambda: 'data1')
        c.get('source2', lambda: 'data2')

        # Make source1 old
        cache_key = c._generate_cache_key('source1')
        _, meta_path = c._get_cache_paths(cache_key)
        with open(meta_path, 'r') as f:
            meta_dict = json.load(f)
        meta_dict['created_at'] = time.time() - (100 * 24 * 60 * 60)  # 100 days ago
        with open(meta_path, 'w') as f:
            json.dump(meta_dict, f)

        # Clear entries older than 50 days
        c.clear(older_than_days=50)

        assert c.is_cached('source1') is False  # Old, should be cleared
        assert c.is_cached('source2') is True   # New, should remain

    def test_get_stats(self):
        """Test cache statistics."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        stats = c.get_stats()
        assert stats['enabled'] is True
        assert stats['entry_count'] == 0

        c.get('source1', lambda: 'data1')
        c.get('source2', lambda: 'data2')

        stats = c.get_stats()
        assert stats['entry_count'] == 2
        assert stats['total_size_mb'] >= 0  # Small files may round to 0

    def test_ttl_setting(self):
        """Test TTL getter and setter."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir, ttl_days=90)
        assert c.ttl_days == 90

        c.ttl_days = 30
        assert c.ttl_days == 30

    def test_ttl_negative_raises_error(self):
        """Test that negative TTL raises ValueError."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)
        with pytest.raises(ValueError):
            c.ttl_days = -1

    def test_cache_dir_setting(self):
        """Test cache_dir getter and setter."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)
        assert c.cache_dir == Path(self.temp_dir)

        new_dir = tempfile.mkdtemp()
        try:
            c.cache_dir = new_dir
            assert c.cache_dir == Path(new_dir)
        finally:
            import shutil
            shutil.rmtree(new_dir, ignore_errors=True)

    def test_thread_safety(self):
        """Test thread-safe concurrent access."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)
        results = []
        errors = []
        fetch_count = 0
        fetch_lock = threading.Lock()

        def fetch():
            nonlocal fetch_count
            with fetch_lock:
                fetch_count += 1
            time.sleep(0.01)  # Simulate network delay
            return 'data'

        def worker(source):
            try:
                for _ in range(5):
                    result = c.get(source, fetch)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f'source{i % 3}',)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread errors: {errors}"
        assert all(r == 'data' for r in results)
        # With 3 unique sources and proper caching, should have at most 3 fetches
        # (may have more due to race conditions before cache is populated)
        assert fetch_count <= 10


class TestEnvironmentVariables:
    """Tests for environment variable configuration."""

    def setup_method(self):
        """Save original environment."""
        self.orig_env = {
            k: os.environ.get(k) for k in [
                'MURGTOOLS_CACHE_ENABLED',
                'MURGTOOLS_CACHE_DIR',
                'MURGTOOLS_CACHE_TTL_DAYS',
            ]
        }
        # Clear environment
        for k in self.orig_env:
            if k in os.environ:
                del os.environ[k]
        # Reset global cache
        cache._global_cache = None
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Restore original environment."""
        for k, v in self.orig_env.items():
            if v is None:
                if k in os.environ:
                    del os.environ[k]
            else:
                os.environ[k] = v
        # Reset global cache
        cache._global_cache = None
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_env_cache_enabled(self):
        """Test MURGTOOLS_CACHE_ENABLED environment variable."""
        os.environ['MURGTOOLS_CACHE_ENABLED'] = '1'
        os.environ['MURGTOOLS_CACHE_DIR'] = self.temp_dir

        c = DataCache()
        assert c.enabled is True

    def test_env_cache_enabled_true_string(self):
        """Test MURGTOOLS_CACHE_ENABLED with 'true' string."""
        os.environ['MURGTOOLS_CACHE_ENABLED'] = 'true'
        os.environ['MURGTOOLS_CACHE_DIR'] = self.temp_dir

        c = DataCache()
        assert c.enabled is True

    def test_env_cache_dir(self):
        """Test MURGTOOLS_CACHE_DIR environment variable."""
        custom_dir = tempfile.mkdtemp()
        try:
            os.environ['MURGTOOLS_CACHE_DIR'] = custom_dir
            c = DataCache()
            assert c.cache_dir == Path(custom_dir)
        finally:
            import shutil
            shutil.rmtree(custom_dir, ignore_errors=True)

    def test_env_cache_ttl(self):
        """Test MURGTOOLS_CACHE_TTL_DAYS environment variable."""
        os.environ['MURGTOOLS_CACHE_TTL_DAYS'] = '90'
        os.environ['MURGTOOLS_CACHE_DIR'] = self.temp_dir

        c = DataCache()
        assert c.ttl_days == 90

    def test_env_cache_ttl_invalid(self):
        """Test invalid TTL value falls back to default."""
        os.environ['MURGTOOLS_CACHE_TTL_DAYS'] = 'invalid'
        os.environ['MURGTOOLS_CACHE_DIR'] = self.temp_dir

        c = DataCache()
        assert c.ttl_days == 180  # default


class TestGlobalCacheFunctions:
    """Tests for global cache functions."""

    def setup_method(self):
        """Reset global cache."""
        cache._global_cache = None
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Reset global cache and clean up."""
        cache._global_cache = None
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_cache_returns_same_instance(self):
        """Test get_cache returns singleton."""
        c1 = get_cache(cache_dir=self.temp_dir)
        c2 = get_cache()
        assert c1 is c2

    def test_enable_cache(self):
        """Test enable_cache convenience function."""
        c = enable_cache(cache_dir=self.temp_dir)
        assert c.enabled is True

    def test_disable_cache(self):
        """Test disable_cache convenience function."""
        enable_cache(cache_dir=self.temp_dir)
        disable_cache()
        c = get_cache()
        assert c.enabled is False

    def test_clear_cache(self):
        """Test clear_cache convenience function."""
        c = enable_cache(cache_dir=self.temp_dir)
        c.get('source', lambda: 'data')
        assert c.is_cached('source') is True

        clear_cache()
        assert c.is_cached('source') is False


class TestCacheWithComplexData:
    """Tests for caching complex data types."""

    def setup_method(self):
        """Create temporary cache directory."""
        self.temp_dir = tempfile.mkdtemp()
        cache._global_cache = None

    def teardown_method(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        cache._global_cache = None

    def test_cache_numpy_arrays(self):
        """Test caching numpy arrays."""
        import numpy as np

        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        data = {'array': np.array([1.0, 2.0, 3.0]), 'value': 42}
        c.get('source', lambda: data)

        # Clear memory and reload from cache
        result = c.get('source', lambda: None)

        assert np.array_equal(result['array'], data['array'])
        assert result['value'] == 42

    def test_cache_nested_dict(self):
        """Test caching nested dictionaries."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        data = {
            'level1': {
                'level2': {
                    'values': [1, 2, 3],
                    'name': 'test',
                }
            }
        }
        c.get('source', lambda: data)
        result = c.get('source', lambda: None)

        assert result == data

    def test_cache_with_extra_params(self):
        """Test caching with extra parameters."""
        c = DataCache(enabled=True, cache_dir=self.temp_dir)

        # Different extra_params should create different cache entries
        result1 = c.get('source', lambda: 'data1', extra_params={'gaugenumber': 'gauge1'})
        result2 = c.get('source', lambda: 'data2', extra_params={'gaugenumber': 'gauge2'})

        assert result1 == 'data1'
        assert result2 == 'data2'
