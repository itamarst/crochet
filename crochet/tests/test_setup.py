"""
Tests for the initial setup.
"""

from __future__ import absolute_import

import threading
import warnings
import subprocess
import sys
from unittest import SkipTest, TestCase

import twisted
from twisted.python.log import PythonLoggingObserver
from twisted.python import log
from twisted.python.runtime import platform
from twisted.internet.task import Clock

from .._eventloop import EventLoop, ThreadLogObserver, _store
from ..tests import crochet_directory


class FakeReactor(Clock):
    """
    A fake reactor for testing purposes.
    """
    thread_id = None
    runs = 0
    in_call_from_thread = False

    def __init__(self):
        Clock.__init__(self)
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


class FakeThread:
    started = False

    def start(self):
        self.started = True


class SetupTests(TestCase):
    """
    Tests for setup().
    """

    def test_first_runs_reactor(self):
        """
        With it first call, setup() runs the reactor in a thread.
        """
        reactor = FakeReactor()
        EventLoop(lambda: reactor, lambda f, *g: None).setup()
        reactor.started.wait(5)
        self.assertNotEqual(reactor.thread_id, None)
        self.assertNotEqual(reactor.thread_id, threading.current_thread().ident)
        self.assertFalse(reactor.installSignalHandlers)

    def test_second_does_nothing(self):
        """
        The second call to setup() does nothing.
        """
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *g: None)
        s.setup()
        s.setup()
        reactor.started.wait(5)
        self.assertEqual(reactor.runs, 1)

    def test_stop_on_exit(self):
        """
        setup() registers an exit handler that stops the reactor, and an exit
        handler that logs stashed EventualResults.
        """
        atexit = []
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *args: atexit.append((f, args)))
        s.setup()
        self.assertEqual(len(atexit), 2)
        self.assertFalse(reactor.stopping)
        f, args = atexit[0]
        self.assertEqual(f, reactor.callFromThread)
        self.assertEqual(args, (reactor.stop,))
        f(*args)
        self.assertTrue(reactor.stopping)
        f, args = atexit[1]
        self.assertEqual(f, _store.log_errors)
        self.assertEqual(args, ())
        f(*args) # make sure it doesn't throw an exception

    def test_runs_with_lock(self):
        """
        All code in setup() and no_setup() is protected by a lock.
        """
        self.assertTrue(EventLoop.setup.synchronized)
        self.assertTrue(EventLoop.no_setup.synchronized)

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
            self.assertIs(wrapped.__func__, expected)
            self.assertEqual(setStdout, False)
            self.assertTrue(reactor.in_call_from_thread)
            logging.append(observer)

        reactor = FakeReactor()
        loop = EventLoop(lambda: reactor, lambda f, *g: None,
                         fakeStartLoggingWithObserver)
        loop.setup()
        self.assertTrue(logging)
        logging[0].stop()

    def test_stop_logging_on_exit(self):
        """
        setup() registers a reactor shutdown event that stops the logging thread.
        """
        observers = []
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *arg: None,
                      lambda observer, setStdout=1: observers.append(observer))
        s.setup()
        self.addCleanup(observers[0].stop)
        self.assertIn(("after", "shutdown", observers[0].stop), reactor.events)

    def test_warnings_untouched(self):
        """
        setup() ensure the warnings module's showwarning is unmodified,
        overriding the change made by normal Twisted logging setup.
        """
        def fakeStartLoggingWithObserver(observer, setStdout=1):
            warnings.showwarning = log.showwarning
            self.addCleanup(observer.stop)
        original = warnings.showwarning
        reactor = FakeReactor()
        loop = EventLoop(lambda: reactor, lambda f, *g: None,
                         fakeStartLoggingWithObserver)
        loop.setup()
        self.assertIs(warnings.showwarning, original)

    def test_start_watchdog_thread(self):
        """
        setup() starts the shutdown watchdog thread.
        """
        thread = FakeThread()
        reactor = FakeReactor()
        loop = EventLoop(lambda: reactor, lambda *args: None,
                         watchdog_thread=thread)
        loop.setup()
        self.assertTrue(thread.started)

    def test_no_setup(self):
        """
        If called first, no_setup() makes subsequent calls to setup() do
        nothing.
        """
        observers = []
        atexit = []
        thread = FakeThread()
        reactor = FakeReactor()
        loop = EventLoop(lambda: reactor, lambda f, *arg: atexit.append(f),
                         lambda observer, *a, **kw: observers.append(observer),
                         watchdog_thread=thread)

        loop.no_setup()
        loop.setup()
        self.assertFalse(observers)
        self.assertFalse(atexit)
        self.assertFalse(reactor.runs)
        self.assertFalse(thread.started)

    def test_no_setup_after_setup(self):
        """
        If called after setup(), no_setup() throws an exception.
        """
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *g: None)
        s.setup()
        self.assertRaises(RuntimeError, s.no_setup)

    def test_setup_registry_shutdown(self):
        """
        ResultRegistry.stop() is registered to run before reactor shutdown by
        setup().
        """
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *g: None)
        s.setup()
        self.assertEqual(reactor.events,
                         [("before", "shutdown", s._registry.stop)])


    def test_no_setup_registry_shutdown(self):
        """
        ResultRegistry.stop() is registered to run before reactor shutdown by
        setup().
        """
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *g: None)
        s.no_setup()
        self.assertEqual(reactor.events,
                         [("before", "shutdown", s._registry.stop)])


