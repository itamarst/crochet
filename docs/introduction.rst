Introduction
------------

What It Does
^^^^^^^^^^^^
Crochet provides the following features:

* Runs Twisted's reactor in a thread it manages.
* The reactor shuts down automatically when the process' main thread finishes.
* Hooks up Twisted's log system to the Python standard library ``logging``
  framework. Unlike Twisted's built-in ``logging`` bridge, this includes
  support for blocking `Handler` instances.
* Provides a blocking API to eventual results (i.e. ``Deferred``
  instances). This last feature can be used separately, so Crochet is also
  useful for normal Twisted applications that use threads.

Why should you care about using Twisted? Because it gives you the full power
of an event-driven networking framework from inside your applications.


Some Use Cases
^^^^^^^^^^^^^^

Writing an application in a blocking framework, but want to use Twisted for
some part of your application? Crochet lets you run the reactor transparently
and call into Twisted in a blocking manner.

If you're writing a web application you can probably use Twisted as a `WSGI
container`_, in which case Crochet's reactor-running functionality isn't
necessary. Crochet's APIs for calling Twisted from threads would still be
useful. And of course if you don't want to use Twisted as your WSGI container
then you'd want to use Crochet's full functionality.

Perhaps you're writing a library that provides a blocking API, but want to use
Twisted for the implementation. Running the reactor in a thread yourself is
difficult... and since you can only run the reactor once this would prevent
using your library in applications that already use Twisted. Crochet provides
a solution for the latter issue using the ``no_setup()`` API.

If you're writing a Twisted application that involves non-trivial threading
interactions, and Twisted's built-in APIs (``deferToThread`` and
``blockCallFromThread``) are therefore insufficient, Crochet's API for calling
into Twisted from threads will come in handy.

.. _WSGI container: https://twistedmatrix.com/documents/current/web/howto/web-in-60/wsgi.html


Example: Background Scheduling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can use Crochet to schedule events that will run in the background
without slowing down the page rendering of your web applications:

.. literalinclude:: ../examples/scheduling.py


Example: SSH into your Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can SSH into your Python process and get a Python prompt, allowing you to
poke around in the internals of your running program:

.. literalinclude:: ../examples/ssh.py


Example: DNS Query
^^^^^^^^^^^^^^^^^^
Twisted also has a fully featured DNS library:

.. literalinclude:: ../examples/mxquery.py


Example: Using Crochet in Normal Twisted Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can use Crochet's APIs for calling into the reactor thread from normal
Twisted applications:

.. literalinclude:: ../examples/fromtwisted.py
