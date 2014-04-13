#!/usr/bin/python
"""
An example of using Crochet from a normal Twisted application.
"""

import sys

from crochet import no_setup, wait_for
# Tell Crochet not to run the reactor:
no_setup()

from twisted.internet import reactor
from twisted.python import log
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site
from twisted.names import client

# A WSGI application, will be run in thread pool:
def application(environ, start_response):
    start_response('200 OK', [])
    try:
        ip = gethostbyname('twistedmatrix.com')
        return "%s has IP %s" % ('twistedmatrix.com', ip)
    except Exception, e:
        return 'Error doing lookup: %s' % (e,)

# A blocking API that will be called from the WSGI application, but actually
# uses DNS:
@wait_for(timeout=10)
def gethostbyname(name):
    d = client.lookupAddress(name)
    d.addCallback(lambda result: result[0][0].payload.dottedQuad())
    return d

# Normal Twisted code, serving the WSGI application and running the reactor:
def main():
    log.startLogging(sys.stdout)
    pool = reactor.getThreadPool()
    reactor.listenTCP(5000, Site(WSGIResource(reactor, pool, application)))
    reactor.run()

if __name__ == '__main__':
    main()
