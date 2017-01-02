What's New
==========

1.6.0
^^^^^

New features:

* Added support for Python 3.6.

1.5.0
^^^^^

New features:

* Added support for Python 3.5.

Removed features:

* Python 2.6, Python 3.3, and versions of Twisted < 15.0 are no longer supported.

1.4.0
^^^^^

New features:

* Added support for Python 3.4.

Documentation:

* Added a section on known issues and workarounds.

Bug fixes:

* Main thread detection (used to determine when Crochet should shutdown) is now less fragile.
  This means Crochet now supports more environments, e.g. uWSGI.
  Thanks to Ben Picolo for the patch.

1.3.0
^^^^^

Bug fixes:

* It is now possible to call ``EventualResult.wait()`` (or functions
  wrapped in ``wait_for``) at import time if another thread holds the
  import lock. Thanks to Ken Struys for the patch.

1.2.0
^^^^^
New features:

* ``crochet.wait_for`` implements the timeout/cancellation pattern documented
  in previous versions of Crochet. ``crochet.wait_for_reactor`` and
  ``EventualResult.wait(timeout=None)`` are now deprecated, since lacking
  timeouts they could potentially block forever.
* Functions wrapped with ``wait_for`` and ``run_in_reactor`` can now be accessed
  via the ``wrapped_function`` attribute, to ease unit testing of the underlying
  Twisted code.

API changes:

* It is no longer possible to call ``EventualResult.wait()`` (or functions
  wrapped with ``wait_for``) at import time, since this can lead to deadlocks
  or prevent other threads from importing. Thanks to Tom Prince for the bug
  report.

Bug fixes:

* ``warnings`` are no longer erroneously turned into Twisted log messages.
* The reactor is now only imported when ``crochet.setup()`` or
  ``crochet.no_setup()`` are called, allowing daemonization if only ``crochet``
  is imported (http://tm.tl/7105). Thanks to Daniel Nephin for the bug report.

Documentation:

* Improved motivation, added contact info and news to the documentation.
* Better example of using Crochet from a normal Twisted application.

1.1.0
^^^^^
Bug fixes:

* ``EventualResult.wait()`` can now be used safely from multiple threads,
  thanks to Gavin Panella for reporting the bug.
* Fixed reentrancy deadlock in the logging code caused by
  http://bugs.python.org/issue14976, thanks to Rod Morehead for reporting the
  bug.
* Crochet now installs on Python 3.3 again, thanks to Ben Cordero.
* Crochet should now work on Windows, thanks to Konstantinos Koukopoulos.
* Crochet tests can now run without adding its absolute path to PYTHONPATH or
  installing it first.

Documentation:

* ``EventualResult.original_failure`` is now documented.

1.0.0
^^^^^
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

0.9.0
^^^^^
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

0.8.1
^^^^^
* ``EventualResult.wait()`` now raises error if called in the reactor thread,
  thanks to David Buchmann.
* Unittests are now included in the release tarball.
* Allow Ctrl-C to interrupt ``EventualResult.wait(timeout=None)``.

0.7.0
^^^^^
* Improved documentation.

0.6.0
^^^^^
* Renamed ``DeferredResult`` to ``EventualResult``, to reduce confusion with
  Twisted's ``Deferred`` class. The old name still works, but is deprecated.
* Deprecated ``@in_reactor``, replaced with ``@run_in_reactor`` which doesn't
  change the arguments to the wrapped function. The deprecated API still works,
  however.
* Unhandled exceptions in ``EventualResult`` objects are logged.
* Added more examples.
* ``setup.py sdist`` should work now.

0.5.0
^^^^^
* Initial release.
