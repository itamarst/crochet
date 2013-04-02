#!/usr/bin/python
"""
A flask web application that downloads a page in the background.
"""

import logging
from flask import Flask, session, escape
from crochet import setup, in_event_loop, resultstore, TimeoutError

# Can be called multiple times with no ill-effect:
setup()

app = Flask(__name__)


@in_event_loop
def download_page(reactor, url):
    """
    Download a page.
    """
    from twisted.web.client import getPage
    return getPage(url)


@app.route('/')
def index():
    url = 'http://www.google.com'
    if 'download' not in session:
        # No download, start it in background:
        result = download_page(url)
        uid = resultstore.store(result)
        session['download'] = uid
        return "Starting download, refresh to track progress."

    result = resultstore.retrieve(session['download'])
    try:
        download = result.result(0)
        del session['download']
        return "Downloaded: " + escape(download)
    except TimeoutError:
        session['download'] = resultstore.store(result)
        return "Download in progress..."


if __name__ == '__main__':
    import os, sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    app.secret_key = os.urandom(24)
    app.run()
