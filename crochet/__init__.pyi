from typing import Any, Callable, Coroutine, Generic, Optional, overload, TypeVar
from typing_extensions import ParamSpec
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_F = TypeVar("_F", bound=Callable[..., Any])
_P = ParamSpec("_P")


def setup() -> None: ...
def run_in_reactor(
    function: Callable[..., _T]
) -> Callable[..., EventualResult[_T]]: ...

class EventualResult(Generic[_T_co]):
    def cancel(self) -> None: ...
    def wait(self, timeout: float) -> _T_co: ...
    def stash(self) -> int: ...
    def original_failure(self) -> Optional[Failure]: ...

class TimeoutError(Exception): ...

def retrieve_result(result_id: int) -> EventualResult[object]: ...
def no_setup() -> None: ...

@overload
def wait_for(timeout: float) -> Callable[
    [Callable[_P, Deferred[_T]]],
    Callable[_P, _T]
]: ...

@overload
def wait_for(timeout: float) -> Callable[
    [Callable[_P, Coroutine[Any, Any, _T]]],
    Callable[_P, _T]
]: ...

@overload
def wait_for(timeout: float) -> Callable[
    [Callable[_P, _T]],
    Callable[_P, _T]
]: ...


class ReactorStopped(Exception): ...

__version__: str
