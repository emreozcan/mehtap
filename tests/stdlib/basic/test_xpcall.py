from mehtap.py2lua import lua_function, PyLuaRet
from mehtap.values import LuaString, Variable, LuaBool, LuaTable
from mehtap.vm import VirtualMachine


def test_xpcall_false():
    vm = VirtualMachine()

    initial_symbol = LuaTable()
    vm.put_nonlocal_ls(LuaString(b"symbol"), Variable(initial_symbol))

    handled_symbol = LuaTable()

    @lua_function
    def handler(s, /) -> PyLuaRet:
        assert s is initial_symbol
        return [handled_symbol]
    vm.put_nonlocal_ls(LuaString(b"handler"), Variable(handler))

    results = vm.exec("return xpcall(error, handler, symbol)")

    assert results[0] == LuaBool(False)
    assert results[1] is handled_symbol


def test_xpcall_true():
    vm = VirtualMachine()

    @lua_function
    def succeed(t, /) -> PyLuaRet:
        return [t]
    vm.put_nonlocal_ls(LuaString(b"succeed"), Variable(succeed))

    initial_symbol = LuaTable()
    vm.put_nonlocal_ls(LuaString(b"symbol"), Variable(initial_symbol))

    handled_symbol = LuaTable()

    @lua_function
    def handler(s, /) -> PyLuaRet:
        assert s is initial_symbol
        return [handled_symbol]
    vm.put_nonlocal_ls(LuaString(b"handler"), Variable(handler))

    results = vm.exec("return xpcall(succeed, handler, symbol)")

    assert results[0] == LuaBool(True)
    assert results[1] is initial_symbol
