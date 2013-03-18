Crochet
=======

Crochet: Asynchronous calls for threaded Python applications

Features
--------

* setup() runs reactor in thread, supports multiple calls.
* in_event_loop decorator that runs code in Twisted, returns DeferredResult.

Planned Initial Features
------------------------

* callLater which runs code in thread pool.
* LoopingCall which runs code in thread pool.

Twisted integration:
* Twisted logging forwarded to `logging.py`, and supports blocking `Handler`s.
