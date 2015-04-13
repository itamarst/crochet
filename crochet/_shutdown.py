"""
Support for calling code when the main thread exits.

atexit cannot be used, since registered atexit functions only run after *all*
threads have exited.

The watchdog thread will be started by crochet.setup().
"""

import threading
import time

from twisted.python import log


class Watchdog(threading.Thread):
    """
    Watch a given thread, call a list of functions when that thread exits.
    """

    def __init__(self, canary, shutdown_function):
        threading.Thread.__init__(self, name="CrochetShutdownWatchdog")
        self._canary = canary
        self._shutdown_function = shutdown_function

    def run(self):
        while self._canary.is_alive():
            time.sleep(0.1)
        self._shutdown_function()


class FunctionRegistry(object):
    """
    A registry of functions that can be called all at once.
    """
    def __init__(self):
        self._functions = []

    def register(self, f, *args, **kwargs):
        """
        Register a function and arguments to be called later.
        """
        self._functions.append(lambda: f(*args, **kwargs))

    def run(self):
        """
        Run all registered functions in reverse order of registration.
        """
        for f in reversed(self._functions):
            try:
                f()
            except:
                log.err()


# This is... fragile. Not sure how else to do it though.
_registry = FunctionRegistry()
_watchdog = Watchdog(
    [
        t for t in threading.enumerate()
        if isinstance(t, threading._MainThread)
    ][0],
    _registry.run,
)
register = _registry.register
