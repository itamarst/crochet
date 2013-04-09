#!/usr/bin/python
"""
A command-line application that uses Twisted to do an MX DNS query.
"""

from __future__ import print_function

from crochet import setup, in_reactor
setup()


@in_reactor
def mx(reactor, domain):
    """
    Return list of MX domains for a given domain.
    """
    from twisted.names.client import lookupMailExchange
    def got_records(result):
        hosts, authorities, additional = result
        return [str(record.name) for record in additional]
    d = lookupMailExchange(domain)
    d.addCallback(got_records)
    return d


def main(domain):
    print("Mail servers for %s:" % (domain,))
    for mailserver in mx(domain).wait():
        print(mailserver)


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
