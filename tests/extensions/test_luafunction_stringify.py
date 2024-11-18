from mehtap.ast_nodes import Block
from mehtap.values import LuaFunction


def noop():
    return None


def test_native_functions():
    # This is equivalent to `function() end`
    native_f = LuaFunction(
        param_names=[],
        variadic=False,
        parent_scope=None,
        block=noop,
        gets_scope=False,
        name=None,
        min_req=None,
    )
    assert str(native_f).startswith("native function(): 0x")

    native_f.variadic = True
    assert str(native_f).startswith("native function(...): 0x")
    native_f.variadic = False

    native_f.param_names += "a"
    assert str(native_f).startswith("native function(a): 0x")

    native_f.param_names += "b"
    assert str(native_f).startswith("native function(a, b): 0x")

    native_f.min_req = 1
    assert str(native_f).startswith("native function(a[, b]): 0x")

    native_f.variadic = True
    assert str(native_f).startswith("native function(a[, b[, ...]]): 0x")

    native_f.min_req = 2
    assert str(native_f).startswith("native function(a, b[, ...]): 0x")

    native_f.min_req = 0
    assert str(native_f).startswith("native function([a[, b[, ...]]]): 0x")

    native_f.param_names = None
    assert str(native_f).startswith(f"native function([...]): 0x")

    native_f.name = "noop"
    assert str(native_f).startswith(f"native function noop([...]): 0x")


def test_lua_functions():
    # This is equivalent to `function() end`
    lua_f = LuaFunction(
        param_names=[],
        variadic=False,
        parent_scope=None,
        block=Block(statements=[]),
        gets_scope=False,
        name=None,
        min_req=None,
    )
    assert str(lua_f).startswith("function(): 0x")

    lua_f.variadic = True
    assert str(lua_f).startswith("function(...): 0x")
    lua_f.variadic = False

    lua_f.param_names += "a"
    assert str(lua_f).startswith("function(a): 0x")

    lua_f.param_names += "b"
    assert str(lua_f).startswith("function(a, b): 0x")

    lua_f.min_req = 1
    assert str(lua_f).startswith("function(a[, b]): 0x")

    lua_f.variadic = True
    assert str(lua_f).startswith("function(a[, b[, ...]]): 0x")

    lua_f.min_req = 2
    assert str(lua_f).startswith("function(a, b[, ...]): 0x")

    lua_f.min_req = 0
    assert str(lua_f).startswith("function([a[, b[, ...]]]): 0x")

    lua_f.param_names = None
    assert str(lua_f).startswith(f"function([...]): 0x")

    lua_f.name = "noop"
    assert str(lua_f).startswith(f"function noop([...]): 0x")
