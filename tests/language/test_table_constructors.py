from mehtap.values import LuaTable, LuaNumber, LuaString
from mehtap.vm import VirtualMachine


def test_fields_with_keys():
    vm = VirtualMachine()
    t, = vm.eval(
        """
        {
            [0+1] = "one",
            [1+1] = "two",
            [2+1] = "three",
            ["fo".."ur"] = "4",
        }
        """
    )
    assert isinstance(t, LuaTable)
    assert t.rawget(LuaNumber(1)) == LuaString(b"one")
    assert t.rawget(LuaNumber(2)) == LuaString(b"two")
    assert t.rawget(LuaNumber(3)) == LuaString(b"three")
    assert t.rawget(LuaString(b"four")) == LuaString(b"4")


def test_fields_counter():
    vm = VirtualMachine()
    t, = vm.eval(
        """
        {
            "one",
            "two",
            "three",
            "4",
        }
        """
    )
    assert isinstance(t, LuaTable)
    assert t.rawget(LuaNumber(1)) == LuaString(b"one")
    assert t.rawget(LuaNumber(2)) == LuaString(b"two")
    assert t.rawget(LuaNumber(3)) == LuaString(b"three")
    assert t.rawget(LuaNumber(4)) == LuaString(b"4")


def test_trailing_separator():
    vm = VirtualMachine()
    t, = vm.eval(
        """
        {
            "one",
            "two",
            "three",
            "4",
        }
        """
    )
    assert isinstance(t, LuaTable)
    assert t.rawget(LuaNumber(1)) == LuaString(b"one")
    assert t.rawget(LuaNumber(2)) == LuaString(b"two")
    assert t.rawget(LuaNumber(3)) == LuaString(b"three")
    assert t.rawget(LuaNumber(4)) == LuaString(b"4")


def test_mixed():
    vm = VirtualMachine()
    t, = vm.eval(
        """
        {
            "one";
            "two",
            "three";
            "4",
            ["five"] = "5",
            5,
        }
        """
    )
    assert isinstance(t, LuaTable)
    assert t.rawget(LuaNumber(1)) == LuaString(b"one")
    assert t.rawget(LuaNumber(2)) == LuaString(b"two")
    assert t.rawget(LuaNumber(3)) == LuaString(b"three")
    assert t.rawget(LuaNumber(4)) == LuaString(b"4")
    assert t.rawget(LuaString(b"five")) == LuaString(b"5")
    assert t.rawget(LuaNumber(5)) == LuaNumber(5)

