import pytest

from mehtap.py2lua import lua_function
from mehtap.values import LuaString, LuaTable, LuaFunction


def test_preserve_table_sanity_check():
    with pytest.raises(ValueError) as excinfo:
        @lua_function(table=None, preserve=True)
        def x():
            pass
    assert excinfo.type is ValueError
    assert "What's your point?" in str(excinfo.value)


def test_invalid_arg_after_variadic():
    with pytest.raises(ValueError) as excinfo:
        @lua_function()
        def x(*a, sentinel_value_123456):
            pass

    assert excinfo.type is ValueError
    assert "sentinel_value_123456" in str(excinfo.value)


def test_invalid_arg_not_pos_only():
    with pytest.raises(ValueError) as excinfo:
        @lua_function()
        def x(a, b, /, sentinel_value_123456):
            pass

    assert excinfo.type is ValueError
    assert "sentinel_value_123456" in str(excinfo.value)


def test_rename_args():
    @lua_function(rename_args=["x", "y", "z"])
    def f(a, b, c, /):
        return None

    assert f.param_names == [
        LuaString(b"x"),
        LuaString(b"y"),
        LuaString(b"z"),
    ]


def test_rename_args_invalid_number():
    with pytest.raises(ValueError) as excinfo:
        @lua_function(rename_args=["x", "y"])
        def f(a, b, c, /):
            return None

    assert excinfo.type is ValueError
    assert "scope parameter" not in str(excinfo.value)


def test_rename_args_invalid_number_with_scope():
    with pytest.raises(ValueError) as excinfo:
        @lua_function(rename_args=["x", "y"], gets_scope=True)
        def f(scope, a, b, c, /):
            return None

    assert excinfo.type is ValueError
    assert "scope parameter" in str(excinfo.value)


def test_unknown_name():
    def f(a, /):
        return None
    f.__name__ = ""

    f = lua_function()(f)

    assert f.name
    assert "native" in f.name
    assert "function" in f.name


def test_preserve():
    t = LuaTable()

    @lua_function(table=t, preserve=True, wrap_values=True)
    def f():
        return None

    assert not isinstance(f, LuaFunction)
    assert callable(f)
    t_f = t.get(LuaString(b"f"))
    assert isinstance(t_f, LuaFunction)
