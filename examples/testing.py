#!/usr/bin/python
"""
Demonstration of accessing wrapped functions for testing.
"""

from __future__ import print_function

from crochet import setup, run_in_reactor
setup()

@run_in_reactor
def add(x, y):
    return x + y


if __name__ == '__main__':
    print("add() returns EventualResult:")
    print("    ", add(1, 2))
    print("add.wrapped_function() returns result of underlying function:")
    print("    ", add.wrapped_function(1, 2))
