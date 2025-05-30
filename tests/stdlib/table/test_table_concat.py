import pytest

from mehtap import VirtualMachine
from mehtap.control_structures import LuaError
from mehtap.py2lua import py2lua


def test_table_concat_simple():
    vm = VirtualMachine()
    result, = vm.eval("table.concat({1,2,3,4,5})")
    assert result == py2lua("12345")


def test_table_concat_with_separator():
    vm = VirtualMachine()
    result, = vm.eval("table.concat({1,2,3,4,5}, ',')")
    assert result == py2lua("1,2,3,4,5")


def test_table_concat_with_indices():
    vm = VirtualMachine()
    result, = vm.eval("table.concat({1,2,3,4,5}, ',', 2, 4)")
    assert result == py2lua("2,3,4")


def test_table_concat_with_invalid_index():
    vm = VirtualMachine()
    with pytest.raises(LuaError) as excinfo:
        vm.eval("table.concat({1,2,3,4,5}, ',', 6, 10)")
    assert "invalid value (nil) at index 6 in table for 'concat'" in str(excinfo.value)


def test_table_concat_with_non_string_elements():
    vm = VirtualMachine()
    with pytest.raises(LuaError) as excinfo:
        vm.eval("table.concat({1, 2, {}, 4}, ',')")
    assert "invalid value (table) at index 3 in table for 'concat'" in str(excinfo.value)


def test_table_concat_with_empty_table():
    vm = VirtualMachine()
    result, = vm.eval("table.concat({})")
    assert result == py2lua("")
