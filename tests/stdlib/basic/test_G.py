from mehtap.values import LuaTable, LuaNumber, LuaString
from mehtap.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return vm.exec(program)


def test_global():
    (table,) = execute(
        """
        x = 1
        return _G
    """
    )
    assert isinstance(table, LuaTable)
    x = LuaString(b"x")
    assert table.has(x)
    assert table.rawget(x) == LuaNumber(1)
