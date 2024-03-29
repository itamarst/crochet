#!/usr/bin/python
"""
Async/await DNS lookup using Twisted's APIs.
"""
from __future__ import print_function

# The Twisted code we'll be using:
from twisted.names import client

from crochet import setup, wait_for
setup()


# Crochet layer, wrapping Twisted's DNS library in a blocking call.
# Uses async/await.
@wait_for(timeout=5.0)
async def gethostbyname(name):
    """Lookup the IP of a given hostname.

    Unlike socket.gethostbyname() which can take an arbitrary amount of time
    to finish, this function will raise crochet.TimeoutError if more than 5
    seconds elapse without an answer being received.
    """
    result = await client.lookupAddress(name)
    return result[0][0].payload.dottedQuad()


if __name__ == '__main__':
    # Application code using the public API - notice it works in a normal
    # blocking manner, with no event loop visible:
    import sys
    name = sys.argv[1]
    ip = gethostbyname(name)
    print(name, "->", ip)
