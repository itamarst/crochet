"""Tests for the logging bridge."""

from __future__ import absolute_import

from twisted.trial.unittest import SynchronousTestCase
import threading

from twisted.python import threadable

from .._eventloop import ThreadLogObserver


class ThreadLogObserverTest(SynchronousTestCase):
    """
    Tests for ThreadLogObserver.

    We use Twisted's SyncTestCase to ensure that unhandled logged errors get
    reported as errors, in particular for test_error.
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
        messages = []
        def observer(msg):
            messages.append((threading.current_thread().ident, msg))

        threadLog = ThreadLogObserver(observer)
        ident = threadLog._thread.ident
        msg1 = {}
        msg2 = {"a": "b"}
        threadLog(msg1)
        threadLog(msg2)
        threadLog.stop()
        # Wait for writing to finish:
        threadLog._thread.join()
        self.assertEqual(messages, [(ident, msg1), (ident, msg2)])

    def test_errors(self):
        """
        ThreadLogObserver.emit catches and silently drops exceptions from its
        observer.
        """
        messages = []
        counter = []
        def observer(msg):
            counter.append(1)
            if len(counter) == 2:
                raise RuntimeError("ono a bug")
            messages.append(msg)

        threadLog = ThreadLogObserver(observer)
        msg1 = {"m": "1"}
        msg2 = {"m": "2"}
        msg3 = {"m": "3"}
        threadLog(msg1)
        threadLog(msg2)
        threadLog(msg3)
        threadLog.stop()
        # Wait for writing to finish:
        threadLog._thread.join()
        self.assertEqual(messages, [msg1, msg3])

    def test_ioThreadUnchanged(self):
        """
        ThreadLogObserver does not change the Twisted I/O thread (which is
        supposed to match the thread the main reactor is running in.)
        """
        threadLog = ThreadLogObserver(None)
        threadLog.stop()
        threadLog._thread.join()
        self.assertIn(threadable.ioThread,
                      # Either reactor was never run, or run in thread running
                      # the tests:
                      (None, threading.current_thread().ident))
