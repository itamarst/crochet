"""
Utility functions and classes.
"""

from functools import wraps


def synchronized(method):
    """
    Decorator that wraps a method with an acquire/release of self._lock.
    """
    @wraps(method)
    def synced(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    synced.synchronized = True
    return synced
