import pytest

from mehtap import VirtualMachine, LuaNil
from mehtap.control_structures import LuaError
from mehtap.py2lua import py2lua


def test_table_insert_simple():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 2, 3, 4, 5}
    table.insert(t, 6)
    return t[6]
    """
    result = vm.exec(lua_code)
    assert result == [py2lua(6)]


def test_table_insert_at_beginning():
    vm = VirtualMachine()
    lua_code = """
    local t = {2, 3, 4, 5}
    table.insert(t, 1, 1)
    return t[1]
    """
    result = vm.exec(lua_code)
    assert result == [py2lua(1)]


def test_table_insert_at_middle():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 3, 4, 5}
    table.insert(t, 2, 2)
    return t[2]
    """
    result = vm.exec(lua_code)
    assert result == [py2lua(2)]


def test_table_insert_at_end():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 2, 3, 4}
    table.insert(t, 5, 5)
    return t[5]
    """
    result = vm.exec(lua_code)
    assert result == [py2lua(5)]


def test_table_insert_in_middle_with_existing_index():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 2, 4, 5}
    table.insert(t, 3, 3)
    return t[3]
    """
    result = vm.exec(lua_code)
    assert result == [py2lua(3)]


def test_table_insert_with_invalid_index():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 2, 3}
    table.insert(t, 5, 4)
    return t[5]
    """
    with pytest.raises(LuaError) as excinfo:
        vm.exec(lua_code)
    assert "bad argument #2 to 'insert'" in str(excinfo.value)
    assert "position out of bounds" in str(excinfo.value)


def test_table_insert_with_non_number_index():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 2, 3}
    table.insert(t, "not_a_number", 4)
    """
    with pytest.raises(LuaError) as excinfo:
        vm.exec(lua_code)
    assert "bad argument #2 to 'insert' (number expected, got string)" in str(excinfo.value)


def test_table_insert_with_nil_value():
    vm = VirtualMachine()
    lua_code = """
    local t = {1, 2, 3}
    table.insert(t, nil)
    return t[4]
    """
    result = vm.exec(lua_code)
    assert result == [LuaNil]
