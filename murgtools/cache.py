"""Data caching module for murgtools.

This module provides disk-based caching for retrieved data to avoid repeated
network requests. Caching is OFF by default and must be explicitly enabled.

Features:
    - Disk-based persistence at configurable location (default: /data/getdata)
    - Configurable TTL (default: 6 months / 180 days)
    - Thread-safe operations
    - Force refresh capability
    - Automatic cache invalidation for stale data

Usage:
    from murgtools.cache import DataCache

    # Create cache instance (caching disabled by default)
    cache = DataCache()

    # Enable caching
    cache = DataCache(enabled=True)

    # Custom configuration
    cache = DataCache(
        enabled=True,
        cache_dir='/custom/path',
        ttl_days=90,  # 3 months
    )

    # Force refresh even if cache is valid
    data = cache.get(key, fetch_func, force_refresh=True)

Environment Variables:
    MURGTOOLS_CACHE_ENABLED: Set to '1' or 'true' to enable caching
    MURGTOOLS_CACHE_DIR: Override default cache directory
    MURGTOOLS_CACHE_TTL_DAYS: Override default TTL in days
"""

import hashlib
import json
import logging
import os
import pickle
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union

import numpy as np

from . import config


class NumpyJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy types."""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass


class CacheMetadata:
    """Metadata for a cached entry."""

    def __init__(self, created_at: float, data_source: str, time_range: Optional[Tuple] = None,
                 extra_info: Optional[Dict] = None):
        """Initialize cache metadata.

        Args:
            created_at: Unix timestamp when cache was created.
            data_source: Identifier for the data source (e.g., URL, gauge name).
            time_range: Optional tuple of (start_epoch, end_epoch) for time-series data.
            extra_info: Optional dictionary with additional metadata.
        """
        self.created_at = created_at
        self.data_source = data_source
        self.time_range = time_range
        self.extra_info = extra_info or {}

    def to_dict(self) -> Dict:
        """Convert metadata to dictionary for serialization."""
        return {
            'created_at': self.created_at,
            'data_source': self.data_source,
            'time_range': self.time_range,
            'extra_info': self.extra_info,
            'version': '1.0',
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CacheMetadata':
        """Create metadata from dictionary."""
        return cls(
            created_at=data['created_at'],
            data_source=data['data_source'],
            time_range=data.get('time_range'),
            extra_info=data.get('extra_info', {}),
        )

    def is_expired(self, ttl_days: int) -> bool:
        """Check if the cache entry has expired.

        Args:
            ttl_days: Time-to-live in days.

        Returns:
            True if expired, False otherwise.
        """
        if ttl_days <= 0:
            return False  # TTL of 0 means never expire

        expiry_time = self.created_at + (ttl_days * 24 * 60 * 60)
        return time.time() > expiry_time

    def age_days(self) -> float:
        """Get the age of this cache entry in days."""
        return (time.time() - self.created_at) / (24 * 60 * 60)


class DataCache:
    """Thread-safe disk-based data cache.

    Caching is OFF by default. Enable it explicitly via the `enabled` parameter
    or by setting the MURGTOOLS_CACHE_ENABLED environment variable.
    """

    def __init__(self, enabled: Optional[bool] = None, cache_dir: Optional[str] = None,
                 ttl_days: Optional[int] = None):
        """Initialize the data cache.

        Args:
            enabled: Whether caching is enabled. If None, checks environment
                variable MURGTOOLS_CACHE_ENABLED, otherwise defaults to False.
            cache_dir: Directory to store cache files. If None, checks environment
                variable MURGTOOLS_CACHE_DIR, otherwise uses config.DEFAULT_CACHE_DIR.
            ttl_days: Time-to-live in days. If None, checks environment variable
                MURGTOOLS_CACHE_TTL_DAYS, otherwise uses config.DEFAULT_CACHE_TTL_DAYS.
                Set to 0 for no expiration.
        """
        self._lock = threading.RLock()

        # Determine if caching is enabled
        if enabled is not None:
            self._enabled = enabled
        else:
            env_enabled = os.environ.get(config.ENV_CACHE_ENABLED, '').lower()
            self._enabled = env_enabled in ('1', 'true', 'yes', 'on')

        # Determine cache directory
        if cache_dir is not None:
            self._cache_dir = Path(cache_dir)
        else:
            env_dir = os.environ.get(config.ENV_CACHE_DIR)
            self._cache_dir = Path(env_dir) if env_dir else Path(config.DEFAULT_CACHE_DIR)

        # Determine TTL
        if ttl_days is not None:
            self._ttl_days = ttl_days
        else:
            env_ttl = os.environ.get(config.ENV_CACHE_TTL_DAYS)
            if env_ttl:
                try:
                    self._ttl_days = int(env_ttl)
                except ValueError:
                    logger.warning(f"Invalid TTL value '{env_ttl}', using default")
                    self._ttl_days = config.DEFAULT_CACHE_TTL_DAYS
            else:
                self._ttl_days = config.DEFAULT_CACHE_TTL_DAYS

        # Create cache directory if enabled and directory doesn't exist
        if self._enabled:
            self._ensure_cache_dir()

    @property
    def enabled(self) -> bool:
        """Whether caching is enabled."""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable caching."""
        with self._lock:
            self._enabled = value
            if value:
                self._ensure_cache_dir()

    @property
    def cache_dir(self) -> Path:
        """The cache directory path."""
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, value: Union[str, Path]):
        """Set the cache directory."""
        with self._lock:
            self._cache_dir = Path(value)
            if self._enabled:
                self._ensure_cache_dir()

    @property
    def ttl_days(self) -> int:
        """Time-to-live in days."""
        return self._ttl_days

    @ttl_days.setter
    def ttl_days(self, value: int):
        """Set the TTL in days."""
        if value < 0:
            raise ValueError("TTL must be non-negative")
        self._ttl_days = value

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.warning(f"Cannot create cache directory {self._cache_dir}: {e}")
            logger.warning("Caching will be disabled")
            self._enabled = False
        except OSError as e:
            logger.warning(f"Error creating cache directory {self._cache_dir}: {e}")
            self._enabled = False

    def _generate_cache_key(self, data_source: str, time_range: Optional[Tuple] = None,
                            extra_params: Optional[Dict] = None) -> str:
        """Generate a unique cache key based on request parameters.

        Args:
            data_source: Identifier for the data source.
            time_range: Optional tuple of (start_epoch, end_epoch).
            extra_params: Optional additional parameters that affect the data.

        Returns:
            A hex string suitable for use as a filename.
        """
        key_parts = [data_source]

        if time_range:
            key_parts.append(f"t{time_range[0]}-{time_range[1]}")

        if extra_params:
            # Sort keys for deterministic ordering
            sorted_params = sorted(extra_params.items())
            key_parts.append(json.dumps(sorted_params, sort_keys=True))

        key_string = '|'.join(str(p) for p in key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def _get_cache_paths(self, cache_key: str) -> Tuple[Path, Path]:
        """Get paths for data and metadata files.

        Args:
            cache_key: The cache key.

        Returns:
            Tuple of (data_path, metadata_path).
        """
        data_path = self._cache_dir / f"{cache_key}.pkl"
        meta_path = self._cache_dir / f"{cache_key}.meta.json"
        return data_path, meta_path

    def get(self, data_source: str, fetch_func: Callable[[], Any],
            time_range: Optional[Tuple] = None, extra_params: Optional[Dict] = None,
            force_refresh: bool = False) -> Any:
        """Get data from cache or fetch it.

        Args:
            data_source: Identifier for the data source (e.g., URL, gauge name).
            fetch_func: Callable that fetches the data if not cached.
            time_range: Optional tuple of (start_epoch, end_epoch) for time-series data.
            extra_params: Optional additional parameters that affect the data.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            The requested data (from cache or freshly fetched).
        """
        # If caching is disabled, just fetch
        if not self._enabled:
            return fetch_func()

        cache_key = self._generate_cache_key(data_source, time_range, extra_params)

        with self._lock:
            # Check cache unless force_refresh is requested
            if not force_refresh:
                cached_data = self._read_cache(cache_key)
                if cached_data is not None:
                    return cached_data

            # Fetch fresh data
            data = fetch_func()

            # Store in cache
            if data is not None:
                self._write_cache(cache_key, data, data_source, time_range, extra_params)

            return data

    def _read_cache(self, cache_key: str) -> Optional[Any]:
        """Read data from cache if valid.

        Args:
            cache_key: The cache key.

        Returns:
            Cached data if valid, None otherwise.
        """
        data_path, meta_path = self._get_cache_paths(cache_key)

        # Check if cache files exist
        if not data_path.exists() or not meta_path.exists():
            return None

        try:
            # Read and validate metadata
            with open(meta_path, 'r') as f:
                meta_dict = json.load(f)
            metadata = CacheMetadata.from_dict(meta_dict)

            # Check if expired
            if metadata.is_expired(self._ttl_days):
                logger.debug(f"Cache expired for {cache_key} (age: {metadata.age_days():.1f} days)")
                self._remove_cache(cache_key)
                return None

            # Read data
            with open(data_path, 'rb') as f:
                data = pickle.load(f)

            logger.debug(f"Cache hit for {cache_key} (age: {metadata.age_days():.1f} days)")
            return data

        except (json.JSONDecodeError, pickle.UnpicklingError, KeyError, OSError) as e:
            logger.warning(f"Error reading cache {cache_key}: {e}")
            self._remove_cache(cache_key)
            return None

    def _write_cache(self, cache_key: str, data: Any, data_source: str,
                     time_range: Optional[Tuple], extra_params: Optional[Dict]):
        """Write data to cache.

        Args:
            cache_key: The cache key.
            data: The data to cache.
            data_source: Identifier for the data source.
            time_range: Optional time range tuple.
            extra_params: Optional extra parameters.
        """
        data_path, meta_path = self._get_cache_paths(cache_key)

        try:
            # Create metadata
            metadata = CacheMetadata(
                created_at=time.time(),
                data_source=data_source,
                time_range=time_range,
                extra_info=extra_params,
            )

            # Write metadata first (smaller, validates we can write)
            with open(meta_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2, cls=NumpyJSONEncoder)

            # Write data
            with open(data_path, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

            logger.debug(f"Cached data for {cache_key}")

        except (OSError, pickle.PicklingError) as e:
            logger.warning(f"Error writing cache {cache_key}: {e}")
            # Clean up partial writes
            self._remove_cache(cache_key)

    def _remove_cache(self, cache_key: str):
        """Remove cache files for a key.

        Args:
            cache_key: The cache key.
        """
        data_path, meta_path = self._get_cache_paths(cache_key)

        for path in (data_path, meta_path):
            try:
                if path.exists():
                    path.unlink()
            except OSError as e:
                logger.warning(f"Error removing cache file {path}: {e}")

    def clear(self, older_than_days: Optional[int] = None):
        """Clear cache entries.

        Args:
            older_than_days: If specified, only clear entries older than this.
                If None, clear all entries.
        """
        if not self._cache_dir.exists():
            return

        with self._lock:
            cleared = 0
            for meta_path in self._cache_dir.glob("*.meta.json"):
                try:
                    with open(meta_path, 'r') as f:
                        meta_dict = json.load(f)
                    metadata = CacheMetadata.from_dict(meta_dict)

                    if older_than_days is None or metadata.age_days() > older_than_days:
                        cache_key = meta_path.stem.replace('.meta', '')
                        self._remove_cache(cache_key)
                        cleared += 1

                except (json.JSONDecodeError, KeyError, OSError) as e:
                    logger.warning(f"Error reading metadata {meta_path}: {e}")
                    # Remove corrupted entry
                    cache_key = meta_path.stem.replace('.meta', '')
                    self._remove_cache(cache_key)
                    cleared += 1

            logger.info(f"Cleared {cleared} cache entries")

    def get_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        if not self._cache_dir.exists():
            return {
                'enabled': self._enabled,
                'cache_dir': str(self._cache_dir),
                'ttl_days': self._ttl_days,
                'entry_count': 0,
                'total_size_mb': 0,
            }

        entry_count = 0
        total_size = 0
        oldest_entry = None
        newest_entry = None

        for data_path in self._cache_dir.glob("*.pkl"):
            entry_count += 1
            total_size += data_path.stat().st_size

            meta_path = data_path.with_suffix('.meta.json')
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        meta_dict = json.load(f)
                    created = meta_dict.get('created_at', 0)
                    if oldest_entry is None or created < oldest_entry:
                        oldest_entry = created
                    if newest_entry is None or created > newest_entry:
                        newest_entry = created
                except (json.JSONDecodeError, OSError):
                    pass

        return {
            'enabled': self._enabled,
            'cache_dir': str(self._cache_dir),
            'ttl_days': self._ttl_days,
            'entry_count': entry_count,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'oldest_entry': datetime.fromtimestamp(oldest_entry).isoformat() if oldest_entry else None,
            'newest_entry': datetime.fromtimestamp(newest_entry).isoformat() if newest_entry else None,
        }

    def is_cached(self, data_source: str, time_range: Optional[Tuple] = None,
                  extra_params: Optional[Dict] = None) -> bool:
        """Check if data is cached and valid.

        Args:
            data_source: Identifier for the data source.
            time_range: Optional time range tuple.
            extra_params: Optional extra parameters.

        Returns:
            True if valid cache exists, False otherwise.
        """
        if not self._enabled:
            return False

        cache_key = self._generate_cache_key(data_source, time_range, extra_params)
        data_path, meta_path = self._get_cache_paths(cache_key)

        if not data_path.exists() or not meta_path.exists():
            return False

        try:
            with open(meta_path, 'r') as f:
                meta_dict = json.load(f)
            metadata = CacheMetadata.from_dict(meta_dict)
            return not metadata.is_expired(self._ttl_days)
        except (json.JSONDecodeError, KeyError, OSError):
            return False

    def invalidate(self, data_source: str, time_range: Optional[Tuple] = None,
                   extra_params: Optional[Dict] = None):
        """Invalidate (remove) a specific cache entry.

        Args:
            data_source: Identifier for the data source.
            time_range: Optional time range tuple.
            extra_params: Optional extra parameters.
        """
        cache_key = self._generate_cache_key(data_source, time_range, extra_params)
        with self._lock:
            self._remove_cache(cache_key)


# Global cache instance (disabled by default)
_global_cache: Optional[DataCache] = None
_global_cache_lock = threading.Lock()


def get_cache(enabled: Optional[bool] = None, cache_dir: Optional[str] = None,
              ttl_days: Optional[int] = None) -> DataCache:
    """Get or create the global cache instance.

    Args:
        enabled: Whether to enable caching. If None on first call, defaults to False.
        cache_dir: Cache directory. If None, uses default or environment variable.
        ttl_days: TTL in days. If None, uses default or environment variable.

    Returns:
        The global DataCache instance.
    """
    global _global_cache

    with _global_cache_lock:
        if _global_cache is None:
            _global_cache = DataCache(enabled=enabled, cache_dir=cache_dir, ttl_days=ttl_days)
        else:
            # Update settings if provided
            if enabled is not None:
                _global_cache.enabled = enabled
            if cache_dir is not None:
                _global_cache.cache_dir = cache_dir
            if ttl_days is not None:
                _global_cache.ttl_days = ttl_days

        return _global_cache


def enable_cache(cache_dir: Optional[str] = None, ttl_days: Optional[int] = None) -> DataCache:
    """Enable the global cache with optional configuration.

    Convenience function to enable caching with one call.

    Args:
        cache_dir: Cache directory. If None, uses default.
        ttl_days: TTL in days. If None, uses default (180 days).

    Returns:
        The enabled DataCache instance.
    """
    return get_cache(enabled=True, cache_dir=cache_dir, ttl_days=ttl_days)


def disable_cache():
    """Disable the global cache."""
    cache = get_cache()
    cache.enabled = False


def clear_cache(older_than_days: Optional[int] = None):
    """Clear the global cache.

    Args:
        older_than_days: If specified, only clear entries older than this.
    """
    cache = get_cache()
    cache.clear(older_than_days=older_than_days)
