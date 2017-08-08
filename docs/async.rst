Differences from async/await
============================

Python 3.6 introduces a new mechanism, ``async``/``await``, that allows integrating asynchronous code in a seemingly blocking way.
This mechanism is however quite different than Crochet.

``await`` gives the illusion of blocking, but can only be used in functions that are marked as ``async``.
As such, this is not true blocking integration: the asyncess percolates throughout your program and cannot be restricted to just a single function.

In contrast, Crochet allows you to truly block on an asynchronous event: it's just another blocking function call, and can be used in any normal Python function.
