from pytest import raises

from mehtap.control_structures import LuaError
from mehtap.values import LuaString, Variable, LuaTable
from mehtap.vm import VirtualMachine


def test_error():
    vm = VirtualMachine()

    symbol = LuaTable()
    vm.put_nonlocal_ls(LuaString(b"symbol"), Variable(symbol))

    with raises(LuaError) as excinfo:
        vm.eval("error(symbol)")
    assert excinfo.value.message is symbol
