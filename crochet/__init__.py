"""
Crochet!
"""

import threading
import atexit

from twisted.internet import reactor


class _Setup(object):
    """
    Initialization infrastructure for running a reactor in a thread.
    """
    def __init__(self, reactor, atexit_register):
        self._reactor = reactor
        self._atexit_register = atexit_register
        self._started = False
        self._lock = threading.Lock()

    def __call__(self):
        """
        Initialize the crochet library.

        This must be called at least once before the library can be used, and
        can be called multiple times.
        """
        with self._lock:
            if self._started:
                return
            self._started = True
            t = threading.Thread(
                target=lambda: self._reactor.run(installSignalHandlers=False))
            t.start()
            self._atexit_register(self._reactor.callFromThread,
                                  self._reactor.stop)

setup = _Setup(reactor, atexit.register)
