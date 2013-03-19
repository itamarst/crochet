Crochet
=======

Crochet: Asynchronous calls for threaded Python applications

Features
--------

* setup() runs reactor in thread, supports multiple calls.
* in_event_loop decorator that runs code in Twisted, returns DeferredResult.
Twisted integration:
* Twisted logging forwarded to `logging.py`, and supports blocking `Handler`s.
