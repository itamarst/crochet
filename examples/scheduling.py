#!/usr/bin/python
"""
An example of scheduling time-based events in the background.

Download the latest EUR/USD exchange rate from Yahoo every 30 seconds in the
background; the rendered Flask web page can use the latest value without
having to do the request itself.

Note this is example is for demonstration purposes only, and is not actually
used in the real world. You should not do this in a real application without
reading Yahoo's terms-of-service and following them.
"""

from __future__ import print_function

from flask import Flask

from twisted.internet.task import LoopingCall
from twisted.web.client import getPage
from twisted.python import log

from crochet import wait_for, run_in_reactor, setup
setup()


# Twisted code:
class _ExchangeRate(object):
    """Download an exchange rate from Yahoo Finance using Twisted."""

    def __init__(self, name):
        self._value = None
        self._name = name

    # External API:
    def latest_value(self):
        """Return the latest exchange rate value.

        May be None if no value is available.
        """
        return self._value

    def start(self):
        """Start the background process."""
        self._lc = LoopingCall(self._download)
        # Run immediately, and then every 30 seconds:
        self._lc.start(30, now=True)

    def _download(self):
        """Download the page."""
        print("Downloading!")
        def parse(result):
            print("Got %r back from Yahoo." % (result,))
            values = result.strip().split(",")
            self._value = float(values[1])
        d = getPage(
            "http://download.finance.yahoo.com/d/quotes.csv?e=.csv&f=c4l1&s=%s=X"
            % (self._name,))
        d.addCallback(parse)
        d.addErrback(log.err)
        return d


# Blocking wrapper:
class ExchangeRate(object):
    """Blocking API for downloading exchange rate."""

    def __init__(self, name):
        self._exchange = _ExchangeRate(name)

    @run_in_reactor
    def start(self):
        self._exchange.start()

    @wait_for(timeout=1)
    def latest_value(self):
        """Return the latest exchange rate value.

        May be None if no value is available.
        """
        return self._exchange.latest_value()


EURUSD = ExchangeRate("EURUSD")
app = Flask(__name__)

@app.route('/')
def index():
    rate = EURUSD.latest_value()
    if rate is None:
        rate = "unavailable, please refresh the page"
    return "Current EUR/USD exchange rate is %s." % (rate,)


if __name__ == '__main__':
    import sys, logging
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    EURUSD.start()
    app.run()
