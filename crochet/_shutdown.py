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
    Poll for a shutdown condition to be True, call a shutdown function
    when it becomes True.
    """

    def __init__(self, shutdown_condition, shutdown_function):
        threading.Thread.__init__(self, name="CrochetShutdownWatchdog")
        self._shutdown_condition = shutdown_condition
        self._shutdown_function = shutdown_function

    def run(self):
        while not self._shutdown_condition():
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


def default_shutdown_condition():
    main_thread = [t for t in threading.enumerate()
                   if t.name == "MainThread"][0]

    def shutdown_condition():
        return not main_thread.is_alive()

    return shutdown_condition


registry = FunctionRegistry()
register = registry.register
