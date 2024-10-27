from ay.__main__ import work_chunk
from ay.values import LuaString, LuaThread, Variable, LuaUserdata
from ay.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return work_chunk(program, vm)


def test_type_nil():
    assert execute("return type(nil)") == [LuaString(b"nil")]


def test_type_number():
    assert execute("return type(1)") == [LuaString(b"number")]
    assert execute("return type(1.5)") == [LuaString(b"number")]


def test_type_string():
    assert execute("return type('a')") == [LuaString(b"string")]


def test_type_boolean():
    assert execute("return type(true)") == [LuaString(b"boolean")]
    assert execute("return type(false)") == [LuaString(b"boolean")]


def test_type_table():
    assert execute("return type({})") == [LuaString(b"table")]


def test_type_function():
    assert execute(
        "return type(function() return 1 end)"
    ) == [LuaString(b"function")]


def test_type_thread():
    vm = VirtualMachine()
    vm.put_nonlocal(LuaString(b"coro"), Variable(LuaThread()))
    assert work_chunk("return type(coro)", vm) == [LuaString(b"thread")]


def test_type_userdata():
    vm = VirtualMachine()
    vm.put_nonlocal(LuaString(b"ud"), Variable(LuaUserdata()))
    assert work_chunk("return type(ud)", vm) == [LuaString(b"userdata")]
