from typing import Any, Awaitable, Callable, Coroutine, Generic, Optional, overload, TypeVar, Union
from typing_extensions import ParamSpec
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_P = ParamSpec("_P")


def setup() -> None: ...
def run_in_reactor(
    function: Callable[_P, _T]
) -> Callable[_P, EventualResult[_T]]: ...

class EventualResult(Generic[_T_co]):
    def cancel(self) -> None: ...
    def wait(self, timeout: float) -> _T_co: ...
    def stash(self) -> int: ...
    def original_failure(self) -> Optional[Failure]: ...

class TimeoutError(Exception): ...

def retrieve_result(result_id: int) -> EventualResult[object]: ...
def no_setup() -> None: ...


@overload
def wait_for_x(f: Callable[_P, Deferred[_T]]) -> Callable[_P, _T]:
    ...

@overload
def wait_for_x(f: Callable[_P, Coroutine[None, None, _T]]) -> Callable[_P, _T]:
    ...


@overload
def wait_for_x(f: Callable[_P, _T]) -> Callable[_P, _T]:
    ...


@overload
def wait_for(f: float) -> Callable[[Callable[_P, Deferred[_T]]], Callable[_P, _T]]:
    ...

@overload
def wait_for(f: float) -> Callable[[Callable[_P, Coroutine[None, None, _T]]], Callable[_P, _T]]:
    ...


@overload
def wait_for(f: float) -> Callable[[Callable[_P, _T]], Callable[_P, _T]]:
    ...




class ReactorStopped(Exception): ...

__version__: str
