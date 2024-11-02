from __future__ import annotations

from typing import Any, overload, Callable, TYPE_CHECKING

from ay.values import (
    LuaNil,
    LuaBool,
    LuaNumber,
    LuaString,
    LuaTable,
    LuaFunction,
    LuaValue,
)
from ay.vm import VirtualMachine


if TYPE_CHECKING:
    from ay.values import LuaNilType


@overload
def lua2py(value: LuaNilType) -> None:
    pass


@overload
def lua2py(value: LuaBool) -> bool:
    pass


@overload
def lua2py(value: LuaNumber) -> int | float:
    pass


@overload
def lua2py(value: LuaString) -> bytes:
    pass


@overload
def lua2py(value: LuaTable) -> dict:
    pass


@overload
def lua2py(value: LuaFunction) -> Callable:
    pass


@overload
def lua2py(value: LuaValue) -> Any:
    pass


def lua2py(value: Any) -> Any:
    """Convert a :class:`LuaValue` to a plain Python value.

    If the value has a ``__py`` metamethod,
    the converter will call it and convert its return value instead.

    Sequence tables are not converted to lists, they are also converted to
    dicts having keys *1, 2, ..., n*.

    Functions are converted using a wrapper function,
    which converts all arguments into LuaValues,
    calls the function using them,
    and then converts the return value back to a Python value.

    This function is implemented using an expansion stack, so it can
    convert recursive data structures.
    """
    return _lua2py(value, {})


PY_SYMBOL = LuaString(b"__py")


def _lua2py(lua_val, obj_map):
    if id(lua_val) in obj_map:
        return obj_map[id(lua_val)]
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
            metamethod = mt.get(PY_SYMBOL)
            if metamethod is not LuaNil:
                assert isinstance(metamethod, LuaFunction)
                if metamethod.parent_scope or not metamethod.gets_scope:
                    m = _lua2py(
                        metamethod.call(
                            [lua_val],
                            metamethod.parent_scope,
                        ),
                        obj_map,
                    )
                else:
                    vm = VirtualMachine()
                    m = _lua2py(
                        metamethod.call(
                            [lua_val],
                            vm.root_scope,
                        ),
                        obj_map,
                    )
                obj_map[id(lua_val)] = m
                return m
        m = {}
        obj_map[id(lua_val)] = m
        for k, v in lua_val.map.items():
            if v is LuaNil:
                continue
            py_v = _lua2py(v, obj_map)
            py_k = _lua2py(k, obj_map)
            m[py_k] = py_v
        return m
    if isinstance(lua_val, LuaFunction):
        from ay.py2lua import py2lua

        def func(*args):
            return lua2py(lua_val.call(*[py2lua(x) for x in args], None))

        if lua_val.name is not None:
            func.__name__ = func.__qualname__ = lua_val.name
        else:
            func.__name__ = func.__qualname__ = "<anonymous Lua function>"
        return func
