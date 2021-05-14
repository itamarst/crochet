"""
Expose Twisted's event loop to threaded programs.
"""

from __future__ import absolute_import

import select
import threading
import weakref
import warnings
from inspect import iscoroutinefunction
from functools import wraps

from twisted.python import threadable
from twisted.python.runtime import platform
from twisted.python.failure import Failure
from twisted.python.log import PythonLoggingObserver, err
from twisted.internet.defer import maybeDeferred, ensureDeferred
from twisted.internet.task import LoopingCall

import wrapt

from ._util import synchronized
from ._resultstore import ResultStore

_store = ResultStore()


class TimeoutError(Exception):  # pylint: disable=redefined-builtin
    """
    A timeout has been hit.
    """


class ReactorStopped(Exception):
    """
    The reactor has stopped, and therefore no result will ever become
    available from this EventualResult.
    """


class ResultRegistry(object):
    """
    Keep track of EventualResults.

    Once the reactor has shutdown:

    1. Registering new EventualResult instances is an error, since no results
       will ever become available.
    2. Already registered EventualResult instances are "fired" with a
       ReactorStopped exception to unblock any remaining EventualResult.wait()
       calls.
    """

    def __init__(self):
        self._results = weakref.WeakSet()
        self._stopped = False
        self._lock = threading.Lock()

    @synchronized
    def register(self, result):
        """
        Register an EventualResult.

        May be called in any thread.
        """
        if self._stopped:
            raise ReactorStopped()
        self._results.add(result)

    @synchronized
    def stop(self):
        """
        Indicate no more results will get pushed into EventualResults, since
        the reactor has stopped.

        This should be called in the reactor thread.
        """
        self._stopped = True
        for result in self._results:
            result._set_result(Failure(ReactorStopped()))


class EventualResult(object):
    """
    A blocking interface to Deferred results.

    This allows you to access results from Twisted operations that may not be
    available immediately, using the wait() method.

    In general you should not create these directly; instead use functions
    decorated with @run_in_reactor.
    """

    def __init__(self, deferred, _reactor):
        """
        The deferred parameter should be a Deferred or None indicating
        _connect_deferred will be called separately later.
        """
        self._deferred = deferred
        self._reactor = _reactor
        self._value = None
        self._result_retrieved = False
        self._result_set = threading.Event()
        if deferred is not None:
            self._connect_deferred(deferred)

    def _connect_deferred(self, deferred):
        """
        Hook up the Deferred that that this will be the result of.

        Should only be run in Twisted thread, and only called once.
        """
        self._deferred = deferred

        # Because we use __del__, we need to make sure there are no cycles
        # involving this object, which is why we use a weakref:
        def put(result, eventual=weakref.ref(self)):
            eventual = eventual()
            if eventual:
                eventual._set_result(result)
            else:
                err(result, "Unhandled error in EventualResult")

        deferred.addBoth(put)

    def _set_result(self, result):
        """
        Set the result of the EventualResult, if not already set.

        This can only happen in the reactor thread, either as a result of
        Deferred firing, or as a result of ResultRegistry.stop(). So, no need
        for thread-safety.
        """
        if self._result_set.isSet():
            return
        self._value = result
        self._result_set.set()

    def __del__(self):
        if self._result_retrieved or not self._result_set.isSet():
            return
        if isinstance(self._value, Failure):
            err(self._value, "Unhandled error in EventualResult")

    def cancel(self):
        """
        Try to cancel the operation by cancelling the underlying Deferred.

        Cancellation of the operation may or may not happen depending on
        underlying cancellation support and whether the operation has already
        finished. In any case, however, the underlying Deferred will be fired.

        Multiple calls will have no additional effect.
        """
        self._reactor.callFromThread(lambda: self._deferred.cancel())

    def _result(self, timeout):
        """
        Return the result, if available.

        It may take an unknown amount of time to return the result, so a
        timeout option is provided. If the given number of seconds pass with
        no result, a TimeoutError will be thrown.

        If a previous call timed out, additional calls to this function will
        still wait for a result and return it if available. If a result was
        returned on one call, additional calls will return/raise the same
        result.
        """
        self._result_set.wait(timeout)
        # In Python 2.6 we can't rely on the return result of wait(), so we
        # have to check manually:
        if not self._result_set.is_set():
            raise TimeoutError()
        self._result_retrieved = True
        return self._value

    def wait(self, timeout):
        """
        Return the result, or throw the exception if result is a failure.

        It may take an unknown amount of time to return the result, so a
        timeout option is provided. If the given number of seconds pass with
        no result, a TimeoutError will be thrown.

        If a previous call timed out, additional calls to this function will
        still wait for a result and return it if available. If a result was
        returned or raised on one call, additional calls will return/raise the
        same result.
        """
        if threadable.isInIOThread():
            raise RuntimeError(
                "EventualResult.wait() must not be run in the reactor thread.")

        result = self._result(timeout)
        if isinstance(result, Failure):
            result.raiseException()
        return result

    def stash(self):
        """
        Store the EventualResult in memory for later retrieval.

        Returns a integer uid which can be passed to crochet.retrieve_result()
        to retrieve the instance later on.
        """
        return _store.store(self)

    def original_failure(self):
        """
        Return the underlying Failure object, if the result is an error.

        If no result is yet available, or the result was not an error, None is
        returned.

        This method is useful if you want to get the original traceback for an
        error result.
        """
        try:
            result = self._result(0.0)
        except TimeoutError:
            return None
        if isinstance(result, Failure):
            return result
        else:
            return None


