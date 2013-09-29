#!/usr/bin/python
"""
Download a web page in a blocking manner.
"""

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
