#!/usr/bin/python
"""
A flask web application that downloads a page in the background.
"""

import logging
from flask import Flask, session, escape
from crochet import setup, in_event_loop, retrieve_result, TimeoutError

# Can be called multiple times with no ill-effect:
setup()

app = Flask(__name__)


@in_event_loop
def download_page(reactor, url):
    """
    Download a page, after a 10 second delay for demonstration purposes.
    """
    from twisted.web.client import getPage
    from twisted.internet.task import deferLater
    return deferLater(reactor, 10, getPage, url)


@app.route('/')
def index():
    if 'download' not in session:
        # No download, start it in background:
        session['download'] = download_page('http://www.google.com').stash()
        return "Starting download, refresh to track progress."

    # retrieval is a one-time operation, so session value cannot be reused:
    result = retrieve_result(session.pop('download'))
    try:
        download = result.result(timeout=0.0)
        return "Downloaded: " + escape(download)
    except TimeoutError:
        session['download'] = result.stash()
        return "Download in progress..."


if __name__ == '__main__':
    import os, sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    app.secret_key = os.urandom(24)
    app.run()
