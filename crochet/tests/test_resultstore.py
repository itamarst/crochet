"""
Tests for _resultstore.
"""

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred

from .._resultstore import ResultStore
from .._eventloop import DeferredResult


class ResultStoreTests(TestCase):
    """
    Tests for ResultStore.
    """

    def test_store_and_retrieve(self):
        """
        DeferredResult instances be be stored in a ResultStore and then
        retrieved using the id returned from store().
        """
        store = ResultStore()
        dr = DeferredResult(Deferred())
        uid = store.store(dr)
        self.assertIdentical(store.retrieve(uid), dr)

    def test_retrieve_only_once(self):
        pass

    def test_synchronized(self):
        pass

    def test_uniqueness(self):
        pass

    def test_log_errors(self):
        pass
