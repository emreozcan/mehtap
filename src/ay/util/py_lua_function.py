from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Callable, TypeAlias

from ay.control_structures import ReturnException
from ay.values import LuaValue, LuaFunction, LuaTable, LuaString

PyLuaRet: TypeAlias = list[LuaValue] | None
PyLuaFunction: TypeAlias = Callable[..., PyLuaRet]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(
        table: LuaTable = None,
        *,
        name: str = None,
        interacts_with_the_vm: bool = False
) -> LuaDecorator:
    def decorator(func: PyLuaFunction) -> LuaFunction:
        if name:
            func.__name__ = name

        def new_function(*args: LuaValue) -> None:
            return_values: list[LuaValue] | None = func(*args)
            raise ReturnException(return_values)

        lf = LuaFunction(
            param_names=[],
            variadic=True,
            parent_stack_frame=None,
            block=new_function,
            interacts_with_the_vm=interacts_with_the_vm,
            name=func.__name__,
        )
        if table is not None:
            table.put(
                LuaString(func.__name__.encode("utf-8")),
                lf
            )
        return lf
    return decorator


class LibraryProvider(ABC):
    @abstractmethod
    def provide(self, table: LuaTable) -> None:
        pass
