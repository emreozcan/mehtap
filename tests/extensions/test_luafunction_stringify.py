from mehtap.values import LuaFunction


def noop():
    return None


def test_luafunctions_from_lua():
    # This is equivalent to `function() end`
    f = LuaFunction(
        param_names=[],
        variadic=False,
        parent_scope=None,
        block=noop,
        gets_scope=False,
        name=None,
        min_req=None,
    )
    assert str(f).startswith("function(): 0x")

    f.variadic = True
    assert str(f).startswith("function(...): 0x")
    f.variadic = False

    f.param_names += "a"
    assert str(f).startswith("function(a): 0x")

    f.param_names += "b"
    assert str(f).startswith("function(a, b): 0x")

    f.min_req = 1
    assert str(f).startswith("function(a[, b]): 0x")

    f.variadic = True
    assert str(f).startswith("function(a[, b[, ...]]): 0x")

    f.min_req = 2
    assert str(f).startswith("function(a, b[, ...]): 0x")

    f.min_req = 0
    assert str(f).startswith("function([a[, b[, ...]]]): 0x")

    f.param_names = None
    assert str(f).startswith(f"function([...]): 0x")

    f.name = "noop"
    assert str(f).startswith(f"function noop([...]): 0x")
