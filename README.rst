Crochet: Asynchronous Calls from Threaded Applications
======================================================

Crochet is an MIT-licensed library that makes it easier for threaded
applications like Flask or Django to use the Twisted networking framework, by
providing:

* An API to help threads interact with Twisted APIs, which are not thread-safe
  by default.
* The ability to easily run the Twisted reactor in the background.

.. image:: https://travis-ci.org/itamarst/crochet.png?branch=master
           :target: http://travis-ci.org/itamarst/crochet
           :alt: Build Status


Documentation can be found at XXX add readthedocs link XXX

Bugs and feature requests should be filed at the project `Github page`_.

.. _Github page: https://github.com/itamarst/crochet/


Changelog
---------

**Next release**

* On POSIX platforms, a workaround is installed to ensure processes started by
  `reactor.spawnProcess` have their exit noticed. See `Twisted ticket 6378`_
  for more details about the underlying issue.

.. _Twisted ticket 6378: http://tm.tl/6738

**0.8.1**

* EventualResult.wait() now raises error if called in the reactor thread.
* Unittests are now included in the release tarball.
* Allow Ctrl-C to interrupt `EventualResult.wait(timeout=None)`.

**0.7.0**

* Improved documentation.

**0.6.0 (unreleased)**

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
