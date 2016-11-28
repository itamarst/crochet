"""
Utility functions and classes.
"""
import sys
from functools import wraps

from twisted.python.runtime import platform

reapAllProcesses = lambda: None
if platform.type == "posix":
    try:
        from twisted.internet.process import reapAllProcesses
    except (SyntaxError, ImportError):
        if sys.version_info < (3, 3, 0):
            raise


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


def get_twisted_reactor(use_global):
    """
    If `use_global=False`, this recreates logic in `twisted.internet.default`
    to choose between reactors, but bypasses "installing" the reactor as a
    global singleton.

    If `use_global=True`, this returns the globally installed twisted reactor.
    """
    if use_global:
        from twisted.internet import reactor
        return reactor

    try:
        if platform.isLinux():
            try:
                from twisted.internet.epollreactor import EPollReactor as _r
            except ImportError:
                from twisted.internet.pollreactor import PollReactor as _r
        elif platform.getType() == 'posix' and not platform.isMacOSX():
            from twisted.internet.pollreactor import PollReactor as _r
        else:
            from twisted.internet.selectreactor import SelectReactor as _r
    except ImportError:
        from twisted.internet.selectreactor import SelectReactor as _r

    return _r()
