from ay.__main__ import work_chunk
from ay.util.py_lua_function import lua_function, PyLuaRet
from ay.values import LuaString, Variable, LuaBool, LuaTable
from ay.vm import VirtualMachine


def test_xpcall_false():
    vm = VirtualMachine()

    initial_symbol = LuaTable()
    vm.put_nonlocal(LuaString(b"symbol"), Variable(initial_symbol))

    handled_symbol = LuaTable()

    @lua_function(vm.globals)
    def handler(s, /) -> PyLuaRet:
        assert s is initial_symbol
        return [handled_symbol]

    results = work_chunk(
        """
        return xpcall(error, handler, symbol)
    """,
        vm,
    )

    assert results[0] == LuaBool(False)
    assert results[1] is handled_symbol


def test_xpcall_true():
    vm = VirtualMachine()

    @lua_function(vm.globals)
    def succeed(t, /) -> PyLuaRet:
        return [t]

    initial_symbol = LuaTable()
    vm.put_nonlocal(LuaString(b"symbol"), Variable(initial_symbol))

    handled_symbol = LuaTable()

    @lua_function(vm.globals)
    def handler(s, /) -> PyLuaRet:
        assert s is initial_symbol
        return [handled_symbol]

    results = work_chunk(
        """
        return xpcall(succeed, handler, symbol)
    """,
        vm,
    )

    assert results[0] == LuaBool(True)
    assert results[1] is initial_symbol
