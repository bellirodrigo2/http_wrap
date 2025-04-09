from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable, Generic, Protocol, Type, TypeVar

from http_wrap.response import ResponseInterface

T = TypeVar("T")


@dataclass(frozen=True)
class ReadProxy(Generic[T]):

    methods: list[str]
    attr_props: list[str]

    target: T
    keys_map: Mapping[str, str] = field(default_factory=dict)  # type: ignore
    overwrite: Mapping[str, Callable[..., Any]] = field(default_factory=dict)  # type: ignore

    def __getattr__(self, name: str) -> Any:

        if name in ["target", "keys_map", "overwrite", "methods", "attr_props"]:
            raise AttributeError(f"Cannot access Proxy internal fields.")

        if name in self.methods:
            if name in self.overwrite:
                return partial(self.overwrite[name], self.target)
            func_name: str = self.keys_map.get(name, name)
            try:
                func = getattr(self.target, func_name)
            except AttributeError:
                raise AttributeError(f"Method '{name}' not found in 'target'.")
            return partial(func, self.target)

        if name in self.attr_props:
            if name in self.overwrite:
                return (
                    self.overwrite[name](self.target)
                    if callable(self.overwrite[name])
                    else self.overwrite[name]
                )
            attr_name: str = self.keys_map.get(name, name)
            try:
                return getattr(self.target, attr_name)
            except AttributeError:
                raise AttributeError(f"Attribute '{name}' not found in 'target'.")

        raise AttributeError(f"Method or attribute '{name}' not found in Proxy.")

    def __eq__(self, other: object) -> bool:
        return self.target == other  # type: ignore

    def __ne__(self, other: object) -> bool:
        return self.target != other  # type: ignore

    def __str__(self) -> str:
        return str(self.target)

    def __repr__(self) -> str:
        return repr(self.target)


import inspect


def get_user_defined_methods_and_attributes(cls):
    members = inspect.getmembers(cls)
    user_methods = [
        name
        for name, obj in members
        if inspect.isfunction(obj) and obj.__module__ == cls.__module__
    ]
    user_attributes = [
        name
        for name, obj in members
        if not inspect.isfunction(obj) and not name.startswith("__")
    ]
    return user_methods, user_attributes


def make_proxy(
    target: T,
    interface: Any,
    key_map: Mapping[str, str],
    overwrite: Mapping[str, Any],
) -> ReadProxy[T]:
    print(get_user_defined_methods_and_attributes(interface))
    all_attrs = [s for s in dir(interface) if s.startswith("_") is False]
    methods = [m for m in all_attrs if callable(getattr(interface, m))]
    attr_props = [a for a in all_attrs if not callable(getattr(interface, a))]

    proxy = ReadProxy(methods, attr_props, target, key_map, overwrite)
    return proxy


if __name__ == "__main__":
    # print(keys)
    # print(methods)
    # print(attr_props)
    ...
