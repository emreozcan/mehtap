from pytest import raises

from ay.__main__ import work_chunk
from ay.control_structures import LuaError
from ay.values import LuaObject, LuaString, Variable
from ay.vm import VirtualMachine


def test_error():
    vm = VirtualMachine()

    symbol = LuaObject()
    vm.put_nonlocal(LuaString(b"symbol"), Variable(symbol))

    with raises(LuaError) as excinfo:
        work_chunk("""
            return error(symbol)
        """, vm)
    assert excinfo.value.message is symbol
