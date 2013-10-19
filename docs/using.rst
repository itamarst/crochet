Using Crochet
-------------

@wait_for_reactor vs. @run_in_reactor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``@wait_for_reactor`` is a much simpler API to use, but also suffers from this
simplicity. In particular, it will indefinitely for the result to be
available. If you're dealing with an in-memory structure this may be fine. Any
time you deal with an external system this can lead to infinite or at least
extremely long wait times. Your network connection may be down, you may be
hitting a firewall that swallows all packets, you might be talking to a
process that got suspended... relying on an external system to respond in a
timely manner is a bad idea.

This is where ``@run_in_reactor`` becomes useful. The ability to check if a
result has arrived yet means the action can run in the background, as we saw
with the background download example. Support for timeouts and cancellation
means you're never left waiting for an unbounded amount of time. But, that
does mean you're using ``EventualResult`` instances. Luckily, you can often
hide their existence from the calling code as we'll see in the next sections.


Hide Twisted and Crochet
^^^^^^^^^^^^^^^^^^^^^^^^

Consider some synchronous do-one-thing-after-the-other application code that
wants to use event-driven Twisted-using code. We have two threads at a
minimum: the application thread(s) and the reactor thread. There are also
multiple layers of code involved in this interaction:

* **Twisted code:** Should only be called in reactor thread. This may be code
  from the Twisted package itself, or more likely code you have written that
  is built on top of Twisted.
* **@wait_for_reactor/@run_in_reactor wrappers:** The body of the functions
  runs in the reactor thread... but the caller should be in the application
  thread.
* **The application code:** Runs in the application thread, expects
  synchronous/blocking calls.

Sometimes the first two layers suffice, but there are some issues with only
having these. First, if you're using ``@run_in_reactor`` it requires the
application code to understand Crochet's API, i.e. ``EventualResult``
objects. Second, if the wrapped function returns an object that expects to
interact with Twisted, the application code will not be able to use that
object since it will be called in the wrong thread.

A better solution is to have an additional layer in-between the application
code and ``@wait_for_reactor/@run_in_reactor`` wrappers. This layer can hide
the details of the Crochet API and wrap returned Twisted objects if
necessary. As a result the application code simply seems a normal API, with no
need to understand ``EventualResult`` objects or Twisted.


Implementing Timeouts
^^^^^^^^^^^^^^^^^^^^^

To see how this might work, let's consider for example how one might use
Twisted and Crochet's features to expose timeouts to application code.

Twisted's ``Deferred`` objects can support cancellation: when
``Deferred.cancel()`` is called the underlying operation is canceled. The API
documentation for Twisted will tell you when this is the case, and you can add
support to your own ``Deferred``-creating code. ``EventualResult.cancel()``
exposes this functionality. ``EventualResult.wait()`` also has the ability to
time out if no result becomes available within the given amount of time. A
layer wrapping ``@run_in_reactor`` is an excellent place to combine the two.

Notice in the following example the different layers of the code.

.. literalinclude:: ../examples/timeouts.py


Minimize Decorated Code
^^^^^^^^^^^^^^^^^^^^^^^

It's best to have as little code as possible in the
``@wait_for_reactor/@run_in_reactor`` wrappers. As this code straddles two
worlds (or at least, two threads) it is more difficult to unit test. Having an
extra layer between this code and the application code is also useful in this
regard as well: Twisted code can be pushed into the lower-level Twisted layer,
and code hiding the Twisted details from the application code can be pushed
into the higher-level layer.


Preventing Deadlocks on Shutdown
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In general, you should avoid using calls that block indefinitely,
i.e. ``@wait_for_reactor`` or ``EventualResult.wait()`` with no
timeout. Crochet will however try to interrupt these during reactor shutdown
with a ``crochet.ReactorStopped`` exception. This is still not a complete
solution, unfortunately. If you are shutting down a thread pool as part of
Twisted's reactor shutdown, this will wait until all threads are done. If
you're blocking indefinitely, this may rely on Crochet interrupting those
blocking calls... but Crochet's shutdown may be delayed until the thread pool
finishes shutting down, depending on the ordering of shutdown events.

The solution is to interrupt all blocking calls yourself. You can do this by
firing or canceling any ``Deferred`` instances you are waiting on as part of
your application shutdown, and do so before you stop any thread pools.
