Crochet
=======

Crochet is an MIT-licensed library that converts Twisted from a framework into a
library. Instead of having Twisted take over your application, you can use
Twisted or Twisted-based libraries like any other library in your Flask,
Django or any other blocking or threaded application.


Quick Example
-------------

Here's an example of a program using Crochet::

  import sys

  from twisted.web.client import getPage
  from crochet import setup, in_event_loop
  crochet.setup()

  @in_event_loop
  def download_page(reactor, url):
      return getPage(url)

  print download_page(sys.argv[1]).wait()

Run on the command line::

  $ python example.py http://google.com
  <!doctype html><html itemscope="itemscope" ... etc. ...

Notice that you get a completely blocking interface to Twisted, and do not
need to run the event loop yourself.


Using Crochet in Blocking Code
------------------------------

Using Crochet involves three parts: setup, setting up functions that call into
Twisted's event loop, and using those functions.


Setup
^^^^^

Creating Event Loop Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Calling Event Loop Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Using Crochet from Twisted Applications
---------------------------------------

If your application is already planning on running the Twisted reactor itself,
Crochet's default behavior of running the reactor in a thread is a problem. To
solve this, Crochet provides the ``no_setup()`` function, which causes future
calls to ``setup()`` to do nothing. Thus, an application that will run the Twisted reactor but also wants to use a Crochet-using library must run it first::

    from crochet import no_setup()
    no_setup()
    # Only now do we import libraries that might run crochet.setup():
    import blockinglib

    # ... setup application ...

    from twisted.internet import reactor
    reactor.run()
