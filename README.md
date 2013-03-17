Crochet
=======

Crochet: Asynchronous calls for threaded Python applications

Features
--------

Planned Initial Features
------------------------

* setup() runs reactor in thread, supports multiple calls.
* runTwisted decorator that runs code in Twisted, returns future of some sort.
* callLater which runs code in thread pool.
* LoopingCall which runs code in thread pool.

Twisted integration:
* Twisted logging forwarded to `logging.py`, and supports blocking `Handler`s.
