from mehtap.py2lua import lua_function
from mehtap.values import LuaString, Variable, LuaTable, LuaNumber
from mehtap.vm import VirtualMachine


class CallTracker:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)


def test_ipairs():
    vm = VirtualMachine()

    tracker = CallTracker()

    @lua_function
    def f(*a):
        tracker(*a)
    vm.put_nonlocal_ls(LuaString(b"f"), Variable(f))

    table = LuaTable(
        {
            LuaNumber(k): LuaString(v.encode("utf-8"))
            for k, v in enumerate(["a", "b", "c", "d", "e"], start=1)
        }
    )
    table.rawput(LuaNumber(7), LuaString(b"g"))
    vm.put_nonlocal_ls(LuaString(b"t"), Variable(table))

    vm.exec(
        """
            for i, v in ipairs(t) do
                f(i, v)
            end
        """,
    )

    assert tracker.calls == [
        (LuaNumber(1), LuaString(b"a")),
        (LuaNumber(2), LuaString(b"b")),
        (LuaNumber(3), LuaString(b"c")),
        (LuaNumber(4), LuaString(b"d")),
        (LuaNumber(5), LuaString(b"e")),
    ]
