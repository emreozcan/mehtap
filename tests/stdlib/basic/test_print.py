from mehtap.py2lua import lua_function
from mehtap.values import LuaString, Variable, LuaTable
from mehtap.vm import VirtualMachine


def test_print_one_string(capsys):
    VirtualMachine().exec('print("hello")')
    captured = capsys.readouterr()
    assert captured.out == "hello\n"


def test_print_tostring(capsys):
    vm = VirtualMachine()

    lua_object = LuaTable()
    lua_object.set_metatable(
        LuaTable(
            {
                LuaString(b"__tostring"): lua_function()(
                    lambda _, /: [LuaString(b";)")]
                )
            }
        )
    )

    vm.put_nonlocal_ls(LuaString(b"mystery"), Variable(lua_object))

    vm.exec("print(mystery)")
    captured = capsys.readouterr()
    assert captured.out == ";)\n"
