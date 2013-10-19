#!/usr/bin/python
"""
An example of using Crochet from a normal Twisted application.
"""

import time
import threading
import sys

from crochet import no_setup, run_in_reactor, wait_for_reactor, TimeoutError
# Tell Crochet not to run the reactor:
no_setup()

from twisted.internet import reactor
from twisted.web.client import getPage


# Blocking API:
@run_in_reactor
def _download_page(url):
    return getPage(url)

def time_page_download(url):
    start = time.time()
    _download_page(url).wait(1)
    return time.time() - start


def main(url):
    def blockingCode():
        print "Downloading", url
        while True:
            try:
                elapsed = time_page_download(url)
            except TimeoutError:
                print "Timeout!"
            else:
                print "Download took", elapsed, "seconds"
    threading.Thread(target=blockingCode).start()
    # Run the reactor as you usually would:
    reactor.run()


if __name__ == '__main__':
    main(sys.argv[1])
