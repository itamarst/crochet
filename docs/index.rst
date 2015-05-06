Use Twisted Anywhere!
=====================

Crochet is an MIT-licensed library that makes it easier for blocking and
threaded applications like Flask or Django to use the Twisted networking
framework.

Here's an example of a program using Crochet. Notice that you get a completely
blocking interface to Twisted and do not need to run the Twisted reactor, the
event loop, yourself.

.. literalinclude:: ../examples/blockingdns.py

Run on the command line::

  $ python blockingdns.py twistedmatrix.com
  twistedmatrix.com -> 66.35.39.66


Table of Contents
^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 3

   introduction
   api
   using
   workarounds
   news
