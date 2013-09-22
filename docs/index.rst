.. Crochet documentation master file, created by
   sphinx-quickstart on Mon Sep 16 19:37:18 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Crochet's documentation!
===================================

Crochet is an MIT-licensed library that makes it easier for blocking and
threaded applications like Flask or Django to use the Twisted networking
framework.

Here's an example of a program using Crochet:

.. code-block:: python

  import sys

  from twisted.web.client import getPage
  from crochet import setup, run_in_reactor
  setup()

  @run_in_reactor
  def download_page(url):
      return getPage(url)

  result = download_page(sys.argv[1])
  # wait() returns the result when it becomes available:
  print result.wait()

Run on the command line::

  $ python example.py http://google.com
  <!doctype html><html itemscope="itemscope" ... etc. ...

Notice that you get a completely blocking interface to Twisted, and do not
need to run the Twisted reactor, the event loop, yourself.


Table of Contents
^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 2

   introduction
   api

