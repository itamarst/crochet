"""
Crochet!
"""

import threading
import atexit
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from twisted.internet import reactor
from twisted.python.failure import Failure


__all__ = ["setup"]


class DeferredResult(object):
    """
    A blocking interface to Deferred results.
    """

    def __init__(self, deferred):
        self._deferred = deferred
        self._queue = Queue()
        self._deferred.addBoth(self._queue.put)

    def cancel(self):
        """
        Try to cancel the operation by cancelling the underlying Defered.

        Cancellation of the operation may or may not happen depending on
        underlying cancellation support and whether the operation has already
        finished. In any case, however, the underlying Deferred will be fired.

        Multiple calls will have no additional effect.
        """

    def result(self, timeout=None):
        """
        Return the result, or throw an exception if result is a failure.

        It may take an unknown amount of time to return the result, so a
        timeout option is provided. If the given number of seconds pass with
        no result, a TimeoutError will be thrown.

        Additional calls to this function will have the same behavior as the
        first call.
        """
        result = self._queue.get()
        self._queue.put(result) # allow next result() call to get a value out
        if isinstance(result, Failure):
            raise result.value
        return result


class _Crochet(object):
    """
    Initialization infrastructure for running a reactor in a thread.
    """
    def __init__(self, reactor, atexit_register):
        self._reactor = reactor
        self._atexit_register = atexit_register
        self._started = False
        self._lock = threading.Lock()

    def setup(self):
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


_main = _Crochet(reactor, atexit.register)
setup = _main.setup
