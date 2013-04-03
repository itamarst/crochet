"""
Tests for _shutdown.
"""

from __future__ import absolute_import

import sys
import os

from twisted.trial.unittest import TestCase
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred


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

from crochet._shutdown import register

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
        done = Deferred()

        class Accumulate(protocol.ProcessProtocol):
            buffer = ""
            def outReceived(self, data):
                self.buffer += data
            def errReceived(self, data):
                print "ERR", data
            def processExited(self, reason):
                done.callback(True)

        pp = Accumulate()
        reactor.spawnProcess(pp, sys.executable,
                             [sys.executable, "-c", program],
                             env=os.environ)

        def check(result):
            self.assertEqual(pp.buffer, "byebye")
        done.addCallback(check)
        return done
