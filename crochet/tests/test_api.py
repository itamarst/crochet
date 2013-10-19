"""
Tests for the crochet APIs.
"""

from __future__ import absolute_import

import threading
import subprocess
import time
import gc
import sys
import weakref

from twisted.trial.unittest import TestCase, SkipTest
from twisted.internet.defer import succeed, Deferred, fail, CancelledError
from twisted.python.failure import Failure
from twisted.python import threadable
from twisted.python.runtime import platform
try:
    from twisted.internet.process import reapAllProcesses
except ImportError:
    reapAllProcesses = None
except SyntaxError:
    if sys.version_info < (3, 3, 0):
        raise
    else:
        # Process support is still not ported to Python 3 on some versions of
        # Twisted.
        reapAllProcesses = None

from .._eventloop import (EventLoop, EventualResult, TimeoutError,
                          ResultRegistry, ReactorStopped)
from .test_setup import FakeReactor
from .. import (_main, setup, in_reactor, retrieve_result, _store, no_setup,
                run_in_reactor, wait_for_reactor)



class ResultRegistryTests(TestCase):
    """
    Tests for ResultRegistry.
    """
    def test_stopped_registered(self):
        """
        ResultRegistery.stop() fires registered EventualResult with
        ReactorStopped.
        """
        registry = ResultRegistry(FakeReactor())
        er = EventualResult(None)
        registry.register(er)
        registry.stop()
        self.assertRaises(ReactorStopped, er.wait, timeout=0)

    def test_stopped_new_registration(self):
        """
        After ResultRegistery.stop() is called subsequent register() calls
        raise ReactorStopped.
        """
        registry = ResultRegistry(FakeReactor())
        er = EventualResult(None)
        registry.stop()
        self.assertRaises(ReactorStopped, registry.register, er)

    def test_stopped_already_have_result(self):
        """
        ResultRegistery.stop() has no impact on registered EventualResult
        which already have a result.
        """
        registry = ResultRegistry(FakeReactor())
        er = EventualResult(succeed(123))
        registry.register(er)
        registry.stop()
        self.assertEqual(er.wait(), 123)
        self.assertEqual(er.wait(), 123)
        self.assertEqual(er.wait(), 123)

    def test_weakref(self):
        """
        Registering an EventualResult with a ResultRegistry does not prevent
        it from being garbage collected.
        """
        registry = ResultRegistry(FakeReactor())
        er = EventualResult(None)
        registry.register(er)
        ref = weakref.ref(er)
        del er
        gc.collect()
        self.assertIdentical(ref(), None)

    def test_runs_with_lock(self):
        """
        All code in ResultRegistry.stop() and register() is protected by a
        lock.
        """
        self.assertTrue(ResultRegistry.stop.synchronized)
        self.assertTrue(ResultRegistry.register.synchronized)


