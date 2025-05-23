from mehtap.lua2py import lua2py
from mehtap.py2lua import lua_function, PyLuaRet
from mehtap.values import LuaTable, LuaString, LuaNil, LuaBool, LuaNumber


def test_recursive():
    t = LuaTable()
    t.rawput(LuaString(b"t"), t)

    d = lua2py(t)
    assert d["t"] is d


def test_nil():
    assert lua2py(LuaNil) is None


def test_bool():
    assert lua2py(LuaBool(True)) is True
    assert lua2py(LuaBool(False)) is False


def test_number():
    int_42 = lua2py(LuaNumber(42))
    assert isinstance(int_42, int)
    assert int_42 == 42
    float_42 = lua2py(LuaNumber(42.0))
    assert isinstance(float_42, float)
    assert float_42 == 42.0


def test_string():
    assert lua2py(LuaString(b"hello")) == "hello"


def test_table():
    t = LuaTable()
    t.rawput(LuaString(b"hello"), LuaString(b"world"))

    d = lua2py(t)
    assert d == {"hello": "world"}


def test_table_metamethod():
    t = LuaTable()
    mt = LuaTable()
    t.set_metatable(mt)

    @lua_function
    def py_function(self, /) -> PyLuaRet:
        return LuaString(b"hello")

    mt.rawput(LuaString(b"__py"), py_function)

    d = lua2py(t)
    assert d == "hello"


def test_function():
    @lua_function(wrap_values=True)
    def lua_f(a: int, b: int, /) -> int:
        return a + b

    py_f = lua2py(lua_f)
    assert py_f(1, 2) == [3]
    assert py_f(3, 4) == [7]
