from ay.__main__ import work_chunk
from ay.values import LuaNil, LuaTable, LuaString, Variable
from ay.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return work_chunk(program, vm)


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

    (recvd_mt,) = work_chunk(
        """
        return getmetatable(example_table)
    """,
        vm,
    )

    assert recvd_mt is source_mt


def test_getmetatable_meta_metatable():
    vm = VirtualMachine()

    source_object = LuaTable()

    metatable = LuaTable()
    metatable.put(LuaString(b"__metatable"), source_object)
    table = LuaTable()
    table.set_metatable(metatable)
    vm.put_nonlocal_ls(LuaString(b"example_table"), Variable(table))

    (recvd_object,) = work_chunk(
        """
        return getmetatable(example_table)
    """,
        vm,
    )

    assert recvd_object is source_object
