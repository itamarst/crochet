Introduction
------------

Features
^^^^^^^^
Crochet provides the following features:

* Runs Twisted's reactor in a thread it manages.
* Hooks up Twisted's log system to the Python standard library ``logging``
  framework. Unlike Twisted's built-in ``logging`` bridge, this includes
  support for blocking `Handler` instances.
* Provides a blocking API to eventual results (i.e. ``Deferred`` instances).

Why should you care about using Twisted? Because it gives you the full power
of an event-driven networking framework from inside your applications.


Example: Background Scheduling
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can use Crochet to schedule events that will run in the background
without slowing down the page rendering of your web applications:

.. literalinclude:: ../examples/scheduling.py


Example: SSH into your Server:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can SSH into your Python process and get a Python prompt, allowing you to
poke around in the internals of your running program:

.. literalinclude:: ../examples/ssh.py


Example: DNS Query
^^^^^^^^^^^^^^^^^^
Twisted also has a fully featured DNS library:

.. literalinclude:: ../examples/mxquery.py
