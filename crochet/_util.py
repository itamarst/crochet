"""
Utility functions and classes.
"""

import wrapt


@wrapt.decorator
def _synced(method, self, args, kwargs):
    """Underlying synchronized wrapper."""
    with self._lock:
        return method(*args, **kwargs)


def synchronized(method):
    """
    Decorator that wraps a method with an acquire/release of self._lock.
    """
    result = _synced(method)
    result.synchronized = True
    return result
