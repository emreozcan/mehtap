from ay.__main__ import work_chunk
from ay.util.py_lua_function import lua_function
from ay.values import LuaObject, LuaTable, LuaString, Variable
from ay.vm import VirtualMachine


def test_tostring_mt_tostring():
    lua_object = LuaObject()

    called = [False]

    @lua_function()
    def callback(o: LuaObject):
        called[0] = True
        return LuaString(b"yay :D")

    mt = LuaTable({
        LuaString(b"__tostring"): callback,
    })
    lua_object.set_metatable(mt)

    vm = VirtualMachine()
    vm.put_nonlocal(LuaString(b"o"), Variable(lua_object))

    lua_string, = work_chunk("""
        return tostring(o)
    """, vm)

    assert lua_string == LuaString(b"yay :D")
    assert called[0]


def test_tostring_mt_name():
    lua_object = LuaObject()

    mt = LuaTable({
        LuaString(b"__name"): LuaString(b"my_object"),
    })
    lua_object.set_metatable(mt)

    vm = VirtualMachine()
    vm.put_nonlocal(LuaString(b"o"), Variable(lua_object))

    lua_string, = work_chunk("""
        return tostring(o)
    """, vm)

    assert b"my_object" in lua_string.content
