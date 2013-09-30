#!/usr/bin/python
"""
Example of implementing timeouts using Deferred cancellation.
"""
# The Twisted code we'll be using:
from twisted.mail import smtp

from crochet import setup, run_in_reactor, TimeoutError
crochet.setup()

# Crochet layer, wrapping Twisted API in blocking call:
@run_in_reactor
def _sendmail(to_addr, message):
    """Send an email to the given address with the given message."""
    return smtp.sendmail("127.0.0.1", "from@example.com",
                         [to_addr], message)

# Public API, hides details of Crochet and Twisted from application code:
def sendmail(to_addr, message, timeout=10):
    """Send an email to the given address with the given message.

    If the operation times out, the function will attempt to cancel the send
    operation and then raise a TimeoutError exception. The cancellation is
    best effort and not guaranteed to succeed.
    """
    result = _sendmail(to_addr, message)
    try:
        return result.wait(timeout)
    except TimeoutError:
        # requires Twisted 13.2 to actually cancel
        result.cancel()
        raise


if __name__ == '__main__':
    # Application code using the public API:
    import sys
    sendmail(sys.argv[1], sys.argv[2])
