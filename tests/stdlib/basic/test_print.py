from ay.__main__ import work_chunk
from ay.util.py_lua_function import lua_function, PyLuaRet
from ay.values import LuaObject, LuaString, Variable, LuaBool, LuaTable
from ay.vm import VirtualMachine


def test_print_one_string(capsys):
    work_chunk('print("hello")', VirtualMachine())
    captured = capsys.readouterr()
    assert captured.out == "hello\n"


def test_print_tostring(capsys):
    vm = VirtualMachine()

    lua_object = LuaObject()
    lua_object.set_metatable(LuaTable({
        LuaString(b"__tostring"): lua_function()(lambda _: [LuaString(b";)")])
    }))

    vm.put_nonlocal(LuaString(b"mystery"), Variable(lua_object))

    work_chunk('print(mystery)', vm)
    captured = capsys.readouterr()
    assert captured.out == ";)\n"

