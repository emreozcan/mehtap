import pytest

from mehtap.control_structures import LuaError
from mehtap.values import LuaNumber
from mehtap.vm import VirtualMachine


def test_length_string():
    vm = VirtualMachine()
    assert vm.exec(
        """
            return #("foo")
        """
    ) == [LuaNumber(3)]


def test_length_table():
    vm = VirtualMachine()
    assert vm.exec(
        """
            return #{}
        """
    ) == [LuaNumber(0)]

    assert vm.exec(
        """
            return #{1, 2, 3}
        """
    ) == [LuaNumber(3)]


def test_length_error():
    vm = VirtualMachine()
    with pytest.raises(LuaError) as excinfo:
        vm.exec(
            """
                return #42
            """
        )

    assert str(excinfo.value) == "attempt to get length of a number value"
