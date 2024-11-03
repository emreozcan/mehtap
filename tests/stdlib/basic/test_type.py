from mehtap.values import LuaString, LuaThread, Variable, LuaUserdata
from mehtap.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return vm.exec(program)


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
    assert execute("return type(function() return 1 end)") == [
        LuaString(b"function")
    ]


def test_type_thread():
    vm = VirtualMachine()
    vm.put_nonlocal_ls(LuaString(b"coro"), Variable(LuaThread()))
    assert vm.exec("return type(coro)") == [LuaString(b"thread")]


def test_type_userdata():
    vm = VirtualMachine()
    vm.put_nonlocal_ls(LuaString(b"ud"), Variable(LuaUserdata()))
    assert vm.exec("return type(ud)") == [LuaString(b"userdata")]
