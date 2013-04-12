#!/usr/bin/python
"""
A demonstration of Conch, allowing you to SSH into a running Python server and
inspect objects at a Python prompt.
"""
import logging

from flask import Flask
from crochet import setup, in_reactor
setup()

# Web server:
app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to my boring web server!"


@in_reactor
def start_ssh_server(reactor, port, username, password, namespace):
    """
    Start an SSH server on the given port, exposing a Python prompt with the
    given namespace.
    """
    # This is a lot of boilerplate, see http://tm.tl/6429 for a ticket to
    # provide a utility function that simplifies this.
    from twisted.conch.insults import insults
    from twisted.conch import manhole, manhole_ssh
    from twisted.cred.checkers import (
        InMemoryUsernamePasswordDatabaseDontUse as MemoryDB)
    from twisted.cred.portal import Portal

    sshRealm = manhole_ssh.TerminalRealm()
    def chainedProtocolFactory():
        return insults.ServerProtocol(manhole.ColoredManhole, namespace)
    sshRealm.chainedProtocolFactory = chainedProtocolFactory

    sshPortal = Portal(sshRealm, [MemoryDB(**{username: password})])
    reactor.listenTCP(port, manhole_ssh.ConchFactory(sshPortal),
                      interface="127.0.0.1")


if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    start_ssh_server(5022, "admin", "secret", {"app": app}).wait()
    app.run()