class ProcessSetupTests(TestCase):
    """
    setup() enables support for IReactorProcess on POSIX plaforms.
    """
    def test_posix(self):
        """
        On POSIX systems, setup() installs a LoopingCall that runs
        t.i.process.reapAllProcesses() 10 times a second.
        """
        reactor = FakeReactor()
        reaps = []
        s = EventLoop(lambda: reactor, lambda f, *g: None,
                      reapAllProcesses=lambda: reaps.append(1))
        s.setup()
        reactor.advance(0.1)
        self.assertEquals(reaps, [1])
        reactor.advance(0.1)
        self.assertEquals(reaps, [1, 1])
        reactor.advance(0.1)
        self.assertEquals(reaps, [1, 1, 1])
    if platform.type != "posix":
        test_posix.skip = "SIGCHLD is a POSIX-specific issue"

    def test_non_posix(self):
        """
        On non-POSIX systems, setup() does not install a LoopingCall.
        """
        if platform.type == "posix":
            raise SkipTest("This test is for non-POSIX systems.")
        reactor = FakeReactor()
        s = EventLoop(lambda: reactor, lambda f, *g: None)
        s.setup()
        self.assertFalse(reactor.getDelayedCalls())


class ReactorImportTests(TestCase):
    """
    Tests for when the reactor gets imported.

    The reactor should only be imported as part of setup()/no_setup(),
    rather than as side-effect of Crochet import, since daemonization
    doesn't work if reactor is imported
    (https://twistedmatrix.com/trac/ticket/7105).
    """
    def test_crochet_import_no_reactor(self):
        """
        Importing crochet should not import the reactor.
        """
        program = """\
import sys
import crochet

if "twisted.internet.reactor" not in sys.modules:
    sys.exit(23)
"""
        process = subprocess.Popen([sys.executable, "-c", program],
                                   cwd=crochet_directory)
        self.assertEqual(process.wait(), 23)


LOGGING_PROGRAM = """\
import sys
from logging import StreamHandler, Formatter, getLogger, DEBUG
handler = StreamHandler(sys.stdout)
handler.setFormatter(Formatter("%%(levelname)s %%(message)s"))
l = getLogger("twisted")
l.addHandler(handler)
l.setLevel(DEBUG)

import crochet
crochet.setup()
from twisted.python import log
%s
log.msg("log-info")
log.msg("log-error", isError=True)
"""

class LoggingTests(TestCase):
    """
    End-to-end tests for Twisted->stdlib logging bridge.
    """
    maxDiff = None

    def test_old_logging(self):
        """
        Messages from the old Twisted logging API are emitted to Python
        standard library logging.
        """
        if tuple(map(int, twisted.__version__.split("."))) >= (15, 2, 0):
            raise SkipTest("This test is for Twisted < 15.2.")

        program = LOGGING_PROGRAM % ("",)
        output = subprocess.check_output([sys.executable, "-u", "-c", program],
                                         cwd=crochet_directory)
        self.assertTrue(output.startswith("""\
INFO Log opened.
INFO log-info
ERROR log-error
"""))

    def test_new_logging(self):
        """
        Messages from both new and old Twisted logging APIs are emitted to Python
        standard library logging.
        """
        if tuple(map(int, twisted.__version__.split("."))) < (15, 2, 0):
            raise SkipTest("This test is for Twisted 15.2 and later.")

        program = LOGGING_PROGRAM % ("""\
from twisted.logger import Logger
l2 = Logger()
import time
time.sleep(1)  # workaround, there is race condition... somewhere
l2.info("logger-info")
l2.critical("logger-critical")
l2.warn("logger-warning")
l2.debug("logger-debug")
""",)
        output = subprocess.check_output([sys.executable, "-u", "-c", program],
                                         cwd=crochet_directory)
        self.assertIn("""\
INFO logger-info
CRITICAL logger-critical
WARNING logger-warning
DEBUG logger-debug
INFO log-info
CRITICAL log-error
""", output.decode("utf-8"))

