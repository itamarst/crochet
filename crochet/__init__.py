"""
Crochet: Use Twisted Anywhere!
"""
from __future__ import absolute_import

from twisted.python.log import startLoggingWithObserver

from ._shutdown import get_watchdog_thread, register
from ._eventloop import (EventualResult, TimeoutError, EventLoop, _store,
                         ReactorStopped)
from ._util import get_twisted_reactor, reapAllProcesses
from ._version import get_versions

__version__ = get_versions()['version']
del get_versions

_main = EventLoop(get_twisted_reactor, register, startLoggingWithObserver,
                  get_watchdog_thread, reapAllProcesses)
setup = _main.setup
no_setup = _main.no_setup
destroy = _main.destroy
run_in_reactor = _main.run_in_reactor
wait_for = _main.wait_for
retrieve_result = _store.retrieve

# Backwards compatibility with 0.5.0:
in_reactor = _main.in_reactor
DeferredResult = EventualResult

def get_reactor():
    return _main._reactor

# Backwards compatibility with 1.1.0 and earlier:
wait_for_reactor = _main.wait_for_reactor

__all__ = ["setup", "run_in_reactor", "EventualResult", "TimeoutError",
           "destroy", "get_reactor", "retrieve_result", "no_setup", "wait_for",
           "ReactorStopped", "__version__",
           # Backwards compatibility:
           "DeferredResult", "in_reactor", "wait_for_reactor",
           ]
