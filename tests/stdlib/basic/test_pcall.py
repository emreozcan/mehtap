from ay.__main__ import work_chunk
from ay.util.py_lua_function import lua_function, PyLuaRet
from ay.values import LuaObject, LuaString, Variable, LuaBool
from ay.vm import VirtualMachine


def test_pcall_false():
    vm = VirtualMachine()

    symbol = LuaObject()
    vm.put_nonlocal(LuaString(b"symbol"), Variable(symbol))

    results = work_chunk("""
        return pcall(error, symbol)
    """, vm)

    assert results[0] == LuaBool(False)
    assert results[1] is symbol


def test_pcall_true():
    vm = VirtualMachine()

    symbol = LuaObject()
    vm.put_nonlocal(LuaString(b"symbol"), Variable(symbol))

    @lua_function(vm.globals_)
    def succeed(t) -> PyLuaRet:
        return [t]

    results = work_chunk("""
        return pcall(succeed, symbol)
    """, vm)

    assert results[0] == LuaBool(True)
    assert results[1] is symbol

