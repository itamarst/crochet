Introduction
------------

.. include:: ../README.rst


Examples
========

Background Scheduling
^^^^^^^^^^^^^^^^^^^^^
You can use Crochet to schedule events that will run in the background
without slowing down the page rendering of your web applications:

.. literalinclude:: ../examples/scheduling.py


SSH into your Server
^^^^^^^^^^^^^^^^^^^^
You can SSH into your Python process and get a Python prompt, allowing you to
poke around in the internals of your running program:

.. literalinclude:: ../examples/ssh.py


DNS Query
^^^^^^^^^
Twisted also has a fully featured DNS library:

.. literalinclude:: ../examples/mxquery.py


Using Crochet in Normal Twisted Code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can use Crochet's APIs for calling into the reactor thread from normal
Twisted applications:

.. literalinclude:: ../examples/fromtwisted.py
