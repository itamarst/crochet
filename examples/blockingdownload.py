#!/usr/bin/python
"""
Download a web page in a blocking manner.
"""

from __future__ import print_function

import sys

from twisted.web.client import getPage
from crochet import setup, wait_for_reactor
setup()

@wait_for_reactor
def download_page(url):
    return getPage(url)

# download_page() now behaves like a normal blocking function:
print(download_page(sys.argv[1]))
