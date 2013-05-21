"""
Tests for the crochet APIs.
"""

from __future__ import absolute_import

import threading
import time
import gc
import sys

from twisted.trial.unittest import TestCase
from twisted.internet.defer import succeed, Deferred, fail, CancelledError
from twisted.python.failure import Failure

from .._eventloop import EventLoop, EventualResult, TimeoutError
from .test_setup import FakeReactor
from .. import (_main, setup, in_reactor, retrieve_result, _store, no_setup,
                run_in_reactor)


class EventualResultTests(TestCase):
    """
    Tests for EventualResult.
    """

    def test_success_result(self):
        """
        wait() returns the value the Deferred fired with.
        """
        dr = EventualResult(succeed(123))
        self.assertEqual(dr.wait(), 123)

    def test_later_success_result(self):
        """
        wait() returns the value the Deferred fired with, in the case where
        the Deferred is fired after wait() is called.
        """
        d = Deferred()
        def fireSoon():
            import time; time.sleep(0.01)
            d.callback(345)
        threading.Thread(target=fireSoon).start()
        dr = EventualResult(d)
        self.assertEqual(dr.wait(), 345)

    def test_success_result_twice(self):
        """
        A second call to wait() returns same value as the first call.
        """
        dr = EventualResult(succeed(123))
        self.assertEqual(dr.wait(), 123)
        self.assertEqual(dr.wait(), 123)

    def test_failure_result(self):
        """
        wait() raises the exception the Deferred fired with.
        """
        dr = EventualResult(fail(RuntimeError()))
        self.assertRaises(RuntimeError, dr.wait)

    def test_later_failure_result(self):
        """
        wait() raises the exception the Deferred fired with, in the case
        where the Deferred is fired after wait() is called.
        """
        d = Deferred()
        def fireSoon():
            time.sleep(0.01)
            d.errback(RuntimeError())
        threading.Thread(target=fireSoon).start()
        dr = EventualResult(d)
        self.assertRaises(RuntimeError, dr.wait)

    def test_failure_result_twice(self):
        """
        A second call to wait() raises same value as the first call.
        """
        dr = EventualResult(fail(ZeroDivisionError()))
        self.assertRaises(ZeroDivisionError, dr.wait)
        self.assertRaises(ZeroDivisionError, dr.wait)

    def test_timeout(self):
        """
        If no result is available, wait(timeout) will throw a TimeoutError.
        """
        start = time.time()
        dr = EventualResult(Deferred())
        self.assertRaises(TimeoutError, dr.wait, timeout=0.03)
        self.assertTrue(abs(time.time() - start - 0.03) < 0.005)

    def test_timeout_twice(self):
        """
        If no result is available, a second call to wait(timeout) will also
        result in a TimeoutError exception.
        """
        dr = EventualResult(Deferred())
        self.assertRaises(TimeoutError, dr.wait, timeout=0.01)
        self.assertRaises(TimeoutError, dr.wait, timeout=0.01)

    def test_timeout_then_result(self):
        """
        If a result becomes available after a timeout, a second call to
        wait() will return it.
        """
        d = Deferred()
        dr = EventualResult(d)
        self.assertRaises(TimeoutError, dr.wait, timeout=0.01)
        d.callback(u"value")
        self.assertEqual(dr.wait(), u"value")
        self.assertEqual(dr.wait(), u"value")

    def test_cancel(self):
        """
        cancel() cancels the wrapped Deferred, running cancellation in the
        event loop thread.
        """
        reactor = FakeReactor()
        cancelled = []
        def error(f):
            cancelled.append(reactor.in_call_from_thread)
            cancelled.append(f)

        d = Deferred().addErrback(error)
        dr = EventualResult(d, _reactor=reactor)
        dr.cancel()
        self.assertTrue(cancelled[0])
        self.assertIsInstance(cancelled[1].value, CancelledError)

    def test_stash(self):
        """
        EventualResult.stash() stores the object in the global ResultStore.
        """
        dr = EventualResult(Deferred())
        uid = dr.stash()
        self.assertIdentical(dr, _store.retrieve(uid))

    def test_original_failure(self):
        """
        original_failure() returns the underlying Failure of the Deferred
        wrapped by the EventualResult.
        """
        try:
            1/0
        except:
            f = Failure()
        dr = EventualResult(fail(f))
        self.assertIdentical(dr.original_failure(), f)

    def test_original_failure_no_result(self):
        """
        If there is no result yet, original_failure() returns None.
        """
        dr = EventualResult(Deferred())
        self.assertIdentical(dr.original_failure(), None)

    def test_original_failure_not_error(self):
        """
        If the result is not an error, original_failure() returns None.
        """
        dr = EventualResult(succeed(3))
        self.assertIdentical(dr.original_failure(), None)

    def test_error_logged_no_wait(self):
        """
        If the result is an error and wait() was never called, the error will
        be logged once the EventualResult is garbage-collected.
        """
        dr = EventualResult(fail(ZeroDivisionError()))
        del dr
        gc.collect()
        excs = self.flushLoggedErrors(ZeroDivisionError)
        self.assertEqual(len(excs), 1)

    def test_error_logged_wait_timeout(self):
        """
        If the result is an error and wait() was called but timed out, the
        error will be logged once the EventualResult is garbage-collected.
        """
        d = Deferred()
        dr = EventualResult(d)
        try:
            dr.wait(0)
        except TimeoutError:
            pass
        d.errback(ZeroDivisionError())
        del dr
        sys.exc_clear()
        gc.collect()
        excs = self.flushLoggedErrors(ZeroDivisionError)
        self.assertEqual(len(excs), 1)

    def test_error_after_gc_logged(self):
        """
        If the result is an error that occurs after all user references to the
        EventualResult are lost, the error is still logged.
        """
        d = Deferred()
        dr = EventualResult(d)
        del dr
        d.errback(ZeroDivisionError())
        gc.collect()
        excs = self.flushLoggedErrors(ZeroDivisionError)
        self.assertEqual(len(excs), 1)


