"""
In-memory store for DeferredResults.
"""

import threading

from twisted.python import log

from ._util import synchronized


class ResultStore(object):
    """
    An in-memory store for DeferredResult instances.

    Each DeferredResult put in the store gets a unique identifier, which can
    be used to retrieve it later. This is useful for referring to results in
    e.g. web sessions.

    DeferredResults that are not retrieved by shutdown will be logged if they
    have an error result.
    """
    def __init__(self):
        self._counter = 0
        self._stored = {}
        self._lock = threading.Lock()

    @synchronized
    def store(self, deferred_result):
        """
        Store a DeferredResult.

        Return an integer, a unique identifier that can be used to retrieve
        the object.
        """
        self._counter += 1
        self._stored[self._counter] = deferred_result
        return self._counter

    @synchronized
    def retrieve(self, result_id):
        """
        Return the given DeferredResult, and remove it from the store.
        """
        return self._stored.pop(result_id)

    @synchronized
    def log_errors(self):
        """
        Log errors for all stored DeferredResults that have error results.
        """
        for result in self._stored.values():
            failure = result.original_failure()
            if failure is not None:
                log.err(failure, "Unhandled error in stashed DeferredResult:")

