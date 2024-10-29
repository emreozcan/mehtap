from ay.__main__ import work_chunk
from ay.util.py_lua_function import lua_function
from ay.values import LuaString, Variable, LuaTable, LuaNumber
from ay.vm import VirtualMachine


class CallTracker:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)


def test_ipairs():
    vm = VirtualMachine()

    tracker = CallTracker()

    @lua_function(vm.globals, name="f")
    def f(*a):
        tracker(*a)

    table = LuaTable(
        {
            LuaNumber(k): LuaString(v.encode("utf-8"))
            for k, v in enumerate(["a", "b", "c", "d", "e"], start=1)
        }
    )
    table.put(LuaNumber(7), LuaString(b"g"))
    vm.put_nonlocal_ls(LuaString(b"t"), Variable(table))

    assert (
        work_chunk(
            """
        for i, v in ipairs(t) do
            f(i, v)
        end
    """,
            vm,
        )
        == []
    )

    assert tracker.calls == [
        (LuaNumber(1), LuaString(b"a")),
        (LuaNumber(2), LuaString(b"b")),
        (LuaNumber(3), LuaString(b"c")),
        (LuaNumber(4), LuaString(b"d")),
        (LuaNumber(5), LuaString(b"e")),
    ]
