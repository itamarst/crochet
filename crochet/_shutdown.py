"""
Support for calling code when the main thread exits.

atexit cannot be used, since registered atexit functions only run after *all*
threads have exited.
"""

import threading
import time


class Watchdog(threading.Thread):
    """
    Watch a given thread, call a list of functions when that thread exits.
    """

    def __init__(self, canary):
        threading.Thread.__init__(self)
        self._canary = canary
        self._functions = []
        self.start()

    def register(self, function, *args, **kwargs):
        """
        Call the function when the watched thread exits.

        The function must be thread-safe.
        """
        self._functions.append(lambda: function(*args, **kwargs))

    def run(self):
        while True:
            if self._canary.is_alive():
                time.sleep(0.1)
                continue
            # Ideally this should catch errors and log them, but in practice
            # we only register one shutdown function for now:
            for f in self._functions:
                f()
            return


# This is... fragile. Not sure how else to do it though.
_watchdog = Watchdog([t for t in threading.enumerate()
                     if t.name == "MainThread"][0])
register = _watchdog.register