class InReactorTests(TestCase):
    """
    Tests for the run_in_reactor decorator (and the deprecated in_reactor).
    """

    def test_name(self):
        """
        The function decorated with in_reactor has the same name as the
        original function.
        """
        c = EventLoop(None, lambda f, g: None)

        @c.in_reactor
        def some_name(reactor):
            pass
        self.assertEqual(some_name.__name__, "some_name")

    def test_in_reactor_thread(self):
        """
        The function decorated with in_reactor is run in the reactor
        thread, and takes the reactor as its first argument.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)
        calls = []

        @c.in_reactor
        def func(reactor, a, b, c):
            self.assertIdentical(reactor, myreactor)
            self.assertTrue(reactor.in_call_from_thread)
            calls.append((a, b, c))

        func(1, 2, c=3)
        self.assertEqual(calls, [(1, 2, 3)])

    def test_run_in_reactor_thread(self):
        """
        The function decorated with run_in_reactor is run in the reactor
        thread, and takes the reactor as its first argument.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)
        calls = []

        @c.run_in_reactor
        def func(a, b, c):
            self.assertTrue(myreactor.in_call_from_thread)
            calls.append((a, b, c))

        func(1, 2, c=3)
        self.assertEqual(calls, [(1, 2, 3)])

    def make_wrapped_function(self):
        """
        Return a function wrapped with in_reactor that returns its first argument.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)

        @c.run_in_reactor
        def passthrough(argument):
            return argument
        return passthrough

    def test_deferred_success_result(self):
        """
        If the underlying function returns a Deferred, the wrapper returns a
        EventualResult hooked up to the Deferred.
        """
        passthrough = self.make_wrapped_function()
        result = passthrough(succeed(123))
        self.assertIsInstance(result, EventualResult)
        self.assertEqual(result.wait(), 123)

    def test_deferred_failure_result(self):
        """
        If the underlying function returns a Deferred, the wrapper returns a
        EventualResult hooked up to the Deferred that can deal with failures
        as well.
        """
        passthrough = self.make_wrapped_function()
        result = passthrough(fail(ZeroDivisionError()))
        self.assertIsInstance(result, EventualResult)
        self.assertRaises(ZeroDivisionError, result.wait)

    def test_regular_result(self):
        """
        If the underlying function returns a non-Deferred, the wrapper returns
        a EventualResult hooked up to a Deferred wrapping the result.
        """
        passthrough = self.make_wrapped_function()
        result = passthrough(123)
        self.assertIsInstance(result, EventualResult)
        self.assertEqual(result.wait(), 123)

    def test_exception_result(self):
        """
        If the underlying function throws an exception, the wrapper returns a
        EventualResult hooked up to a Deferred wrapping the exception.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)

        @c.run_in_reactor
        def raiser():
            1/0

        result = raiser()
        self.assertIsInstance(result, EventualResult)
        self.assertRaises(ZeroDivisionError, result.wait)


class PublicAPITests(TestCase):
    """
    Tests for the public API.
    """
    def test_eventloop_api(self):
        """
        An EventLoop object configured with the real reactor and
        _shutdown.register is exposed via its public methods.
        """
        from twisted.internet import reactor
        from twisted.python.log import startLoggingWithObserver
        from crochet import _shutdown
        self.assertIsInstance(_main, EventLoop)
        self.assertEqual(_main.setup, setup)
        self.assertEqual(_main.no_setup, no_setup)
        self.assertEqual(_main.in_reactor, in_reactor)
        self.assertEqual(_main.run_in_reactor, run_in_reactor)
        self.assertIdentical(_main._reactor, reactor)
        self.assertIdentical(_main._atexit_register, _shutdown.register)
        self.assertIdentical(_main._startLoggingWithObserver, startLoggingWithObserver)
        self.assertIdentical(_main._watchdog_thread, _shutdown._watchdog)

    def test_retrieve_result(self):
        """
        retrieve_result() calls retrieve() on the global ResultStore.
        """
        dr = EventualResult(Deferred())
        uid = dr.stash()
        self.assertIdentical(dr, retrieve_result(uid))
