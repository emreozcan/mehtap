from ay.__main__ import work_expr
from ay.operations import str_to_lua_string
from ay.util.py_lua_function import py_to_lua
from ay.values import LuaTable, LuaFunction
from ay.vm import VirtualMachine


def test_nested_variable_read():
    vm = VirtualMachine()

    vm.put_nonlocal_ls(
        str_to_lua_string("a"),
        py_to_lua({
            "b": {
                "c": lambda: "foo"
            }
        })
    )

    a, = work_expr("a", vm)
    assert isinstance(a, LuaTable)

    b, = work_expr("a.b", vm)
    assert isinstance(b, LuaTable)

    c, = work_expr("a.b.c", vm)
    assert isinstance(c, LuaFunction)
