from pytest import raises

from ay.__main__ import work_chunk
from ay.control_structures import LuaError
from ay.operations import str_to_lua_string
from ay.values import LuaBool, LuaNil, LuaNumber
from ay.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return work_chunk(program, vm)


def test_assert_fail_simple():
    with raises(LuaError) as excinfo:
        execute(
            """
            return assert(false)
        """
        )
    assert excinfo.value.message == str_to_lua_string("assertion failed!")


def test_assert_fail_with_message():
    with raises(LuaError) as excinfo:
        execute(
            """
            return assert(false, "message")
        """
        )
    assert excinfo.value.message == str_to_lua_string("message")


def test_assert_success():
    assert (
        execute(
            """
        return assert(true)
    """
        )
        == [LuaBool(True), LuaNil]
    )

    assert (
        execute(
            """
        return assert(true, 1)
    """
        )
        == [LuaBool(True), LuaNumber(1)]
    )

    assert (
        execute(
            """
        return assert(true, 1, 2)
    """
        )
        == [LuaBool(True), LuaNumber(1), LuaNumber(2)]
    )
