import pytest

from ay.py2lua import py2lua, PyLuaRet
from ay.values import LuaBool, LuaNil, LuaNumber, LuaNumberType, LuaString


def test_nil():
    assert py2lua(None) == LuaNil


def test_protocol():
    class CustomClass:
        def __lua__(self) -> LuaNumber:
            return LuaNumber(42)

    assert py2lua(CustomClass()) == LuaNumber(42)


def test_booleans():
    assert py2lua(True) == LuaBool(True)
    assert py2lua(False) == LuaBool(False)


def test_numbers():
    _42 = py2lua(42)
    assert _42 == LuaNumber(42)
    assert _42.type == LuaNumberType.INTEGER

    _42_0 = py2lua(42.0)
    assert _42_0 == LuaNumber(42.0)
    assert _42_0.type == LuaNumberType.FLOAT


def test_strings():
    assert py2lua("hello") == LuaString(b"hello")


def test_bytes():
    assert py2lua(b"hello") == LuaString(b"hello")


def test_mappings():
    country_codes = {"US": "United States", "CA": "Canada"}

    lua_table = py2lua(country_codes)

    assert lua_table.get(LuaString(b"US")) == LuaString(b"United States")
    assert lua_table.get(LuaString(b"CA")) == LuaString(b"Canada")


def test_iterables():
    numbers = [200, 500, 900]

    lua_table = py2lua(numbers)

    assert lua_table.get(LuaNumber(1)) == LuaNumber(200)
    assert lua_table.get(LuaNumber(2)) == LuaNumber(500)
    assert lua_table.get(LuaNumber(3)) == LuaNumber(900)


def test_callables():
    def add(a, b, /):
        assert isinstance(a, int)
        assert isinstance(b, int)
        return a + b

    lua_function = py2lua(add)

    assert lua_function.call(
        [LuaNumber(1), LuaNumber(2)],
        None
    ) == [LuaNumber(3)]
    assert lua_function.call(
        [LuaNumber(3), LuaNumber(4)],
        None
    ) == [LuaNumber(7)]
    assert lua_function.call(
        [LuaNumber(5), LuaNumber(6)],
        None
    ) == [LuaNumber(11)]


def test_recursive():
    a = {}
    a["a"] = a
    lua_table = py2lua(a)
    assert lua_table.get(LuaString(b"a")) is lua_table


def test_unknown():
    class X:
        pass
    with pytest.raises(TypeError) as excinfo:
        py2lua(X())
    assert isinstance(excinfo.value, TypeError)
