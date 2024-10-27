from _pytest.python_api import raises

from ay.__main__ import work_chunk
from ay.control_structures import LuaError
from ay.values import LuaNumber
from ay.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return work_chunk(program, vm)


def test_no_base():
    assert execute("return tonumber(1)") == [LuaNumber(1)]
    assert execute("return tonumber(2.5)") == [LuaNumber(2.5)]
    assert execute("return tonumber(\"7.25\")") == [LuaNumber(7.25)]
    assert execute("return tonumber(\"+8.5\")") == [LuaNumber(8.5)]
    assert execute("return tonumber(\"-9.5\")") == [LuaNumber(-9.5)]


def test_base():
    with raises(LuaError):
        assert execute("return tonumber(1, 10)") == [LuaNumber(1)]
    with raises(LuaError):
        assert execute("return tonumber(25, 10)") == [LuaNumber(25)]
    assert execute("return tonumber(\"725\", 10)") == [LuaNumber(725)]
    assert execute("return tonumber(\"+85\", 10)") == [LuaNumber(85)]
    assert execute("return tonumber(\"-95\", 10)") == [LuaNumber(-95)]

    assert execute("return tonumber(\"1\", 16)") == [LuaNumber(1)]
    assert execute("return tonumber(\"19\", 16)") == [LuaNumber(25)]
    assert execute("return tonumber(\"2D5\", 16)") == [LuaNumber(725)]
    assert execute("return tonumber(\"+55\", 16)") == [LuaNumber(85)]
    assert execute("return tonumber(\"-5F\", 16)") == [LuaNumber(-95)]

    assert execute(
        "return tonumber(\"ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ"
        "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ\", 36)",
    ) == [LuaNumber(-1)]
