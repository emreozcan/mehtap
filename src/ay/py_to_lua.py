from __future__ import annotations

from inspect import signature
from typing import Optional, Callable, TypeAlias, Mapping, Iterable, \
    overload

from ay.control_structures import ReturnException
from ay.operations import str_to_lua_string
from ay.values import LuaValue, LuaFunction, LuaTable, LuaString, LuaNil, \
    LuaBool, LuaNumber


@overload
def py_to_lua(value: None) -> LuaNil: ...


@overload
def py_to_lua(value: bool) -> LuaBool: ...


@overload
def py_to_lua(value: int | float) -> LuaNumber: ...


@overload
def py_to_lua(value: str) -> LuaString: ...


@overload
def py_to_lua(value: Mapping) -> LuaTable: ...


@overload
def py_to_lua(value: Iterable) -> LuaTable: ...


@overload
def py_to_lua(value: Callable) -> LuaFunction: ...


def py_to_lua(value) -> LuaValue:
    return _py_to_lua(value, {})


def _py_to_lua(py_val, obj_map):
    if id(py_val) in obj_map:
        return obj_map[id(py_val)]
    if py_val is None:
        return LuaNil
    if isinstance(py_val, bool):
        return LuaBool(py_val)
    if isinstance(py_val, (int, float)):
        return LuaNumber(py_val)
    if isinstance(py_val, str):
        return LuaString(str(py_val).encode("utf-8"))
    if isinstance(py_val, Mapping):
        m = LuaTable()
        obj_map[id(py_val)] = m
        for k, v in py_val.items():
            m.put(_py_to_lua(k, obj_map), _py_to_lua(v, obj_map))
        return m
    if isinstance(py_val, Iterable):
        m = LuaTable()
        obj_map[id(py_val)] = m
        for i, v in enumerate(py_val, start=1):
            m.put(LuaNumber(i), _py_to_lua(v, obj_map))
        return m
    if callable(py_val):
        return lua_function(wrap_values=True)(py_val)
    raise NotImplementedError(f"can't yet convert {py_val!r} to LuaValue")


Py2LuaAccepts: TypeAlias = (bool | int | float
                            | str
                            | Mapping | Iterable
                            | Callable)
PyLuaRet: TypeAlias = list[LuaValue] | None
PyLuaWrapRet: TypeAlias = list[Py2LuaAccepts] | None
PyLuaFunction: TypeAlias = Callable[..., PyLuaRet]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(
    table: Optional[LuaTable] = None,
    *,
    name: Optional[str] = None,
    gets_scope: bool = False,
    wrap_values: bool = False,
) -> LuaDecorator:
    def decorator(func: PyLuaFunction) -> LuaFunction:
        if name:
            func.__name__ = name

        f_signature = signature(func)
        param_names = []
        minimum_required = 0
        f_variadic = False
        scope_skipped = False
        for param in f_signature.parameters.values():
            if gets_scope and not scope_skipped:
                scope_skipped = True
                continue
            if f_variadic:
                raise ValueError(
                    f"Function {func.__name__} has a parameter after a "
                    f"variadic parameter ({param.name})"
                )
            if param.kind == param.POSITIONAL_ONLY:
                if param.default is param.empty:
                    minimum_required += 1
            elif param.kind == param.VAR_POSITIONAL:
                f_variadic = True
                continue
            else:
                raise ValueError(
                    f"Function {func.__name__} has a parameter that is not "
                    f"positional or variadic"
                )
            param_names.append(param.name)

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
            parent_scope=None,
            block=new_function,
            gets_scope=gets_scope,
            name=func.__name__,
            min_req=minimum_required,
        )
        if table is not None:
            table.put(LuaString(func.__name__.encode("utf-8")), lf)
        return lf

    return decorator
