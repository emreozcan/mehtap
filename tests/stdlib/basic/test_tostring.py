from mehtap.py2lua import lua_function
from mehtap.values import LuaTable, LuaString, Variable, LuaValue
from mehtap.vm import VirtualMachine


def test_tostring_mt_tostring():
    lua_object = LuaTable()

    called = [False]

    @lua_function()
    def callback(o: LuaValue, /):
        called[0] = True
        return LuaString(b"yay :D")

    mt = LuaTable(
        {
            LuaString(b"__tostring"): callback,
        }
    )
    lua_object.set_metatable(mt)

    vm = VirtualMachine()
    vm.put_nonlocal_ls(LuaString(b"o"), Variable(lua_object))

    (lua_string,) = vm.exec(
        """
            return tostring(o)
        """,
    )

    assert lua_string == LuaString(b"yay :D")
    assert called[0]


def test_tostring_mt_name():
    lua_object = LuaTable()

    mt = LuaTable(
        {
            LuaString(b"__name"): LuaString(b"my_object"),
        }
    )
    lua_object.set_metatable(mt)

    vm = VirtualMachine()
    vm.put_nonlocal_ls(LuaString(b"o"), Variable(lua_object))

    (lua_string,) = vm.exec(
        """
            return tostring(o)
        """,
    )

    assert b"my_object" in lua_string.content
