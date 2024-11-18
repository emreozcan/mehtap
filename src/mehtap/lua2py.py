from __future__ import annotations

from typing import Any, overload, Callable, TYPE_CHECKING

from mehtap.control_structures import LuaError
from mehtap.operations import index, call
from mehtap.values import (
    LuaNil,
    LuaBool,
    LuaNumber,
    LuaString,
    LuaTable,
    LuaFunction,
    LuaValue, type_of_lv,
)
from mehtap.vm import VirtualMachine


if TYPE_CHECKING:
    from mehtap.values import LuaNilType


@overload
def lua2py(value: LuaNilType) -> None: ...


@overload
def lua2py(value: LuaBool) -> bool: ...


@overload
def lua2py(value: LuaNumber) -> int | float: ...


@overload
def lua2py(value: LuaString) -> bytes: ...


@overload
def lua2py(value: LuaTable) -> dict: ...


@overload
def lua2py(value: LuaFunction) -> Callable: ...


@overload
def lua2py(value: LuaValue) -> Any: ...


def lua2py(value: Any) -> Any:
    """Convert a :class:`LuaValue` to a plain Python value.

    If the value has a ``__py`` metamethod,
    the converter will call it and convert its return value instead.

    Sequence tables are not converted to lists, they are also converted to
    dicts having keys *1, 2, ..., n*.

    :class:`LuaFunctions <LuaFunction>` are converted using a wrapper function,
    which converts all arguments into :class:`LuaValues <LuaValue>`,
    calls the :class:`LuaFunction` using them,
    and then converts the return value back to a Python value.

    This function is implemented using memoization,
    so it can convert recursive data structures.
    """
    return _lua2py(value, {})


PY_SYMBOL = LuaString(b"__py")


def _lua2py(lua_val, memos):
    if id(lua_val) in memos:
        return memos[id(lua_val)]
    if lua_val is LuaNil:
        return None
    if isinstance(lua_val, LuaBool):
        return lua_val.true
    if isinstance(lua_val, LuaNumber):
        return lua_val.value
    if isinstance(lua_val, LuaString):
        return lua_val.content
    if isinstance(lua_val, LuaTable):
        mt = lua_val.get_metatable()
        if mt is not LuaNil:
            metamethod = index(mt, PY_SYMBOL)
            if metamethod is not LuaNil:
                if not isinstance(metamethod, LuaFunction):
                    raise LuaError(
                        f"metavalue __py is a {type_of_lv(metamethod)}, "
                        f"not a function"
                    )
                if metamethod.parent_scope or not metamethod.gets_scope:
                    m = _lua2py(
                        call(
                            metamethod,
                            [lua_val],
                            metamethod.parent_scope,
                        ),
                        memos,
                    )
                else:
                    vm = VirtualMachine()
                    m = _lua2py(
                        call(
                            metamethod,
                            [lua_val],
                            vm.root_scope,
                        ),
                        memos,
                    )
                memos[id(lua_val)] = m
                return m
        m = {}
        memos[id(lua_val)] = m
        for k, v in lua_val.map.items():
            if v is LuaNil:
                continue
            py_v = _lua2py(v, memos)
            py_k = _lua2py(k, memos)
            m[py_k] = py_v
        return m
    if isinstance(lua_val, LuaFunction):
        from mehtap.py2lua import py2lua

        def func(*args):
            return_values = call(
                lua_val,
                args=[py2lua(x) for x in args],
                scope=None,
            )
            return [lua2py(rv) for rv in return_values]

        if lua_val.name is not None:
            func.__name__ = func.__qualname__ = lua_val.name
        else:
            func.__name__ = func.__qualname__ = "<anonymous Lua function>"
        return func
    raise TypeError(f"unknown LuaValue {lua_val!r}")
