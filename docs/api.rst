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


@wait_for_reactor: Blocking Calls into Twisted
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that you've got the reactor running, the next stage is defining some
functions that will run inside the Twisted reactor thread. Twisted's APIs are
not thread-safe, and so they cannot be called directly from another
thread. Moreover, results may not be available immediately. The easiest way to
deal with these issues is to decorate a function that calls Twisted APIs with
``crochet.wait_for_reactor``.

* When the decorated function is called, the code will not run in the calling
  thread, but rather in the reactor thread.
* The function blocks until a result is available from the code running in the
  Twisted thread. The returned result is the result of running the code; if
  the code throws an exception, an exception is thrown.
* If the underlying code returns a ``Deferred``, it is handled transparently;
  its results are extracted and passed to the caller.

To see what this means, let's return to the first example in the
documentation:

.. literalinclude:: ../examples/blockingdownload.py

Twisted's ``getPage()`` call returns a ``Deferred``, but the code calling the
decorated ``download_page()`` doesn't know that. As far as the caller
concerned is just calling a blocking function that returns a result or raises
an exception. Run on the command line with a valid URL we get::

  $ python blockingdownload.py http://google.com
  <!doctype html><html itemscope="itemscope" ... etc. ...

If we try to call the function with an invalid URL, we get back an exception::

  $ python blockingdownload.py http://notarealsite.atall
  Traceback (most recent call last):
    File "examples/blockingdownload.py", line 19, in <module>
      print(download_page(sys.argv[1]))
    File "/home/itamar/devel/python/crochet/crochet/_eventloop.py", line 300, in wrapper
      function, *args, **kwargs)
    File "/usr/lib/python2.7/dist-packages/twisted/internet/threads.py", line 118, in blockingCallFromThread
      result.raiseException()
    File "/usr/lib/python2.7/dist-packages/twisted/python/failure.py", line 370, in raiseException
      raise self.type, self.value, self.tb
  twisted.internet.error.DNSLookupError: DNS lookup failed: address 'notarealsite.atall' not found: [Errno -5] No address associated with hostname.

For comparison, here's what the Twisted version would look like; notice the
use of ``addCallback`` since ``getPage()`` returns a ``Deferred``:

.. code-block:: python

  #!/usr/bin/python
  """
  Download a web page in a non-blocking manner.
  """

  from __future__ import print_function

  import sys

  from twisted.web.client import getPage
  from twisted.internet.task import react

  def main(reactor, url):
      return getPage(url).addCallback(print)

  react(main, sys.argv[1:])


@run_in_reactor: Asynchronous Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``run_in_reactor`` is a more sophisticated alternative to
``wait_for_reactor``. Rather than waiting until a result is available, it
returns a special object supporting timeouts and cancellation. Decorating a
function that calls Twisted APIs with ``run_in_reactor`` has two consequences:

* When the function is called, the code will not run in the calling thread,
  but rather in the reactor thread.
* The return result from a decorated function is an ``EventualResult``
  instance, wrapping the result of the underlying code, with particular
  support for ``Deferred`` instances.

``EventualResult`` has the following methods:

* ``wait(timeout=None)``: Return the result when it becomes available; if the
  result is an exception it will be raised. If an optional timeout is given
  (in seconds), ``wait()`` will throw ``crochet.TimeoutError`` if the timeout
  is hit, rather than blocking indefinitely.
* ``cancel()``: Cancel the operation tied to the underlying
  ``Deferred``. Many, but not all, ``Deferred`` results returned from Twisted
  allow the underlying operation to be canceled. In any case this should be
  considered a best effort cancellation.
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


Reducing Twisted Log Messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Twisted can be rather verbose with its log messages. If you wish to reduce the
message flow you can limit them to error messages only:

.. code-block:: python

   import logging
   logging.getLogger('twisted').setLevel(logging.ERROR)
