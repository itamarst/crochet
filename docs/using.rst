Using Crochet
-------------

Hide Twisted and Crochet
^^^^^^^^^^^^^^^^^^^^^^^^

Consider some synchronous do-one-thing-after-the-other application code that
wants to use event-driven Twisted-using code. We have two threads at a
minimum: the application thread(s) and the reactor thread. There are also
multiple layers of code involved in this interaction:

* **Twisted code:** Should only be called in reactor thread. This may be code
  from the Twisted package itself, or more likely code you have written that
  is built on top of Twisted.
* **@wait_for/@run_in_reactor wrappers:** The body of the functions
  runs in the reactor thread... but the caller should be in the application
  thread.
* **The application code:** Runs in the application thread(s), expects
  synchronous/blocking calls.

Sometimes the first two layers suffice, but there are some issues with only
having these. First, if you're using ``@run_in_reactor`` it requires the
application code to understand Crochet's API, i.e. ``EventualResult``
objects. Second, if the wrapped function returns an object that expects to
interact with Twisted, the application code will not be able to use that
object since it will be called in the wrong thread.

A better solution is to have an additional layer in-between the application
code and ``@wait_for/@run_in_reactor`` wrappers. This layer can hide
the details of the Crochet API and wrap returned Twisted objects if
necessary. As a result the application code simply seems a normal API, with no
need to understand ``EventualResult`` objects or Twisted.

In the following example the different layers of the code demonstrate this
separation: ``_ExchangeRate`` is just Twisted code, and ``ExchangeRate``
provides a blocking wrapper using Crochet.

.. literalinclude:: ../examples/scheduling.py


Minimize Decorated Code
^^^^^^^^^^^^^^^^^^^^^^^

It's best to have as little code as possible in the
``@wait_for/@run_in_reactor`` wrappers. As this code straddles two
worlds (or at least, two threads) it is more difficult to unit test. Having an
extra layer between this code and the application code is also useful in this
regard as well: Twisted code can be pushed into the lower-level Twisted layer,
and code hiding the Twisted details from the application code can be pushed
into the higher-level layer.


Preventing Deadlocks on Shutdown
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To ensure a timely process exit, during reactor shutdown Crochet will try to
interrupt calls to ``EventualResult.wait()`` or functions decorated with
``@wait_for`` with a ``crochet.ReactorStopped`` exception. This is still not a
complete solution, unfortunately. If you are shutting down a thread pool as
part of Twisted's reactor shutdown, this will wait until all threads are
done. If you're blocking indefinitely, this may rely on Crochet interrupting
those blocking calls... but Crochet's shutdown may be delayed until the thread
pool finishes shutting down, depending on the ordering of shutdown events.

The solution is to interrupt all blocking calls yourself. You can do this by
firing or canceling any ``Deferred`` instances you are waiting on as part of
your application shutdown, and do so before you stop any thread pools.
