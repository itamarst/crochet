"""
Crochet!
"""

from __future__ import absolute_import

from twisted.internet import reactor
from twisted.python.log import startLoggingWithObserver

from ._shutdown import _watchdog, register
from ._eventloop import EventualResult, TimeoutError, EventLoop, _store

_main = EventLoop(reactor, register, startLoggingWithObserver,
                  _watchdog)
setup = _main.setup
no_setup = _main.no_setup
run_in_reactor = _main.run_in_reactor
retrieve_result = _store.retrieve

# Backwards compatibility with 0.5.0:
in_reactor = _main.in_reactor
DeferredResult = EventualResult


__version__ = "0.5.0"

__all__ = ["setup", "run_in_reactor", "EventualResult", "TimeoutError",
           "retrieve_result", "no_setup",
           # Backwards compatibility:
           "DeferredResult", "in_reactor",
           ]