class ThreadLogObserver(object):
    """
    A log observer that wraps another observer, and calls it in a thread.

    In particular, used to wrap PythonLoggingObserver, so that blocking
    logging.py Handlers don't block the event loop.

    Once Python 3.6 support is dropped, this can use a queue.SimpleQueue object
    instead of a whole 'nother event loop.
    """

    def __init__(self, observer):
        self._observer = observer
        if getattr(select, "epoll", None):
            from twisted.internet.epollreactor import EPollReactor
            reactorFactory = EPollReactor
        elif getattr(select, "poll", None):
            from twisted.internet.pollreactor import PollReactor
            reactorFactory = PollReactor
        else:
            from twisted.internet.selectreactor import SelectReactor
            reactorFactory = SelectReactor
        self._logWritingReactor = reactorFactory()
        self._logWritingReactor._registerAsIOThread = False
        self._thread = threading.Thread(
            target=self._reader, name="CrochetLogWriter")
        self._thread.start()

    def _reader(self):
        """
        Runs in a thread, reads messages from a queue and writes them to
        the wrapped observer.
        """
        self._logWritingReactor.run(installSignalHandlers=False)

    def stop(self):
        """
        Stop the thread.
        """
        self._logWritingReactor.callFromThread(self._logWritingReactor.stop)

    def __call__(self, msg):
        """
        A log observer that writes to a queue.
        """

        def log():
            try:
                self._observer(msg)
            except Exception:
                # Lower-level logging system blew up, nothing we can do, so
                # just drop on the floor.
                pass

        self._logWritingReactor.callFromThread(log)


