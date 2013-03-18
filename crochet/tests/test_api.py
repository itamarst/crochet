"""
Tests for the crochet APIs.
"""

from twisted.trial.unittest import TestCase

from crochet import _Crochet


class InEventLoopTests(TestCase):
    """
    Tests for the in_event_loop decorator.
    """
