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
