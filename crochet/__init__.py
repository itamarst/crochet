"""
Crochet: Use Twisted Anywhere!
"""

from twisted.python.log import startLoggingWithObserver
from twisted.python.runtime import platform

from ._shutdown import _watchdog, register
from ._eventloop import (
    EventualResult, EventLoop, _store, ReactorStopped
)
from ._eventloop import TimeoutError  # pylint: disable=redefined-builtin
from ._version import get_versions

if platform.type == "posix":
    from twisted.internet.process import reapAllProcesses
else:
    # waitpid() is only necessary on POSIX:
    def reapAllProcesses(): pass


__version__ = get_versions()['version']
del get_versions


def _importReactor():
    from twisted.internet import reactor
    return reactor


_main = EventLoop(
    _importReactor, register, startLoggingWithObserver, _watchdog,
    reapAllProcesses)
setup = _main.setup
no_setup = _main.no_setup
run_in_reactor = _main.run_in_reactor
wait_for = _main.wait_for
retrieve_result = _store.retrieve


__all__ = [
    "setup",
    "run_in_reactor",
    "EventualResult",
    "TimeoutError",
    "retrieve_result",
    "no_setup",
    "wait_for",
    "ReactorStopped",
    "__version__",
]
