Using Crochet
-------------

Designing Your API
^^^^^^^^^^^^^^^^^^

Consider some synchronous do-one-thing-after-the-other application code that
wants to use event-driven Twisted-using code. We have two threads at a
minimum: the application thread(s) and the reactor thread. There are also
multiple layers of code involved in this interaction:

* **Twisted code:** Should only be called in reactor thread. This may be code
  from the Twisted package itself, or more likely code you have written that
  is built on top of Twisted.
* **@run_in_reactor wrapper:** The body of the functions runs in the
  reactor thread... but the caller should be in the application thread.
* **The application code:** Runs in the application thread, expects
  synchronous/blocking calls.

Sometimes the first two layers suffice, but there are some issues with only
having these. First, it requires the application code to understand Crochet's
API, i.e. ``EventualResult`` objects. Second, if the wrapped function returns
an object that expects to interact with Twisted, the application code will not
be able to use that object since it will be called in the wrong thread.

A better solution is to have an additional layer in-between the application
code and ``@run_in_reactor`` wrappers. This layer can hide the details of the
Crochet API and wrap returned Twisted objects if necessary. As a result the
application code simply seems a normal API, with no need to understand
``EventualResult`` objects or Twisted.

In addition, it's best to have as little code as possible in the
``@run_in_reactor`` wrappers. As this code straddles two worlds (or at least,
two threads) it is more difficult to unit test. Having an extra layer between
this code and the application code is also useful in this regard as well:
Twisted code can be pushed into the lower-level Twisted layer, and code hiding
the Twisted details from the application code can be pushed into the
higher-level layer.


Implementing Timeouts
^^^^^^^^^^^^^^^^^^^^^

To see how this might work, let's consider how one might use Twisted and
Crochet's features to expose timeouts to application code.

Twisted's ``Deferred`` objects can support cancellation: when
``Deferred.cancel()`` is called the underlying operation is canceled. The API
documentation for Twisted will tell you when this is the case, and you can add
support to your own ``Deferred``-creating code. ``EventualResult.cancel()``
exposes this functionality. ``EventualResult.wait()`` also has the ability to
time out if no result becomes available within the given amount of time. A
layer wrapping ``@run_in_reactor`` is an excellent place to combine the two.

Notice in the following example the different layers of the code.

.. literalinclude:: ../examples/timeouts.py
