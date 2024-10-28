from ay.__main__ import work_expr
from ay.util.py_lua_function import lua_function
from ay.values import LuaObject, LuaTable, LuaString, Variable, LuaNumber
from ay.vm import VirtualMachine


@lua_function()
def fail():
    assert False


def get_vm(m1: dict | None = None, m2: dict | None = None):
    vm = VirtualMachine()

    mt = LuaTable(
        {
            LuaString(b"__eq"): fail,
            LuaString(b"__index"): fail,
            LuaString(b"__len"): fail,
            LuaString(b"__newindex"): fail,
        }
    )

    o1 = LuaTable(m1 if m1 is not None else {})
    o1.set_metatable(mt)
    o2 = LuaTable(m2 if m2 is not None else {})
    o2.set_metatable(mt)

    vm.put_nonlocal(LuaString(b"o1"), Variable(o1))
    vm.put_nonlocal(LuaString(b"o2"), Variable(o2))

    return vm


def test_rawequal():
    assert work_expr("rawequal(o1, o2)", get_vm())


def test_rawget():
    obj = LuaObject()
    assert work_expr("rawget(o1, 1)", get_vm({LuaNumber(1): obj}))[0] is obj


def test_rawlen():
    assert work_expr("rawlen(o1)", get_vm({LuaNumber(1): LuaObject()})) == [
        LuaNumber(1)
    ]


def test_rawset():
    obj = LuaObject()
    vm = get_vm(m2={LuaNumber(1): obj})
    work_expr(
        "rawset(o1, 1, o2[1])",
        vm,
    )
    assert vm.get(LuaString(b"o1")).get(LuaNumber(1)) is obj
