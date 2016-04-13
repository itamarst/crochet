"""
Tests for IReactorProcess.
"""

import subprocess
import sys

from twisted.trial.unittest import TestCase
from twisted.python.runtime import platform

from ..tests import crochet_directory

class ProcessTests(TestCase):
    """
    Tests for process support.
    """
    def test_processExit(self):
        """
        A Crochet-managed reactor notice when a process it started exits.

        On POSIX platforms this requies waitpid() to be called, which in
        default Twisted implementation relies on a SIGCHLD handler which is not
        installed by Crochet at the moment.
        """
        program = """\
from crochet import setup, run_in_reactor
setup()

import sys
import os
from twisted.internet.protocol import ProcessProtocol
from twisted.internet.defer import Deferred
from twisted.internet import reactor

class Waiter(ProcessProtocol):
    def __init__(self):
        self.result = Deferred()

    def processExited(self, reason):
        self.result.callback(None)


@run_in_reactor
def run():
    waiter = Waiter()
    # Closing FDs before exit forces us to rely on SIGCHLD to notice process
    # exit:
    reactor.spawnProcess(waiter, sys.executable,
                         [sys.executable, '-c',
                          'import os; os.close(0); os.close(1); os.close(2)'],
                         env=os.environ)
    return waiter.result

run().wait(10)
# If we don't notice process exit, TimeoutError will be thrown and we won't
# reach the next line:
sys.stdout.write("abc")
"""
        process = subprocess.Popen([sys.executable, "-c", program],
                                   cwd=crochet_directory,
                                   stdout=subprocess.PIPE)
        result = process.stdout.read()
        self.assertEqual(result, b"abc")
    if platform.type != "posix":
        test_processExit.skip = "SIGCHLD is a POSIX-specific issue"
