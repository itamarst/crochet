"""
Crochet!
"""

from __future__ import absolute_import

import atexit
from twisted.internet import reactor
from twisted.python.log import startLoggingWithObserver

from ._shutdown import _watchdog
from ._eventloop import DeferredResult, TimeoutError, EventLoop, _store

_main = EventLoop(reactor, _shutdown.register, startLoggingWithObserver,
                  _watchdog)
setup = _main.setup
in_event_loop = _main.in_event_loop
retrieve_result = _store.retrieve


__all__ = ["setup", "in_event_loop", "DeferredResult", "TimeoutError",
           "resultstore"]
