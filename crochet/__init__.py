"""
Crochet: Use Twisted Anywhere!
"""

from __future__ import absolute_import

import sys

from twisted.python.log import startLoggingWithObserver
from twisted.python.runtime import platform
if platform.type == "posix":
    try:
        from twisted.internet.process import reapAllProcesses
    except (SyntaxError, ImportError):
        if sys.version_info < (3, 3, 0):
            raise
        else:
            # Process support is still not ported to Python 3 on some versions
            # of Twisted.
            reapAllProcesses = lambda: None
else:
    # waitpid() is only necessary on POSIX:
    reapAllProcesses = lambda: None

from ._shutdown import _watchdog, register
from ._eventloop import (EventualResult, TimeoutError, EventLoop, _store,
                         ReactorStopped)
from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


def _importReactor():
    from twisted.internet import reactor
    return reactor
_main = EventLoop(_importReactor, register, startLoggingWithObserver,
                  _watchdog, reapAllProcesses)
setup = _main.setup
no_setup = _main.no_setup
run_in_reactor = _main.run_in_reactor
wait_for = _main.wait_for
retrieve_result = _store.retrieve

# Backwards compatibility with 0.5.0:
in_reactor = _main.in_reactor
DeferredResult = EventualResult

# Backwards compatibility with 1.1.0 and earlier:
wait_for_reactor = _main.wait_for_reactor

__all__ = ["setup", "run_in_reactor", "EventualResult", "TimeoutError",
           "retrieve_result", "no_setup", "wait_for",
           "ReactorStopped", "__version__",
           # Backwards compatibility:
           "DeferredResult", "in_reactor", "wait_for_reactor",
           ]
