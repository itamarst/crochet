#!/usr/bin/python
"""
A command-line application that uses Twisted to do an MX DNS query.
"""

from __future__ import print_function

from twisted.names.client import lookupMailExchange
from crochet import setup, wait_for
setup()


# Twisted code:
def _mx(domain):
    """
    Return Deferred that fires with a list of (priority, MX domain) tuples for
    a given domain.
    """
    def got_records(result):
        return sorted(
            [(int(record.payload.preference), str(record.payload.name))
             for record in result[0]])
    d = lookupMailExchange(domain)
    d.addCallback(got_records)
    return d


# Blocking wrapper:
@wait_for(timeout=5)
def mx(domain):
    """
    Return list of (priority, MX domain) tuples for a given domain.
    """
    return _mx(domain)


# Application code:
def main(domain):
    print("Mail servers for %s:" % (domain,))
    for priority, mailserver in mx(domain):
        print(priority, mailserver)


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
