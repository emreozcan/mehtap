from mehtap.py2lua import lua_function, PyLuaRet
from mehtap.values import LuaString, Variable, LuaBool, LuaTable
from mehtap.vm import VirtualMachine


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

    @lua_function
    def succeed(t, /) -> PyLuaRet:
        return [t]
    vm.put_nonlocal_ls(LuaString(b"succeed"), Variable(succeed))

    results = vm.exec("return pcall(succeed, symbol)")

    assert results[0] == LuaBool(True)
    assert results[1] is symbol
