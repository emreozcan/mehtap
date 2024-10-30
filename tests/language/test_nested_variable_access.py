from ay.operations import str_to_lua_string
from ay.py2lua import py2lua
from ay.values import LuaTable, LuaFunction
from ay.vm import VirtualMachine


def test_nested_variable_read():
    vm = VirtualMachine()

    vm.put_nonlocal_ls(
        str_to_lua_string("a"),
        py2lua({
            "b": {
                "c": lambda: "foo"
            }
        })
    )

    a, = vm.eval("a")
    assert isinstance(a, LuaTable)

    b, = vm.eval("a.b")
    assert isinstance(b, LuaTable)

    c, = vm.eval("a.b.c")
    assert isinstance(c, LuaFunction)
