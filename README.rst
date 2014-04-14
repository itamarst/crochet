Crochet: Use Twisted Anywhere!
==============================

Crochet is an MIT-licensed library that makes it easier to use Twisted from
regular blocking code. Some use cases include:

* Easily use Twisted from a blocking framework like Django or Flask.
* Write a library that provides a blocking API, but uses Twisted for its
  implementation.
* Port blocking code to Twisted more easily, by keeping a backwards
  compatibility layer.
* Allow normal Twisted programs that use threads to interact with Twisted more
  cleanly from their threaded parts. For example this can be useful when using
  Twisted as a `WSGI container`_.

.. _WSGI container: https://twistedmatrix.com/documents/current/web/howto/web-in-60/wsgi.html

Crochet is maintained by Itamar Turner-Trauring.

Downloads are available on `PyPI`_.

Documentation can be found on `Read The Docs`_.

Bugs and feature requests should be filed at the project `Github page`_.

.. _Read the Docs: https://crochet.readthedocs.org/
.. _Github page: https://github.com/itamarst/crochet/
.. _PyPI: https://pypi.python.org/pypi/crochet


Features
========

Crochet aims for 100% unit test coverage, and supports Python 2.6, 2.7 and 3.3.

.. image:: https://travis-ci.org/itamarst/crochet.png?branch=master
           :target: http://travis-ci.org/itamarst/crochet
           :alt: Build Status

Crochet provides the following general features:

* Allow blocking code to call into Twisted and block until results are available
  or a timeout is hit, using the ``crochet.wait_for`` decorator.
* A lower-level API (``crochet.run_in_reactor``) allows blocking code to run
  code "in the background" in the Twisted thread, with ability to repeatedly
  check if it's done.

Additionally Crochet can:

* Transparently start Twisted's reactor in a thread it manages.
* The reactor shuts down automatically when the process' main thread finishes.
* Hooks up Twisted's log system to the Python standard library ``logging``
  framework. Unlike Twisted's built-in ``logging`` bridge, this includes
  support for blocking `Handler` instances.
