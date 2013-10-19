Crochet: Use Twisted Anywhere!
==============================

Crochet is an MIT-licensed library that makes it easier for blocking or
threaded applications like Flask or Django to use the Twisted networking
framework. Crochet provides the following features:

* Runs Twisted's reactor in a thread it manages.
* The reactor shuts down automatically when the process' main thread finishes.
* Hooks up Twisted's log system to the Python standard library ``logging``
  framework. Unlike Twisted's built-in ``logging`` bridge, this includes
  support for blocking `Handler` instances.
* A blocking API to eventual results (i.e. ``Deferred`` instances). This last
  feature can be used separately, so Crochet is also useful for normal Twisted
  applications that use threads.

.. image:: https://travis-ci.org/itamarst/crochet.png?branch=master
           :target: http://travis-ci.org/itamarst/crochet
           :alt: Build Status


Documentation can be found on `Read The Docs`_.

Bugs and feature requests should be filed at the project `Github page`_.

.. _Read the Docs: https://crochet.readthedocs.org/
.. _Github page: https://github.com/itamarst/crochet/


Changelog
---------

**1.0.0**

Documentation:

* Added section on use cases and alternatives. Thanks to Tobias Oberstein for
  the suggestion.

Bug fixes:

* Twisted does not have to be pre-installed to run ``setup.py``, thanks to
  Paul Weaver for bug report and Chris Scutcher for patch.
* Importing Crochet does not have side-effects (installing reactor event)
  any more.
* Blocking calls are interrupted earlier in the shutdown process, to reduce
  scope for deadlocks. Thanks to rmorehead for bug report.

**0.9.0**

New features:

* Expanded and much improved documentation, including a new section with
  design suggestions.
* New decorator ``@wait_for_reactor`` added, a simpler alternative to
  ``@run_in_reactor``.
* Refactored ``@run_in_reactor``, making it a bit more responsive.
* Blocking operations which would otherwise never finish due to reactor having
  stopped (``EventualResult.wait()`` or ``@wait_for_reactor`` decorated call)
  will be interrupted with a ``ReactorStopped`` exception. Thanks to rmorehead
  for the bug report.

Bug fixes:

* ``@run_in_reactor`` decorated functions (or rather, their generated wrapper)
  are interrupted by Ctrl-C.
* On POSIX platforms, a workaround is installed to ensure processes started by
  `reactor.spawnProcess` have their exit noticed. See `Twisted ticket 6378`_
  for more details about the underlying issue.

.. _Twisted ticket 6378: http://tm.tl/6738

**0.8.1**

* ``EventualResult.wait()`` now raises error if called in the reactor thread,
  thanks to David Buchmann.
* Unittests are now included in the release tarball.
* Allow Ctrl-C to interrupt ``EventualResult.wait(timeout=None)``.

**0.7.0**

* Improved documentation.

**0.6.0**

* Renamed ``DeferredResult`` to ``EventualResult``, to reduce confusion with
  Twisted's ``Deferred`` class. The old name still works, but is deprecated.
* Deprecated ``@in_reactor``, replaced with ``@run_in_reactor`` which doesn't
  change the arguments to the wrapped function. The deprecated API still works,
  however.
* Unhandled exceptions in ``EventualResult`` objects are logged.
* Added more examples.
* ``setup.py sdist`` should work now.

**0.5.0**

* Initial release.
