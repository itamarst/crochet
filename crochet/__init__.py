"""
Crochet: Use Twisted Anywhere!
"""

from __future__ import absolute_import

import sys

from twisted.internet import reactor
from twisted.python.log import startLoggingWithObserver
try:
    from twisted.internet.process import reapAllProcesses
except SyntaxError:
    if sys.version_info < (3, 3, 0):
        raise
    else:
        # Process support is still not ported to Python 3 on some versions of
        # Twisted.
        reapAllProcesses = lambda: None

from ._shutdown import _watchdog, register
from ._eventloop import (EventualResult, TimeoutError, EventLoop, _store,
                         ReactorStopped)
from ._version import __version__

_main = EventLoop(reactor, register, startLoggingWithObserver,
                  _watchdog, reapAllProcesses)
setup = _main.setup
no_setup = _main.no_setup
run_in_reactor = _main.run_in_reactor
wait_for_reactor = _main.wait_for_reactor
retrieve_result = _store.retrieve

# Backwards compatibility with 0.5.0:
in_reactor = _main.in_reactor
DeferredResult = EventualResult


__all__ = ["setup", "run_in_reactor", "EventualResult", "TimeoutError",
           "retrieve_result", "no_setup", "wait_for_reactor",
           "ReactorStopped",
           # Backwards compatibility:
           "DeferredResult", "in_reactor",
           ]
