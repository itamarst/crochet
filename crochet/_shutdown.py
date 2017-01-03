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
        self._signal_stop = False

    def run(self):
        while self._canary.is_alive():
            if self._signal_stop:
                return
            time.sleep(0.1)
        self._shutdown_function()

    def stop(self):
        """
        Stop the thread without running shutdown functions.
        """
        self._signal_stop = True


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


_registry = FunctionRegistry()
register = _registry.register


def get_watchdog_thread():
    """
    Returns a thread that runs registered callbacks when the main thread
    shuts down. Callbacks are registered in a global named `_registry`.
    """
    # This is... fragile. Not sure how else to do it though.
    watchdog = Watchdog(
        [
            t for t in threading.enumerate()
            if isinstance(t, threading._MainThread)
        ][0],
        _registry.run,
    )
    return watchdog
