Known Issues and Workarounds
----------------------------

Preventing Deadlocks on Shutdown
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To ensure a timely process exit, during reactor shutdown Crochet will try to
interrupt calls to ``EventualResult.wait()`` or functions decorated with
``@wait_for`` with a ``crochet.ReactorStopped`` exception. This is still not a
complete solution, unfortunately. If you are shutting down a thread pool as
part of Twisted's reactor shutdown, this will wait until all threads are
done. If you're blocking indefinitely, this may rely on Crochet interrupting
those blocking calls... but Crochet's shutdown may be delayed until the thread
pool finishes shutting down, depending on the ordering of shutdown events.

The solution is to interrupt all blocking calls yourself. You can do this by
firing or canceling any ``Deferred`` instances you are waiting on as part of
your application shutdown, and do so before you stop any thread pools.

Reducing Twisted Log Messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Twisted can be rather verbose with its log messages. If you wish to reduce the
message flow you can limit them to error messages only:

.. code-block:: python

   import logging
   logging.getLogger('twisted').setLevel(logging.ERROR)


Missing Tracebacks
^^^^^^^^^^^^^^^^^^

In order to prevent massive memory leaks, Twisted currently wipes out the traceback from exceptions it captures (see https://tm.tl/7873 for ideas on improving this).
This means that often exceptions re-raised by Crochet will be missing their tracebacks.
You can however get access to a string version of the traceback, suitable for logging, from ``EventualResult`` objects returned by ``@run_in_reactor``\-wrapped functions:

.. code-block:: python

    from crochet import run_in_reactor, TimeoutError
    
    @run_in_reactor
    def download_page(url):
        from twisted.web.client import getPage
        return getPage(url)

    result = download_page("https://github.com")
    try:
        page = result.wait(timeout=1000)
    except TimeoutError:
        # Handle timeout ...
    except:
        # Something else happened:
        print(result.original_failure().getTraceback())

uWSGI, multiprocessing, Celery
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

uWSGI, the standard library ``multiprocessing.py`` library and Celery by default use ``fork()`` without ``exec()`` to create child processes on Unix systems.
This means they effectively clone a running parent Python process, preserving all existing imported modules.
This is a fundamentally broken thing to do, e.g. it breaks the standard library's ``logging`` package.
It also breaks Crochet.

You have two options for dealing with this problem.
The ideal solution is to avoid this "feature":

uWSGI
  Use the ``--lazy-apps`` command-line option.

``multiprocessing.py``
  Use the ``spawn`` (or possibly ``forkserver``) start methods when using Python 3. See https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods for more details.

Alternatively, you can ensure you only start Crochet inside the child process:

uWSGI
  Only run ``crochet.setup()`` inside the WSGI application function.

``multiprocessing.py``
  Only run ``crochet.setup()`` in the child process.

Celery
  Only run ``crochet.setup()`` inside tasks.
