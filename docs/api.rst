Using Crochet in Blocking Code
------------------------------

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


Using Crochet from Twisted Applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Decorating the function with ``run_in_reactor`` has two consequences:

* When the function is called, the code will not run in the calling thread,
  but rather in the reactor thread.
* The return result from a decorated function is an ``EventualResult``, which
  will be discussed in the next section.


Asynchronous Results
^^^^^^^^^^^^^^^^^^^^

Since the code in the decorated function will be run in a separate thread, its
return result or raised exception cannot be returned normally. Moreover, the
code may return a ``Deferred``, which means the result may not be available
until that ``Deferred`` fires. To deal with that, functions decorated with
``crochet.run_in_reactor`` return a ``crochet.EventualResult`` instance.

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

.. code-block:: python

    """
    A flask web application that downloads a page in the background.
    """

    import logging
    from flask import Flask, session, escape
    from crochet import setup, run_in_reactor, retrieve_result, TimeoutError

    # Can be called multiple times with no ill-effect:
    setup()

    app = Flask(__name__)


    @run_in_reactor
    def download_page(url):
        """
        Download a page.
        """
        from twisted.web.client import getPage
        return getPage(url)


    @app.route('/')
    def index():
        if 'download' not in session:
            # Calling an @run_in_reactor function returns an EventualResult:
            result = download_page('http://www.google.com')
            session['download'] = result.stash()
            return "Starting download, refresh to track progress."

        # retrieval is a one-time operation, so the uid in the session cannot be reused:
        result = retrieve_result(session.pop('download'))
        try:
            download = result.wait(timeout=0.1)
            return "Downloaded: " + escape(download)
        except TimeoutError:
            session['download'] = result.stash()
            return "Download in progress..."


    if __name__ == '__main__':
        import os, sys
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
        app.secret_key = os.urandom(24)
        app.run()
