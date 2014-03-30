#!/usr/bin/python
"""
A demonstration of Conch, allowing you to SSH into a running Python server and
inspect objects at a Python prompt.

If you're using the system install of Twisted, you may need to install Conch
separately, e.g. on Ubuntu:

   $ sudo apt-get install python-twisted-conch

Once you've started the program, you can ssh in by doing:

    $ ssh admin@localhost -p 5022

The password is 'secret'. Once you've reached the Python prompt, you have
access to the app object, and can import code, etc.:

    >>> 3 + 4
    7
    >>> print(app)
    <flask.app.Flask object at 0x18e1690>

"""

import logging

from flask import Flask
from crochet import setup, run_in_reactor
setup()

# Web server:
app = Flask(__name__)

@app.route('/')
def index():
    return "Welcome to my boring web server!"


@run_in_reactor
def start_ssh_server(port, username, password, namespace):
    """
    Start an SSH server on the given port, exposing a Python prompt with the
    given namespace.
    """
    # This is a lot of boilerplate, see http://tm.tl/6429 for a ticket to
    # provide a utility function that simplifies this.
    from twisted.internet import reactor
    from twisted.conch.insults import insults
    from twisted.conch import manhole, manhole_ssh
    from twisted.cred.checkers import (
        InMemoryUsernamePasswordDatabaseDontUse as MemoryDB)
    from twisted.cred.portal import Portal

    sshRealm = manhole_ssh.TerminalRealm()
    def chainedProtocolFactory():
        return insults.ServerProtocol(manhole.Manhole, namespace)
    sshRealm.chainedProtocolFactory = chainedProtocolFactory

    sshPortal = Portal(sshRealm, [MemoryDB(**{username: password})])
    reactor.listenTCP(port, manhole_ssh.ConchFactory(sshPortal),
                      interface="127.0.0.1")


if __name__ == '__main__':
    import sys
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    start_ssh_server(5022, "admin", "secret", {"app": app})
    app.run()