class EventLoop(object):
    """
    Initialization infrastructure for running a reactor in a thread.
    """

    def __init__(
        self,
        reactorFactory,
        atexit_register,
        startLoggingWithObserver=None,
        watchdog_thread=None,
        reapAllProcesses=None
    ):
        """
        reactorFactory: Zero-argument callable that returns a reactor.
        atexit_register: atexit.register, or look-alike.
        startLoggingWithObserver: Either None, or
            twisted.python.log.startLoggingWithObserver or lookalike.
        watchdog_thread: crochet._shutdown.Watchdog instance, or None.
        reapAllProcesses: twisted.internet.process.reapAllProcesses or
            lookalike.
        """
        self._reactorFactory = reactorFactory
        self._atexit_register = atexit_register
        self._startLoggingWithObserver = startLoggingWithObserver
        self._started = False
        self._lock = threading.Lock()
        self._watchdog_thread = watchdog_thread
        self._reapAllProcesses = reapAllProcesses

    def _startReapingProcesses(self):
        """
        Start a LoopingCall that calls reapAllProcesses.
        """
        lc = LoopingCall(self._reapAllProcesses)
        lc.clock = self._reactor
        lc.start(0.1, False)

    def _common_setup(self):
        """
        The minimal amount of setup done by both setup() and no_setup().
        """
        self._started = True
        self._reactor = self._reactorFactory()
        self._registry = ResultRegistry()
        # We want to unblock EventualResult regardless of how the reactor is
        # run, so we always register this:
        self._reactor.addSystemEventTrigger(
            "before", "shutdown", self._registry.stop)

    @synchronized
    def setup(self):
        """
        Initialize the crochet library.

        This starts the reactor in a thread, and connect's Twisted's logs to
        Python's standard library logging module.

        This must be called at least once before the library can be used, and
        can be called multiple times.
        """
        if self._started:
            return
        self._common_setup()
        if platform.type == "posix":
            self._reactor.callFromThread(self._startReapingProcesses)
        if self._startLoggingWithObserver:
            observer = ThreadLogObserver(PythonLoggingObserver().emit)

            def start():
                # Twisted is going to override warnings.showwarning; let's
                # make sure that has no effect:
                from twisted.python import log
                original = log.showwarning
                log.showwarning = warnings.showwarning
                self._startLoggingWithObserver(observer, False)
                log.showwarning = original

            self._reactor.callFromThread(start)

            # We only want to stop the logging thread once the reactor has
            # shut down:
            self._reactor.addSystemEventTrigger(
                "after", "shutdown", observer.stop)
        t = threading.Thread(
            target=lambda: self._reactor.run(installSignalHandlers=False),
            name="CrochetReactor")
        t.start()
        self._atexit_register(self._reactor.callFromThread, self._reactor.stop)
        self._atexit_register(_store.log_errors)
        if self._watchdog_thread is not None:
            self._watchdog_thread.start()

    @synchronized
    def no_setup(self):
        """
        Initialize the crochet library with no side effects.

        No reactor will be started, logging is uneffected, etc.. Future calls
        to setup() will have no effect. This is useful for applications that
        intend to run Twisted's reactor themselves, and so do not want
        libraries using crochet to attempt to start it on their own.

        If no_setup() is called after setup(), a RuntimeError is raised.
        """
        if self._started:
            raise RuntimeError(
                "no_setup() is intended to be called once, by a"
                " Twisted application, before any libraries "
                "using crochet are imported and call setup().")
        self._common_setup()

    def run_in_reactor(self, function):
        """
        A decorator that ensures the wrapped function runs in the
        reactor thread.

        When the wrapped function is called, an EventualResult is returned.
        """
        def _run_in_reactor(wrapped, _, args, kwargs):
            """
            Implementation: A decorator that ensures the wrapped function runs in
            the reactor thread.

            When the wrapped function is called, an EventualResult is returned.
            """

            if iscoroutinefunction(wrapped):
                def runs_in_reactor(result, args, kwargs):
                    d = ensureDeferred(wrapped(*args, **kwargs))
                    result._connect_deferred(d)
            else:
                def runs_in_reactor(result, args, kwargs):
                    d = maybeDeferred(wrapped, *args, **kwargs)
                    result._connect_deferred(d)

            result = EventualResult(None, self._reactor)
            self._registry.register(result)
            self._reactor.callFromThread(runs_in_reactor, result, args, kwargs)
            return result

        if iscoroutinefunction(function):
            # Create a non-async wrapper with same signature.
            @wraps(function)
            def non_async_wrapper():
                pass
        else:
            # Just use default behavior of looking at underlying object.
            non_async_wrapper = None

        return wrapt.decorator(_run_in_reactor, adapter=non_async_wrapper)(function)

    def wait_for(self, timeout):
        """
        A decorator factory that ensures the wrapped function runs in the
        reactor thread.

        When the wrapped function is called, its result is returned or its
        exception raised. Deferreds are handled transparently. Calls will
        timeout after the given number of seconds (a float), raising a
        crochet.TimeoutError, and cancelling the Deferred being waited on.
        """

        def decorator(function):
            def wrapper(function, _, args, kwargs):
                @self.run_in_reactor
                def run():
                    if iscoroutinefunction(function):
                        return ensureDeferred(function(*args, **kwargs))
                    else:
                        return function(*args, **kwargs)

                eventual_result = run()
                try:
                    return eventual_result.wait(timeout)
                except TimeoutError:
                    eventual_result.cancel()
                    raise

            if iscoroutinefunction(function):
                # Create a non-async wrapper with same signature.
                @wraps(function)
                def non_async_wrapper():
                    pass
            else:
                # Just use default behavior of looking at underlying object.
                non_async_wrapper = None

            wrapper = wrapt.decorator(wrapper, adapter=non_async_wrapper)
            return wrapper(function)

        return decorator
