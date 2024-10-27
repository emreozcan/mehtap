from pytest import raises

from ay.__main__ import work_chunk
from ay.control_structures import LuaError
from ay.values import LuaString, LuaNil
from ay.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return work_chunk(program, vm)


def test_setmetatable_protected():
    vm = VirtualMachine()
    work_chunk("""
        mt = {__metatable = "hello"}
        t = {}
        setmetatable(t, mt)
    """, vm)

    with raises(LuaError) as excinfo:
        work_chunk("""
            setmetatable(t, mt)
        """, vm)
    assert "protected metatable" in str(excinfo.value.message)


def test_setmetatable_clear():
    vm = VirtualMachine()
    t, = work_chunk("""
        mt = {hello = "hello"}
        t = {}
        return setmetatable(t, mt)
    """, vm)

    assert t.get_metamethod(LuaString(b"hello")) == LuaString(b"hello")

    t, = work_chunk("""
        return setmetatable(t, nil)
    """, vm)
    assert t.get_metatable() is LuaNil


def test_setmetatable_clear_protected():
    vm = VirtualMachine()
    t, = work_chunk("""
        mt = {__metatable = "hello"}
        t = {}
        return setmetatable(t, mt)
    """, vm)

    assert t.get_metatable() is not LuaNil

    with raises(LuaError) as excinfo:
        work_chunk("""
            return setmetatable(t, nil)
        """, vm)
    assert "protected metatable" in str(excinfo.value.message)
    assert t.get_metatable() is not LuaNil