class EventualResultTests(TestCase):
    """
    Tests for EventualResult.
    """

    def setUp(self):
        self.patch(threadable, "isInIOThread", lambda: False)

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

    def test_reactor_thread_disallowed(self):
        """
        wait() cannot be called from the reactor thread.
        """
        self.patch(threadable, "isInIOThread", lambda: True)
        d = Deferred()
        dr = EventualResult(d)
        self.assertRaises(RuntimeError, dr.wait, 0)

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
        if sys.version_info[0] == 2:
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

    def test_control_c_is_possible(self):
        """
        If you're wait()ing on an EventualResult in main thread, make sure the
        KeyboardInterrupt happens in timely manner.
        """
        program = """\
import os, threading, signal, time, sys
import crochet
crochet.setup()
from twisted.internet.defer import Deferred

def interrupt():
    time.sleep(0.1) # Make sure we've hit wait()
    os.kill(os.getpid(), signal.SIGINT)
    time.sleep(1)
    # Still running, test shall fail...
    os.kill(os.getpid(), signal.SIGKILL)
t = threading.Thread(target=interrupt)
t.setDaemon(True)
t.start()

d = Deferred()
e = crochet.EventualResult(d)
try:
    # Queue.get() has special non-interruptible behavior if not given timeout,
    # so don't give timeout here.
    e.wait()
except KeyboardInterrupt:
    sys.exit(23)
"""
        process = subprocess.Popen([sys.executable, "-c", program])
        self.assertEqual(process.wait(), 23)

    def test_reactor_stop_unblocks_EventualResult(self):
        """
        Any EventualResult.wait() calls still waiting when the reactor has
        stopped will get a ReactorStopped exception.
        """
        raise SkipTest("Not done yet.")

    def test_connect_deferred(self):
        """
        If an EventualResult is created with None,
        EventualResult._connect_deferred can be called later to register a
        Deferred as the one it is wrapping.
        """
        er = EventualResult(None)
        self.assertRaises(TimeoutError, er.wait, 0)
        d = Deferred()
        er._connect_deferred(d)
        self.assertRaises(TimeoutError, er.wait, 0)
        d.callback(123)
        self.assertEqual(er.wait(), 123)

    def test_reactor_stop_unblocks_EventualResult(self):
        """
        Any EventualResult.wait() calls still waiting when the reactor has
        stopped will get a ReactorStopped exception.
        """
        program = """\
import os, threading, signal, time, sys

from twisted.internet.defer import Deferred
from twisted.internet import reactor

import crochet
crochet.setup()

@crochet.run_in_reactor
def run():
    reactor.callLater(0.1, reactor.stop)
    return Deferred()

er = run()
try:
    er.wait(timeout=10)
except crochet.ReactorStopped:
    sys.exit(23)
"""
        process = subprocess.Popen([sys.executable, "-c", program])
        self.assertEqual(process.wait(), 23)

    def test_reactor_stop_unblocks_EventualResult_in_threadpool(self):
        """
        Any EventualResult.wait() calls still waiting when the reactor has
        stopped will get a ReactorStopped exception, even if it is running in
        Twisted's thread pool.
        """
        program = """\
import os, threading, signal, time, sys

from twisted.internet.defer import Deferred
from twisted.internet import reactor

import crochet
crochet.setup()

@crochet.run_in_reactor
def run():
    reactor.callLater(0.1, reactor.stop)
    return Deferred()

result = [13]
def inthread():
    er = run()
    try:
        er.wait(timeout=10)
    except crochet.ReactorStopped:
        result[0] = 23
reactor.callInThread(inthread)
time.sleep(1)
sys.exit(result[0])
"""
        process = subprocess.Popen([sys.executable, "-c", program])
        self.assertEqual(process.wait(), 23)

    def test_immediate_cancel(self):
        """
        Immediately cancelling the result of @run_in_reactor function will
        still cancel the Deferred.
        """
        # This depends on the way reactor runs callFromThread calls, so need
        # real functional test.
        program = """\
import os, threading, signal, time, sys

from twisted.internet.defer import Deferred, CancelledError

import crochet
crochet.setup()

@crochet.run_in_reactor
def run():
    return Deferred()

er = run()
er.cancel()
try:
    er.wait(1)
except CancelledError:
    sys.exit(23)
else:
    sys.exit(3)
"""
        process = subprocess.Popen([sys.executable, "-c", program])
        self.assertEqual(process.wait(), 23)


class InReactorTests(TestCase):
    """
    Tests for the deprecated in_reactor decorator.
    """

    def test_name(self):
        """
        The function decorated with in_reactor has the same name as the
        original function.
        """
        c = EventLoop(FakeReactor(), lambda f, g: None)

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

    def test_run_in_reactor_wrapper(self):
        """
        in_reactor is implemented on top of run_in_reactor.
        """
        wrapped = [False]

        def fake_run_in_reactor(function):
            def wrapper(*args, **kwargs):
                wrapped[0] = True
                result = function(*args, **kwargs)
                wrapped[0] = False
                return result
            return wrapper

        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)
        c.run_in_reactor = fake_run_in_reactor


        @c.in_reactor
        def func(reactor):
            self.assertTrue(wrapped[0])
            return 17

        result = func()
        self.assertFalse(wrapped[0])
        self.assertEqual(result, 17)


class RunInReactorTests(TestCase):
    """
    Tests for the run_in_reactor decorator.
    """
    def test_name(self):
        """
        The function decorated with run_in_reactor has the same name as the
        original function.
        """
        c = EventLoop(FakeReactor(), lambda f, g: None)

        @c.run_in_reactor
        def some_name():
            pass
        self.assertEqual(some_name.__name__, "some_name")

    def test_run_in_reactor_thread(self):
        """
        The function decorated with run_in_reactor is run in the reactor
        thread.
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
        Return a function wrapped with run_in_reactor that returns its first
        argument.
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

    def test_registry(self):
        """
        @run_in_reactor registers the EventualResult in the ResultRegistry.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)

        @c.run_in_reactor
        def run():
            return

        result = run()
        self.assertIn(result, c._registry._results)


