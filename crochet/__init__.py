"""
Crochet!
"""

from __future__ import absolute_import

import atexit
from twisted.internet import reactor

from ._eventloop import DeferredResult, TimeoutError, EventLoop

__all__ = ["setup", "in_event_loop", "DeferredResult", "TimeoutError"]


_main = EventLoop(reactor, atexit.register)
setup = _main.setup
in_event_loop = _main.in_event_loop
