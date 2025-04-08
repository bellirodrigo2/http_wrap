from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import (
    Any,
    ContextManager,
    Generic,
    Iterable,
    Iterator,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
    cast,
    runtime_checkable,
)

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)


@runtime_checkable
class GetHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> Any: ...


@runtime_checkable
class SetHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, value: Any) -> Any: ...


HasHandler = GetHandler


@runtime_checkable
class DeleteHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> None: ...


@runtime_checkable
class CallHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class ContextHandler(Protocol):
    def __call__(self, obj: Any) -> ContextManager[Any]: ...


IteratorHandler = GetHandler

StrHandler = GetHandler
ReprHandler = GetHandler


@runtime_checkable
class GetItemHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, key: str) -> Any: ...


@runtime_checkable
class LenHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> int: ...


@runtime_checkable
class SetItemHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, key: Any, value: Any) -> None: ...


@runtime_checkable
class EqualHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra, other: Any) -> bool: ...


NEqualHandler = EqualHandler


@runtime_checkable
class BoolHandler(Protocol[T_contra]):
    def __call__(self, obj: T_contra) -> bool: ...


@dataclass
class Handler(Generic[T]):
    get: Optional[dict[str, GetHandler[T]]] = None
    set: Optional[dict[str, SetHandler[T]]] = None
    has: Optional[dict[Any, HasHandler[T]]] = None
    delete: Optional[dict[str, DeleteHandler[T]]] = None
    call: Optional[dict[str, CallHandler[T]]] = None
    context: Optional[ContextHandler] = None
    iterator: Optional[IteratorHandler[T]] = None
    str: Optional[StrHandler[T]] = None
    repr: Optional[ReprHandler[T]] = None
    getitem: Optional[GetItemHandler[T]] = None
    setitem: Optional[SetItemHandler[T]] = None
    len: Optional[LenHandler[T]] = None
    eq: Optional[EqualHandler[T]] = None
    ne: Optional[NEqualHandler[T]] = None
    bool: Optional[BoolHandler[T]] = None


@dataclass
class Proxy(Generic[T]):
    target: T
    handler: Handler[T]
    __is_proxy__: bool = field(init=False, default=True)

    def __post_init__(self) -> None:
        if not isinstance(self.handler, Handler):  # type: ignore
            raise TypeError("handler must be an instance of Handler")
        self._iter: Optional[Iterator[Any]] = None

    def __getattr__(self, name: str) -> Any:
        if self.handler.call:
            func = self.handler.call.get(name)
            if func is not None:
                return lambda *args, **kwargs: func(self.target, *args, **kwargs)  # type: ignore

        if self.handler.get:
            func = self.handler.get.get(name)
            if func is not None:
                return func(self.target)
        return getattr(self.target, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"target", "handler", "__is_proxy__", "_iter"}:
            return super().__setattr__(name, value)

        if self.handler.set:
            func = self.handler.set.get(name)
            if func is not None:
                return func(self.target, value)

        setattr(self.target, name, value)

    def __delattr__(self, name: str) -> None:
        if self.handler.delete:
            func = self.handler.delete.get(name)
            if func is not None:
                return func(self.target)

        delattr(self.target, name)

    def __contains__(self, name: object) -> bool:
        if self.handler.has:
            func = self.handler.has.get(name)
            if func:
                return func(self.target)

        if isinstance(self.target, Iterable):
            try:
                return name in self.target  # type: ignore
            except TypeError:
                pass

        if isinstance(name, str):
            return hasattr(self.target, name)  # type: ignore

        return False

    def __enter__(self) -> T:
        if self.handler.context:
            self._ctx = self.handler.context(self.target)
            return self._ctx.__enter__()

        # fallback seguro: garantimos em runtime que o target é context manager
        if not hasattr(self.target, "__enter__") or not hasattr(
            self.target, "__exit__"
        ):
            raise TypeError("Target does not support context manager protocol")

        return cast(ContextManager[Any], self.target).__enter__()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        if hasattr(self, "_ctx"):
            try:
                return self._ctx.__exit__(exc_type, exc_val, exc_tb)
            finally:
                del self._ctx
        return cast(ContextManager[Any], self.target).__exit__(
            exc_type, exc_val, exc_tb
        )

    def __iter__(self) -> Iterable[Any]:
        if self.handler.iterator:
            return iter(self.handler.iterator(self.target))
        return iter(self.target)  # type: ignore

    def __next__(self) -> Any:
        if not hasattr(self, "_iter") or self._iter is None:
            self._iter = iter(self)  # type: ignore
        return next(self._iter)  # type: ignore

    def __getattribute__(self, name: str):  # type: ignore
        if name == "__class__" and getattr(self, "__spoof_class__", False):
            return type(object.__getattribute__(self, "target"))  # type: ignore
        return object.__getattribute__(self, name)

    def __str__(self) -> str:
        if self.handler.str:
            return self.handler.str(self.target)
        return str(self.target)

    def __repr__(self) -> str:
        if self.handler.repr:
            return self.handler.repr(self.target)
        return repr(self.target)

    def __getitem__(self, key: Any) -> Any:
        if self.handler.getitem:
            return self.handler.getitem(self.target, key)
        return self.target[key]  # type: ignore

    def __setitem__(self, key: Any, value: Any) -> None:
        if self.handler.setitem:
            return self.handler.setitem(self.target, key, value)
        self.target[key] = value  # type: ignore

    def __len__(self) -> int:
        if self.handler.len:
            return self.handler.len(self.target)
        return len(self.target)  # type: ignore

    def __eq__(self, other: Any) -> bool:
        if self.handler.eq:
            return self.handler.eq(self.target, other)
        return self.target == other  # type: ignore

    def __ne__(self, other: Any) -> bool:
        if self.handler.ne:
            return self.handler.ne(self.target, other)
        return self.target != other  # type: ignore

    def __bool__(self) -> bool:
        if self.handler.bool:
            return self.handler.bool(self.target)
        return bool(self.target)

    @classmethod
    def wrap(
        cls, target: T, handler: Handler[T], spoof_class: bool = False
    ) -> Proxy[T]:
        instance = cls.__new__(cls)
        object.__setattr__(instance, "target", target)
        object.__setattr__(instance, "handler", handler)
        instance.__post_init__()
        if spoof_class:
            object.__setattr__(instance, "__spoof_class__", True)
        return instance


def is_proxy(obj: Any) -> bool:
    return getattr(obj, "__is_proxy__", False)


def unwrap(obj: Union[T, Proxy[T]]) -> T:
    if is_proxy(obj):
        return getattr(obj, "target")
    return obj  # type: ignore


def deep_unwrap(obj: Any) -> Any:
    while is_proxy(obj):
        obj = unwrap(obj)
    return obj
