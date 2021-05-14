Static Type Checking
--------------------

Crochet comes with type hints for Python 3.6+.  However, due to current
limitations in ``Callable`` generic construction (see
`PEP 612 — Parameter Specification Variables`_), the arguments of a call to
a ``@run_in_reactor``-decorated function or method cannot be checked without
giving type checkers some special help.  Crochet ships with a plugin which
fills this role when the ``mypy`` static type checker is used.  It resides in
``crochet.mypy`` and must be configured as described in
`Configuring mypy to use plugins`_.  For example, in a ``mypy.ini``
configuration file::

    [mypy]
    plugins = crochet.mypy

This type checking is intended primarily for code which calls the decorated
function.  As Twisted isn't fully type-hinted yet, and in particular Deferred
does not yet have a generic type argument so that the eventual result type can
vary, the analysis of the return type of a ``@run_in_reactor`` function/method
does not account for a Deferred result.  This requires you to lie to the type
checker when returning a Deferred; just cast it to the known, eventual result
type using ``typing.cast``.  For example::

    @run_in_reactor
    def get_time_in_x_seconds(delay: float) -> float:
        def get_time() -> float:
            return reactor.seconds()  # type: ignore

        if delay < 0.001:
            # Close enough; just return the current time.
            return get_time()
        else:
            d = Deferred()

            def complete():
                d.callback(get_time())

            reactor.callLater(delay, complete)  # type: ignore
            return typing.cast(float, d)

If the mypy plugin is correctly installed, the client code will expect a float
from the ``wait()`` of the ``EventualResult`` returned by a call to this
function::

    # OK
    t1: float = get_time_in_x_seconds(2).wait(3)
    print(f"The reactor time is {t1}")

    # mypy error: Incompatible types in assignment
    #   (expression has type "float", variable has type "str")
    t2: str = get_time_in_x_seconds(2).wait(3)
    print(f"The reactor time is {t2}")

.. _PEP 612 — Parameter Specification Variables: https://www.python.org/dev/peps/pep-0612/
.. _Configuring mypy to use plugins: https://mypy.readthedocs.io/en/latest/extending_mypy.html#configuring-mypy-to-use-plugins
