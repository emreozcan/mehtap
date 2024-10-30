from pytest import raises

from ay.control_structures import LuaError
from ay.values import LuaString, Variable, LuaTable
from ay.vm import VirtualMachine


def test_error():
    vm = VirtualMachine()

    symbol = LuaTable()
    vm.put_nonlocal_ls(LuaString(b"symbol"), Variable(symbol))

    with raises(LuaError) as excinfo:
        vm.eval("error(symbol)")
    assert excinfo.value.message is symbol
