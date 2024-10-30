from ay.py2lua import lua_function, PyLuaRet
from ay.values import LuaString, Variable, LuaBool, LuaTable
from ay.vm import VirtualMachine


def test_pcall_false():
    vm = VirtualMachine()

    symbol = LuaTable()
    vm.put_nonlocal_ls(LuaString(b"symbol"), Variable(symbol))

    results = vm.exec(
        """
        return pcall(error, symbol)
    """,
    )

    assert results[0] == LuaBool(False)
    assert results[1] is symbol


def test_pcall_true():
    vm = VirtualMachine()

    symbol = LuaTable()
    vm.put_nonlocal_ls(LuaString(b"symbol"), Variable(symbol))

    @lua_function(vm.globals)
    def succeed(t, /) -> PyLuaRet:
        return [t]

    results = vm.exec("return pcall(succeed, symbol)")

    assert results[0] == LuaBool(True)
    assert results[1] is symbol
