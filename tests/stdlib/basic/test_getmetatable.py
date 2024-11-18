from mehtap.values import LuaNil, LuaTable, LuaString, Variable
from mehtap.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return vm.exec(program)


def test_getmetatable_no_mt():
    assert (
        execute(
            """
        return getmetatable(1)
    """
        )
        == [LuaNil]
    )


def test_getmetatable_yes_mt():
    vm = VirtualMachine()

    source_mt = LuaTable()
    table = LuaTable()
    table.set_metatable(source_mt)
    vm.put_nonlocal_ls(LuaString(b"example_table"), Variable(table))

    (recvd_mt,) = vm.eval("getmetatable(example_table)")

    assert recvd_mt is source_mt


def test_getmetatable_meta_metatable():
    vm = VirtualMachine()

    source_object = LuaTable()

    metatable = LuaTable()
    metatable.rawput(LuaString(b"__metatable"), source_object)
    table = LuaTable()
    table.set_metatable(metatable)
    vm.put_nonlocal_ls(LuaString(b"example_table"), Variable(table))

    (recvd_object,) = vm.eval("getmetatable(example_table)")

    assert recvd_object is source_object