class WaitForReactorTests(TestCase):
    """
    Tests for the wait_for_reactor decorator.
    """
    def test_name(self):
        """
        The function decorated with run_in_reactor has the same name as the
        original function.
        """
        c = EventLoop(FakeReactor(), lambda f, g: None)

        @c.wait_for_reactor
        def some_name():
            pass
        self.assertEqual(some_name.__name__, "some_name")

    def test_reactor_thread_disallowed(self):
        """
        Functions decorated with wait_for_reactor() cannot be called from the
        reactor thread.
        """
        self.patch(threadable, "isInIOThread", lambda: True)
        c = EventLoop(FakeReactor(), lambda f, g: None)
        @c.wait_for_reactor
        def f():
            pass
        self.assertRaises(RuntimeError, f)

    def test_wait_for_reactor_thread(self):
        """
        The function decorated with wait_for_reactor is run in the reactor
        thread.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)
        calls = []

        @c.wait_for_reactor
        def func(a, b, c):
            self.assertTrue(myreactor.in_call_from_thread)
            calls.append((a, b, c))

        func(1, 2, c=3)
        self.assertEqual(calls, [(1, 2, 3)])

    def make_wrapped_function(self):
        """
        Return a function wrapped with wait_for_reactor that returns its first
        argument.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)

        @c.wait_for_reactor
        def passthrough(argument):
            return argument
        return passthrough

    def test_deferred_success_result(self):
        """
        If the underlying function returns a Deferred, the wrapper returns a
        the Deferred's result.
        """
        passthrough = self.make_wrapped_function()
        result = passthrough(succeed(123))
        self.assertEqual(result, 123)

    def test_deferred_failure_result(self):
        """
        If the underlying function returns a Deferred with an errback, the
        wrapper throws an exception.
        """
        passthrough = self.make_wrapped_function()
        self.assertRaises(
            ZeroDivisionError, passthrough, fail(ZeroDivisionError()))

    def test_regular_result(self):
        """
        If the underlying function returns a non-Deferred, the wrapper returns
        that result.
        """
        passthrough = self.make_wrapped_function()
        result = passthrough(123)
        self.assertEqual(result, 123)

    def test_exception_result(self):
        """
        If the underlying function throws an exception, the wrapper raises
        that exception.
        """
        myreactor = FakeReactor()
        c = EventLoop(myreactor, lambda f, g: None)

        @c.wait_for_reactor
        def raiser():
            1/0

        self.assertRaises(ZeroDivisionError, raiser)

    def test_control_c_is_possible(self):
        """
        A call to a decorated function responds to a Ctrl-C (i.e. with a
        KeyboardInterrupt) in a timely manner.
        """
        program = """\
import os, threading, signal, time, sys
import crochet
crochet.setup()
from twisted.internet.defer import Deferred

def interrupt():
    time.sleep(0.1) # Make sure we've hit wait()
    os.kill(os.getpid(), signal.SIGINT)
    time.sleep(1)
    # Still running, test shall fail...
    os.kill(os.getpid(), signal.SIGKILL)
t = threading.Thread(target=interrupt)
t.setDaemon(True)
t.start()

@crochet.wait_for_reactor
def wait():
    return Deferred()

try:
    wait()
except KeyboardInterrupt:
    sys.exit(23)
"""
        process = subprocess.Popen([sys.executable, "-c", program])
        self.assertEqual(process.wait(), 23)

    def test_reactor_stop_unblocks(self):
        """
        Any @wait_for_reactor-decorated calls still waiting when the reactor
        has stopped will get a ReactorStopped exception.
        """
        program = """\
import os, threading, signal, time, sys

from twisted.internet.defer import Deferred
from twisted.internet import reactor

import crochet
crochet.setup()

@crochet.wait_for_reactor
def run():
    reactor.callLater(0.1, reactor.stop)
    return Deferred()

try:
    er = run()
except crochet.ReactorStopped:
    sys.exit(23)
"""
        process = subprocess.Popen([sys.executable, "-c", program])
        self.assertEqual(process.wait(), 23)


class PublicAPITests(TestCase):
    """
    Tests for the public API.
    """
    def test_no_sideeffects(self):
        """
        Creating an EventLoop object, as is done in crochet.__init__, does not
        call any methods on the objects it is created with.
        """
        c = EventLoop(None, lambda f, g: 1/0, lambda *args: 1/0,
                      watchdog_thread=object(), reapAllProcesses=lambda: 1/0)
        del c

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
        self.assertEqual(_main.wait_for_reactor, wait_for_reactor)
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

    def test_reapAllProcesses(self):
        """
        An EventLoop object configured with the real reapAllProcesses on POSIX
        plaforms.
        """
        self.assertIdentical(_main._reapAllProcesses, reapAllProcesses)
    if platform.type != "posix":
        test_reapAllProcesses.skip = "Only relevant on POSIX platforms"
    if reapAllProcesses is None:
        test_reapAllProcesses.skip = "Twisted does not yet support processes"
