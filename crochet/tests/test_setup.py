"""
Tests for the initial setup.
"""

from __future__ import absolute_import

import threading

from twisted.trial.unittest import TestCase
from twisted.python.log import PythonLoggingObserver

from .._eventloop import EventLoop, ThreadLogObserver


class FakeReactor(object):
    """
    A fake reactor for testing purposes.
    """
    thread_id = None
    runs = 0
    in_call_from_thread = False

    def __init__(self):
        self.started = threading.Event()
        self.stopping = False
        self.events = []

    def run(self, installSignalHandlers=True):
        self.runs += 1
        self.thread_id = threading.current_thread().ident
        self.installSignalHandlers = installSignalHandlers
        self.started.set()

    def callFromThread(self, f, *args, **kwargs):
        self.in_call_from_thread = True
        f(*args, **kwargs)
        self.in_call_from_thread = False

    def stop(self):
        self.stopping = True

    def addSystemEventTrigger(self, when, event, f):
        self.events.append((when, event, f))


class SetupTests(TestCase):
    """
    Tests for setup().
    """

    def test_first_runs_reactor(self):
        """
        With it first call, setup() runs the reactor in a thread.
        """
        reactor = FakeReactor()
        EventLoop(reactor, lambda f, g: None).setup()
        reactor.started.wait(5)
        self.assertNotEqual(reactor.thread_id, None)
        self.assertNotEqual(reactor.thread_id, threading.current_thread().ident)
        self.assertFalse(reactor.installSignalHandlers)

    def test_second_does_nothing(self):
        """
        The second call to setup() does nothing.
        """
        reactor = FakeReactor()
        s = EventLoop(reactor, lambda f, g: None)
        s.setup()
        s.setup()
        reactor.started.wait(5)
        self.assertEqual(reactor.runs, 1)

    def test_stop_on_exit(self):
        """
        setup() registers an exit handler that stops the reactor.
        """
        atexit = []
        reactor = FakeReactor()
        s = EventLoop(reactor, lambda f, arg: atexit.append((f, arg)))
        s.setup()
        self.assertTrue(atexit)
        self.assertFalse(reactor.stopping)
        f, arg = atexit[0]
        self.assertEqual(f, reactor.callFromThread)
        self.assertEqual(arg, reactor.stop)
        f(arg)
        self.assertTrue(reactor.stopping)

    def test_runs_with_lock(self):
        """
        All code in setup() is protected by a lock.
        """
    test_runs_with_lock.skip = "Need to figure out how to do this decently"

    def test_logging(self):
        """
        setup() registers a PythonLoggingObserver wrapped in a
        ThreadLogObserver, removing the default log observer.
        """
        logging = []
        def fakeStartLoggingWithObserver(observer, setStdout=1):
            self.assertIsInstance(observer, ThreadLogObserver)
            wrapped = observer._observer
            expected = PythonLoggingObserver.emit
            # Python 3 and 2 differ in value of __func__:
            expected = getattr(expected, "__func__", expected)
            self.assertIdentical(wrapped.__func__, expected)
            self.assertEqual(setStdout, False)
            self.assertTrue(reactor.in_call_from_thread)
            logging.append(observer)

        reactor = FakeReactor()
        loop = EventLoop(reactor, lambda f, g: None, fakeStartLoggingWithObserver)
        loop.setup()
        self.assertTrue(logging)
        logging[0].stop()

    def test_stop_logging_on_exit(self):
        """
        setup() registers a reactor shutdown event that stops the logging thread.
        """
        observers = []
        reactor = FakeReactor()
        s = EventLoop(reactor, lambda f, arg: None,
                      lambda observer, setStdout=1: observers.append(observer))
        s.setup()
        self.addCleanup(observers[0].stop)
        self.assertEqual(reactor.events,
                         [("after", "shutdown", observers[0].stop)])


class ThreadLogObserverTest(TestCase):
    """
    Tests for ThreadLogObserver.
    """
    def test_stop(self):
        """
        ThreadLogObserver.stop() stops the thread started in __init__.
        """
        threadLog = ThreadLogObserver(None)
        self.assertTrue(threadLog._thread.is_alive())
        threadLog.stop()
        threadLog._thread.join()
        self.assertFalse(threadLog._thread.is_alive())

    def test_emit(self):
        """
        ThreadLogObserver.emit runs the wrapped observer's in its thread, with
        the given message.
        """
        log = []
        def observer(msg):
            log.append((threading.current_thread().ident, msg))

        threadLog = ThreadLogObserver(observer)
        ident = threadLog._thread.ident
        msg1 = {}
        msg2 = {"a": "b"}
        threadLog(msg1)
        threadLog(msg2)
        threadLog.stop()
        # Wait for writing to finish:
        threadLog._thread.join()
        self.assertEqual(log, [(ident, msg1), (ident, msg2)])
