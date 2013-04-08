"""
Crochet!
"""

from __future__ import absolute_import

from twisted.internet import reactor
from twisted.python.log import startLoggingWithObserver

from ._shutdown import _watchdog, register
from ._eventloop import DeferredResult, TimeoutError, EventLoop, _store

_main = EventLoop(reactor, register, startLoggingWithObserver,
                  _watchdog)
setup = _main.setup
no_setup = _main.no_setup
in_event_loop = _main.in_event_loop
retrieve_result = _store.retrieve

__version__ = "0.5"

__all__ = ["setup", "in_event_loop", "DeferredResult", "TimeoutError",
           "retrieve_result", "no_setup"]
