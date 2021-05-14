Use Twisted Anywhere!
=====================
.. raw:: html

  <div><a class="github-button" href="https://github.com/itamarst/crochet" data-icon="octicon-star" data-show-count="true" aria-label="Star itamarst/crochet on GitHub">Star</a>
  <script async defer src="https://buttons.github.io/buttons.js"></script></div>

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

You can also wrap ``async`` functions.
Here is the equivalent code to the previous example, but using an ``async/await`` function:

.. code-block:: python

   @wait_for(timeout=5.0)
   async def gethostbyname(name):
       result = await client.lookupAddress(name)
       return result[0][0].payload.dottedQuad()

Table of Contents
^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 3

   introduction
   api
   using
   type-checking
   workarounds
   async
   api-reference
   news
