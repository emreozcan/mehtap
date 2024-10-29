from __future__ import annotations

from abc import abstractmethod, ABC
from inspect import signature
from typing import Optional, Callable, TypeAlias, Any, Mapping, Iterable

from ay.control_structures import ReturnException
from ay.operations import str_to_lua_string
from ay.values import LuaValue, LuaFunction, LuaTable, LuaString, LuaNil, \
    LuaBool, LuaNumber, LuaUserdata


def py_to_lua(value: Any) -> LuaValue:
    if value is None:
        return LuaNil
    if isinstance(value, bool):
        return LuaBool(value)
    if isinstance(value, (int, float)):
        return LuaNumber(value)
    if isinstance(value, str):
        return LuaString(str(value).encode("utf-8"))
    if isinstance(value, bytes):
        return LuaUserdata(value)
    if isinstance(value, Mapping):
        m = LuaTable()
        for k, v in value.items():
            m.put(py_to_lua(k), py_to_lua(v))
        return m
    if isinstance(value, Iterable):
        m = LuaTable()
        for i, v in enumerate(value, start=1):
            m.put(LuaNumber(i), py_to_lua(v))
        return m
    if callable(value):
        return lua_function(wrap_values=True)(value)
    raise NotImplementedError(f"can't yet convert {value!r} to LuaValue")


PyLuaRet: TypeAlias = list[LuaValue] | None
PyLuaFunction: TypeAlias = Callable[..., PyLuaRet]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(
    table: Optional[LuaTable] = None,
    *,
    name: Optional[str] = None,
    gets_stack_frame: bool = False,
    wrap_values: bool = False,
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

        if gets_stack_frame:
            param_names.pop(0)

        def new_function(*args: LuaValue) -> None:
            return_values: list[LuaValue] | None = func(*args)
            if wrap_values and return_values:
                raise ReturnException([
                    py_to_lua(v) for v in return_values
                ])
            raise ReturnException(return_values)

        lf = LuaFunction(
            param_names=[str_to_lua_string(x) for x in param_names],
            variadic=f_variadic,
            parent_stack_frame=None,
            block=new_function,
            gets_stack_frame=gets_stack_frame,
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
