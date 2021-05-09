"""
Mypy plugin to aid with typechecking code that uses Crochet.
"""
import typing
from typing import Callable, Optional

from mypy.plugin import FunctionContext, Plugin
from mypy.types import CallableType, Type, get_proper_type


def plugin(_version: str) -> typing.Type[Plugin]:
    return CrochetMypyPlugin


class CrochetMypyPlugin(Plugin):
    """
    Assists mypy with type checking APIs not (yet) fully covered by Python's
    type hint annotation types.
    """

    def get_function_hook(
        self,
        fullname: str,
    ) -> Optional[Callable[[FunctionContext], Type]]:
        if fullname == "crochet.run_in_reactor":
            return _copyargs_callback
        return None


def _copyargs_callback(ctx: FunctionContext) -> Type:
    """
    Copy the paramters from the signature of the type of the argument of the
    call to the signature of the return type.  This is appropriate for
    function/method decorators which can be used on functions/methods with
    variable signatures and simply change the return type while passing through
    all arguments unchanged.

    For example::

        T = TypeVar("T")

        def make_coroutine(
            f: Callable[..., Awaitable[T]],
        ) -> Callable[..., Coroutine[None, None, T]]:

            @wraps(f)
            async def wrapper(*a: Any, **kw: Any) -> T:
                return await f(*a, **kw)

            # Replace the runtime-inspectable signature too.
            sig = inspect.signature(f, follow_wrapped=False)
            if sig.get_origin() is Awaitable:
                t = sig.return_annotation.get_args(0)
                wrapper.__signature__ = sig.replace(
                    return_annotation=Coroutine[None, None, t],
                )

            return wrapper

        @make_coroutine
        def do_thing_in_future(
            thing: Callable[[], Result], when: float,
        ) -> Awaitable[Result]:
            ...
            return asyncio.ensure_future(...)

        # Oops!  No type-checking on do_thing_in_future's args without help!
        # Hopefully future Python typing enhancements will fix this. For
        # example, see PEP 612: Parameter Specification Variables.
    """
    original_return_type = ctx.default_return_type
    if not ctx.arg_types or len(ctx.arg_types[0]) != 1:
        return original_return_type

    arg_type = get_proper_type(ctx.arg_types[0][0])
    default_return_type = get_proper_type(original_return_type)

    if not (
        isinstance(arg_type, CallableType)
        and isinstance(default_return_type, CallableType)
    ):
        return original_return_type

    return default_return_type.copy_modified(
        arg_types=arg_type.arg_types,
        arg_kinds=arg_type.arg_kinds,
        arg_names=arg_type.arg_names,
        variables=arg_type.variables,
        is_ellipsis_args=arg_type.is_ellipsis_args,
    )
