from __future__ import annotations

from inspect import signature
from typing import Optional, Callable, TypeAlias, Mapping, Iterable, \
    overload

from ay.control_structures import ReturnException
from ay.operations import str_to_lua_string
from ay.values import LuaValue, LuaFunction, LuaTable, LuaString, LuaNil, \
    LuaBool, LuaNumber


@overload
def py2lua(value: None) -> LuaNil: ...


@overload
def py2lua(value: bool) -> LuaBool: ...


@overload
def py2lua(value: int | float) -> LuaNumber: ...


@overload
def py2lua(value: str) -> LuaString: ...


@overload
def py2lua(value: Mapping) -> LuaTable: ...


@overload
def py2lua(value: Iterable) -> LuaTable: ...


@overload
def py2lua(value: Callable) -> LuaFunction: ...


def py2lua(value) -> LuaValue:
    return _py2lua(value, {})


def _py2lua(py_val, obj_map):
    if id(py_val) in obj_map:
        return obj_map[id(py_val)]
    if py_val is None:
        return LuaNil
    if hasattr(py_val, "__lua__"):
        return py_val.__lua__()
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
            m.put(_py2lua(k, obj_map), _py2lua(v, obj_map))
        return m
    if isinstance(py_val, Iterable):
        m = LuaTable()
        obj_map[id(py_val)] = m
        for i, v in enumerate(py_val, start=1):
            m.put(LuaNumber(i), _py2lua(v, obj_map))
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
    rename_args: Optional[list[str]] = None,
) -> LuaDecorator:
    def decorator(func: Callable) -> LuaFunction:
        f_signature = signature(func)
        callable_argnames = []
        minimum_required = 0
        f_variadic = False
        scope_skipped = False
        for param in f_signature.parameters.values():
            if gets_scope and not scope_skipped:
                scope_skipped = True
                continue
            if f_variadic:
                raise ValueError(
                    f"Function {func.__qualname__} has a parameter after a "
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
                    f"Function {func.__qualname__} has a parameter that is not "
                    f"positional or variadic"
                )
            callable_argnames.append(param.name)

        def new_function(*args: LuaValue) -> None:
            return_values: list[LuaValue] | None = func(*args)
            if wrap_values and return_values:
                raise ReturnException([
                    py2lua(v) for v in return_values
                ])
            raise ReturnException(return_values)

        if rename_args is None:
            lua_param_names = [str_to_lua_string(x) for x in callable_argnames]
        else:
            callable_arg_count = len(callable_argnames)
            rename_arg_count = len(rename_args)
            if callable_arg_count != rename_arg_count:
                scope_warning = (
                    "(not counting the scope parameter,) "
                    if gets_scope else ""
                )
                raise ValueError(
                    f"Callable has {callable_arg_count} parameters "
                    f"{scope_warning}but "
                    f"{len(rename_args)} names were supplied"
                )
            lua_param_names = [str_to_lua_string(x) for x in rename_args]

        used_name = name if name is not None else func.__name__

        lf = LuaFunction(
            param_names=lua_param_names,
            variadic=f_variadic,
            parent_scope=None,
            block=new_function,
            gets_scope=gets_scope,
            name=used_name,
            min_req=minimum_required,
        )
        if table is not None:
            table.put(py2lua(used_name), lf)
        return lf

    return decorator
