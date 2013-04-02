"""
Crochet!
"""

from __future__ import absolute_import

import atexit
from twisted.internet import reactor
from twisted.python.log import startLoggingWithObserver

from ._eventloop import DeferredResult, TimeoutError, EventLoop
from ._resultstore import ResultStore

_main = EventLoop(reactor, atexit.register, startLoggingWithObserver)
setup = _main.setup
in_event_loop = _main.in_event_loop
resultstore = ResultStore()


__all__ = ["setup", "in_event_loop", "DeferredResult", "TimeoutError", "resultstore"]
