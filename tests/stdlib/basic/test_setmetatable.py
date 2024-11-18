from pytest import raises

from mehtap.control_structures import LuaError
from mehtap.values import LuaString, LuaNil
from mehtap.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return vm.exec(program)


def test_setmetatable_protected():
    vm = VirtualMachine()
    vm.exec(
        """
            mt = {__metatable = "hello"}
            t = {}
            setmetatable(t, mt)
        """,
    )

    with raises(LuaError) as excinfo:
        vm.exec(
            """
                setmetatable(t, mt)
            """,
        )
    assert "protected metatable" in str(excinfo.value.message)


def test_setmetatable_clear():
    vm = VirtualMachine()
    (t,) = vm.exec(
        """
            mt = {hello = "hello"}
            t = {}
            return setmetatable(t, mt)
        """,
    )

    assert t.get_metavalue(LuaString(b"hello")) == LuaString(b"hello")

    (t,) = vm.exec(
        """
            return setmetatable(t, nil)
        """,
    )
    assert t.get_metatable() is LuaNil


def test_setmetatable_clear_protected():
    vm = VirtualMachine()
    (t,) = vm.exec(
        """
            mt = {__metatable = "hello"}
            t = {}
            return setmetatable(t, mt)
        """,
    )

    assert t.get_metatable() is not LuaNil

    with raises(LuaError) as excinfo:
        vm.exec(
            """
                return setmetatable(t, nil)
            """,
        )
    assert "protected metatable" in str(excinfo.value.message)
    assert t.get_metatable() is not LuaNil
