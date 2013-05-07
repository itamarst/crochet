Crochet: Asynchronous Calls from Threaded Applications
======================================================

Crochet is an MIT-licensed library that makes it easier to use Twisted as a
library in threaded applications. Instead of having Twisted running in the
main thread, or running the reactor in a thread yourself, you can use Twisted
or Twisted-based libraries like any other library in Flask, Django or blocking
applications.

.. image:: https://travis-ci.org/itamarst/crochet.png?branch=master
           :target: http://travis-ci.org/itamarst/crochet
           :alt: Build Status


Bugs and feature requests should be filed at the project `Github page`_.

Quick Example
-------------

Here's an example of a program using Crochet:

.. code-block:: python

  import sys

  from twisted.web.client import getPage
  from crochet import setup, run_in_reactor
  crochet.setup()

  @run_in_reactor
  def download_page(url):
      return getPage(url)

  result = download_page(sys.argv[1])
  # wait() returns the result when it becomes available:
  print result.wait()

Run on the command line::

  $ python example.py http://google.com
  <!doctype html><html itemscope="itemscope" ... etc. ...

Notice that you get a completely blocking interface to Twisted, and do not
need to run the Twisted reactor, the event loop, yourself.

More examples are available in the ``examples/`` folder, or online on the
project `Github page`_.

.. _Github page: https://github.com/itamarst/crochet/

News
----

**Next release**

* Deprecated ``@in_reactor``, replaced with ``@run_in_reactor`` which doesn't
  change the arguments to the wrapped function.
* Added more examples.
* ``setup.py sdist`` should work now.

**0.5**

* Initial release.


Features
--------

* Runs Twisted's reactor in a thread it manages.
* Hooks up Twisted's log system to the Python standard library ``logging``
  framework. Unlike Twisted's built-in ``logging`` bridge, this includes
  support for blocking `Handler` instances.
* Provides a blocking API to eventual results (i.e. ``Deferred`` instances).


Using Crochet in Blocking Code
------------------------------

Using Crochet involves three parts: setup, setting up functions that call into
Twisted's reactor, and using those functions.


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

Creating Asynchronous Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that you've got the reactor running, the next stage is defining some
functions that will run inside the Twisted reactor thread. Twisted's APIs are
not thread-safe, and so they cannot be called directly from another
thread. Instead, we write a function that is decorated with
``crochet.run_in_reactor``:

.. code-block:: python

  from twisted.internet import reactor
  from crochet import run_in_reactor

  @run_in_reactor
  def call_later(delay, f, *args, **kwargs):
      reactor.callLater(delay, f, *args, **kwargs)

  call_later(30, sys.stdout.write, "30 seconds have passed.\n")

Some points to notice:

* The code will not run in the calling thread, but rather in the reactor
  thread.
* The return result from a decorated object is a ``DeferredResult``, which
  will be discussed in the next section.

Asynchronous Results
^^^^^^^^^^^^^^^^^^^^

Since the code in the decorated function will be run in a separate thread, it
cannot be returned normally. Moreover, the code may return a ``Deferred``,
which means the result may not be available until that ``Deferred`` fires. To
deal with that, functions decorated with ``crochet.run_in_reactor`` return a
``crochet.DeferredResult`` instance.

``DeferredResult`` has the following methods:

* ``wait(timeout=None)``: Return the result when it becomes available; if the
  result is an exception it will be raised. If an optional timeout is given
  (in seconds), ``wait()`` will throw ``crochet.TimeoutError`` if the timeout
  is hit, rather than blocking indefinitely.
* ``cancel()``: Cancel the operation tied to the underlying
  ``Deferred``. Many, but not all, ``Deferred`` results returned from Twisted
  allow the underlying operation to be canceled. In any case this should be
  considered a best effort cancellation.
* ``stash()``: Sometimes you want to store the ``DeferredResult`` in memory
  for later retrieval. ``stash()`` stores the ``DeferredResult`` in memory,
  and returns an integer uid that can be used to retrieve the result using
  ``crochet.retrieve_result(uid)``. This is specifically useful when you want
  to store a reference to the ``DeferredResult`` in a web session like
  Flask's. See the included ``examples/downloader.py`` for an example of using
  this API.


Using Crochet from Twisted Applications
---------------------------------------

If your application is already planning on running the Twisted reactor itself,
Crochet's default behavior of running the reactor in a thread is a problem. To
solve this, Crochet provides the ``no_setup()`` function, which causes future
calls to ``setup()`` to do nothing. Thus, an application that will run the
Twisted reactor but also wants to use a Crochet-using library must run it
first:

.. code-block:: python

    from crochet import no_setup
    no_setup()
    # Only now do we import libraries that might run crochet.setup():
    import blockinglib

    # ... setup application ...

    from twisted.internet import reactor
    reactor.run()
