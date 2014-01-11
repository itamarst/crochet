"""
Tests for _shutdown.
"""

from __future__ import absolute_import

import sys
import subprocess
import time

from twisted.trial.unittest import TestCase

from crochet._shutdown import (Watchdog, FunctionRegistry, _watchdog, register,
                               _registry)
from ..tests import crochet_directory


class ShutdownTests(TestCase):
    """
    Tests for shutdown registration.
    """
    def test_shutdown(self):
        """
        A function registered with _shutdown.register() is called when the
        main thread exits.
        """
        program = """\
import threading, sys

from crochet._shutdown import register, _watchdog
_watchdog.start()

end = False

def thread():
    while not end:
        pass
    sys.stdout.write("byebye")
    sys.stdout.flush()

def stop(x, y):
    # Move this into separate test at some point.
    assert x == 1
    assert y == 2
    global end
    end = True

threading.Thread(target=thread).start()
register(stop, 1, y=2)

sys.exit()
"""
        process = subprocess.Popen([sys.executable, "-c", program],
                                   cwd=crochet_directory,
                                   stdout=subprocess.PIPE)
        result = process.stdout.read()
        self.assertEqual(process.wait(), 0)
        self.assertEqual(result, b"byebye")

    def test_watchdog(self):
        """
        The watchdog thread exits when the thread it is watching exits, and
        calls its shutdown function.
        """
        done = []
        alive = True

        class FakeThread:
            def is_alive(self):
                return alive

        w = Watchdog(FakeThread(), lambda: done.append(True))
        w.start()
        time.sleep(0.2)
        self.assertTrue(w.is_alive())
        self.assertFalse(done)
        alive = False
        time.sleep(0.2)
        self.assertTrue(done)
        self.assertFalse(w.is_alive())

    def test_api(self):
        """
        The module exposes a shutdown thread that will call a global
        registry's run(), and a register function tied to the global registry.
        """
        self.assertIsInstance(_registry, FunctionRegistry)
        self.assertEqual(register, _registry.register)
        self.assertIsInstance(_watchdog, Watchdog)
        self.assertEqual(_watchdog._shutdown_function, _registry.run)


class FunctionRegistryTests(TestCase):
    """
    Tests for FunctionRegistry.
    """

    def test_called(self):
        """
        Functions registered with a FunctionRegistry are called in reverse
        order by run().
        """
        result = []
        registry = FunctionRegistry()
        registry.register(lambda: result.append(1))
        registry.register(lambda x: result.append(x), 2)
        registry.register(lambda y: result.append(y), y=3)
        registry.run()
        self.assertEqual(result, [3, 2, 1])

    def test_log_errors(self):
        """
        Registered functions that raise an error have the error logged, and
        run() continues processing.
        """
        result = []
        registry = FunctionRegistry()
        registry.register(lambda: result.append(2))
        registry.register(lambda: 1/0)
        registry.register(lambda: result.append(1))
        registry.run()
        self.assertEqual(result, [1, 2])
        excs = self.flushLoggedErrors(ZeroDivisionError)
        self.assertEqual(len(excs), 1)
