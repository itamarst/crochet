"""
Tests for _resultstore.
"""

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred, fail, succeed

from .._resultstore import ResultStore
from .._eventloop import EventualResult


class ResultStoreTests(TestCase):
    """
    Tests for ResultStore.
    """

    def test_store_and_retrieve(self):
        """
        EventualResult instances be be stored in a ResultStore and then
        retrieved using the id returned from store().
        """
        store = ResultStore()
        dr = EventualResult(Deferred(), None)
        uid = store.store(dr)
        self.assertIdentical(store.retrieve(uid), dr)

    def test_retrieve_only_once(self):
        """
        Once a result is retrieved, it can no longer be retrieved again.
        """
        store = ResultStore()
        dr = EventualResult(Deferred(), None)
        uid = store.store(dr)
        store.retrieve(uid)
        self.assertRaises(KeyError, store.retrieve, uid)

    def test_synchronized(self):
        """
        store() and retrieve() are synchronized.
        """
        self.assertTrue(ResultStore.store.synchronized)
        self.assertTrue(ResultStore.retrieve.synchronized)
        self.assertTrue(ResultStore.log_errors.synchronized)

    def test_uniqueness(self):
        """
        Each store() operation returns a larger number, ensuring uniqueness.
        """
        store = ResultStore()
        dr = EventualResult(Deferred(), None)
        previous = store.store(dr)
        for i in range(100):
            store.retrieve(previous)
            dr = EventualResult(Deferred(), None)
            uid = store.store(dr)
            self.assertTrue(uid > previous)
            previous = uid

    def test_log_errors(self):
        """
        Unretrieved EventualResults have their errors, if any, logged on
        shutdown.
        """
        store = ResultStore()
        store.store(EventualResult(Deferred(), None))
        store.store(EventualResult(fail(ZeroDivisionError()), None))
        store.store(EventualResult(succeed(1), None))
        store.store(EventualResult(fail(RuntimeError()), None))
        store.log_errors()
        excs = self.flushLoggedErrors(ZeroDivisionError)
        self.assertEqual(len(excs), 1)
        excs = self.flushLoggedErrors(RuntimeError)
        self.assertEqual(len(excs), 1)
