"""
In-memory store for DeferredResults.
"""

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

    def store(self, deferred_result):
        """
        Store a DeferredResult.

        Return an integer, a unique identifier that can be used to retrieve
        the object.
        """
        self._stored[self._counter] = deferred_result
        return self._counter

    def retrieve(self, result_id):
        """
        Return the given DeferredResult, and remove it from the store.
        """
        return self._stored.pop(result_id)
