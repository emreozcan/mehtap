from typing import Any, overload, Callable

from ay.values import LuaNil, LuaBool, LuaNumber, LuaString, LuaTable, \
    LuaFunction
from ay.vm import VirtualMachine


@overload
def lua2py(value: LuaNil) -> None:
    pass


@overload
def lua2py(value: LuaBool) -> bool:
    pass


@overload
def lua2py(value: LuaNumber) -> int | float:
    pass


@overload
def lua2py(value: LuaString) -> str:
    pass


@overload
def lua2py(value: LuaTable) -> dict:
    pass


@overload
def lua2py(value: LuaFunction) -> Callable:
    pass


def lua2py(value: Any) -> Any:
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
        return lua_val.content.decode("utf-8")
    if isinstance(lua_val, LuaTable):
        mt = lua_val.get_metatable()
        if mt is not LuaNil:
            metamethod = mt.get(PY_SYMBOL)
            if metamethod is not LuaNil:
                if isinstance(metamethod, LuaFunction):
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
                else:
                    m = _lua2py(metamethod, obj_map)
                obj_map[id(lua_val)] = m
                return m
        m = {}
        obj_map[id(lua_val)] = m
        for k, v in lua_val.map.items():
            py_v = _lua2py(v, obj_map)
            py_k = _lua2py(k, obj_map)
            m[py_k] = py_v
        return m
    if isinstance(lua_val, LuaFunction):
        from ay.py2lua import py2lua

        def func(*args):
            return lua2py(lua_val(*[py2lua(x) for x in args]))
        if lua_val.name is not None:
            func.__name__ = func.__qualname__ = lua_val.name
        else:
            func.__name__ = func.__qualname__ = "<anonymous Lua function>"
        return func
