from __future__ import annotations

from abc import abstractmethod, ABC
from inspect import signature
from typing import Optional, Callable, TypeAlias

from ay.control_structures import ReturnException
from ay.values import LuaValue, LuaFunction, LuaTable, LuaString

PyLuaRet: TypeAlias = list[LuaValue] | None
PyLuaFunction: TypeAlias = Callable[..., PyLuaRet]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(
    table: Optional[LuaTable] = None,
    *,
    name: Optional[str] = None,
    interacts_with_the_vm: bool = False,
) -> LuaDecorator:
    def decorator(func: PyLuaFunction) -> LuaFunction:
        if name:
            func.__name__ = name

        f_signature = signature(func)
        param_names = []
        f_variadic = False
        for param in f_signature.parameters.values():
            if f_variadic:
                raise ValueError(
                    f"Function {func.__name__} has a parameter after a "
                    f"variadic parameter ({param.name})"
                )
            if param.kind not in (
                param.POSITIONAL_ONLY,
                param.VAR_POSITIONAL,
            ):
                raise ValueError(
                    f"Function {func.__name__} has a parameter that is not "
                    f"positional or variadic"
                )
            if param.kind == param.VAR_POSITIONAL:
                f_variadic = True
                continue
            param_names.append(param.name)

        if interacts_with_the_vm:
            param_names.pop(0)

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
            table.put(LuaString(func.__name__.encode("utf-8")), lf)
        return lf

    return decorator


class LibraryProvider(ABC):
    @abstractmethod
    def provide(self, table: LuaTable) -> None:
        pass
