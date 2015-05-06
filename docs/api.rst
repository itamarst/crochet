The API
-------

Using Crochet involves three parts: reactor setup, defining functions that
call into Twisted's reactor, and using those functions.


Setup
^^^^^

Crochet does a number of things for you as part of setup. Most significantly,
it runs Twisted's reactor in a thread it manages. Doing setup is easy, just
call the ``setup()`` function:

.. code-block:: python

  from crochet import setup
  setup()

Since Crochet is intended to be used as a library, multiple calls work just
fine; if more than one library does ``crochet.setup()`` only the first one
will do anything.


@wait_for: Blocking Calls into Twisted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that you've got the reactor running, the next stage is defining some
functions that will run inside the Twisted reactor thread. Twisted's APIs are
not thread-safe, and so they cannot be called directly from another
thread. Moreover, results may not be available immediately. The easiest way to
deal with these issues is to decorate a function that calls Twisted APIs with
``crochet.wait_for``.

* When the decorated function is called, the code will not run in the calling
  thread, but rather in the reactor thread.
* The function blocks until a result is available from the code running in the
  Twisted thread. The returned result is the result of running the code; if
  the code throws an exception, an exception is thrown.
* If the underlying code returns a ``Deferred``, it is handled transparently;
  its results are extracted and passed to the caller.
* ``crochet.wait_for`` takes a ``timeout`` argument, a ``float`` indicating
  the number of seconds to wait until a result is available. If the given
  number of seconds pass and the underlying operation is still unfinished a
  ``crochet.TimeoutError`` exception is raised, and the wrapped ``Deferred``
  is canceled. If the underlying API supports cancellation this might free up
  any unused resources, close outgoing connections etc., but cancellation is
  not guaranteed and should not be relied on.

.. note ::
   ``wait_for`` was added to Crochet in v1.2.0. Prior releases provided a
   similar API called ``wait_for_reactor`` which did not provide
   timeouts. This older API still exists but is deprecated since waiting
   indefinitely is a bad idea.

To see what this means, let's return to the first example in the
documentation:

.. literalinclude:: ../examples/blockingdns.py

Twisted's ``lookupAddress()`` call returns a ``Deferred``, but the code calling the
decorated ``gethostbyname()`` doesn't know that. As far as the caller
concerned is just calling a blocking function that returns a result or raises
an exception. Run on the command line with a valid domain we get::

  $ python blockingdns.py twistedmatrix.com
  twistedmatrix.com -> 66.35.39.66

If we try to call the function with an invalid domain, we get back an exception::

  $ python blockingdns.py doesnotexist
  Trace back (most recent call last):
    File "examples/blockingdns.py", line 33, in <module>
      ip = gethostbyname(name)
    File "/home/itamar/crochet/crochet/_eventloop.py", line 434, in wrapper
      return eventual_result.wait(timeout)
    File "/home/itamar/crochet/crochet/_eventloop.py", line 216, in wait
      result.raiseException()
    File "<string>", line 2, in raiseException
  twisted.names.error.DNSNameError: <Message id=36791 rCode=3 maxSize=0 flags=answer,recDes,recAv queries=[Query('doesnotexist', 1, 1)] authority=[<RR name= type=SOA class=IN ttl=1694s auth=False>]>


@run_in_reactor: Asynchronous Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``wait_for`` is implemented using ``run_in_reactor``, a more sophisticated and
lower-level API. Rather than waiting until a result is available, it returns a
special object supporting multiple attempts to retrieve results, as well as
manual cancellation. This can be useful for running tasks "in the background",
i.e. asynchronously, as opposed to blocking and waiting for them to finish.

Decorating a function that calls Twisted APIs with ``run_in_reactor`` has two
consequences:

* When the function is called, the code will not run in the calling thread,
  but rather in the reactor thread.
* The return result from a decorated function is an ``EventualResult``
  instance, wrapping the result of the underlying code, with particular
  support for ``Deferred`` instances.

``EventualResult`` has the following basic methods:

* ``wait(timeout)``: Return the result when it becomes available; if the
  result is an exception it will be raised. The timeout argument is a
  ``float`` indicating a number of seconds; ``wait()`` will throw
  ``crochet.TimeoutError`` if the timeout is hit.
* ``cancel()``: Cancel the operation tied to the underlying
  ``Deferred``. Many, but not all, ``Deferred`` results returned from Twisted
  allow the underlying operation to be canceled. Even if implemented,
  cancellation may not be possible for a variety of reasons, e.g. it may be
  too late. Its main purpose to free up no longer used resources, and it
  should not be relied on otherwise.

There are also some more specialized methods:

* ``original_failure()`` returns the underlying Twisted `Failure`_ object if
  your result was a raised exception, allowing you to print the original
  traceback that caused the exception. This is necessary because the default
  exception you will see raised from ``EventualResult.wait()`` won't include
  the stack from the underlying Twisted code where the exception originated.
* ``stash()``: Sometimes you want to store the ``EventualResult`` in memory
  for later retrieval. This is specifically useful when you want to store a
  reference to the ``EventualResult`` in a web session like Flask's (see the
  example below). ``stash()`` stores the ``EventualResult`` in memory, and
  returns an integer uid that can be used to retrieve the result using
  ``crochet.retrieve_result(uid)``. Note that retrieval works only once per
  uid. You will need the stash the ``EventualResult`` again (with a new
  resulting uid) if you want to retrieve it again later.

In the following example, you can see all of these APIs in use. For each user
session, a download is started in the background. Subsequent page refreshes
will eventually show the downloaded page.

.. literalinclude:: ../examples/downloader.py

.. _Failure: https://twistedmatrix.com/documents/current/api/twisted.python.failure.Failure.html

Using Crochet from Twisted Applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your application is already planning on running the Twisted reactor itself
(e.g. you're using Twisted as a WSGI container), Crochet's default behavior of
running the reactor in a thread is a problem. To solve this, Crochet provides
the ``no_setup()`` function, which causes future calls to ``setup()`` to do
nothing. Thus, an application that will run the Twisted reactor but also wants
to use a Crochet-using library must run it first:

.. code-block:: python

    from crochet import no_setup
    no_setup()
    # Only now do we import libraries that might run crochet.setup():
    import blockinglib

    # ... setup application ...

    from twisted.internet import reactor
    reactor.run()


Unit Testing
^^^^^^^^^^^^

Both ``@wait_for`` and ``@run_in_reactor`` expose the underlying Twisted
function via a ``wrapped_function`` attribute. This allows unit testing of the
Twisted code without having to go through the Crochet layer.

.. literalinclude:: ../examples/testing.py

When run, this gives the following output::

    add() returns EventualResult:
         <crochet._eventloop.EventualResult object at 0x2e8b390>
    add.wrapped_function() returns result of underlying function:
         3
