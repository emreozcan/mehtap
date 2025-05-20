from mehtap.py2lua import lua_function
from mehtap.values import (
    LuaString,
    Variable,
    LuaTable,
    LuaNumber,
    LuaNil,
    LuaBool,
    LuaValue,
)
from mehtap.vm import VirtualMachine


class CallTracker:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)


def to_lua(ob, /) -> LuaValue:
    if isinstance(ob, LuaValue):
        return ob
    if isinstance(ob, str):
        return LuaString(ob.encode("utf-8"))
    if isinstance(ob, (int, float)):
        return LuaNumber(ob)
    if isinstance(ob, bool):
        return LuaBool(ob)
    if ob is None:
        return LuaNil
    raise TypeError(f"unsupported type: {type(ob)}")


def test_ipairs():
    vm = VirtualMachine()

    tracker = CallTracker()

    @lua_function
    def f(*a):
        tracker(*a)
    vm.put_nonlocal_ls(LuaString(b"f"), Variable(f))

    src_map = {
        to_lua(k): to_lua(v)
        for k, v in {
            "a": 1,
            "b": 2,
            "c": 3,
            4: "d",
            5: "e",
            6: "f",
            7.5: "ğ",
        }.items()
    }

    table = LuaTable(src_map.copy())
    vm.put_nonlocal_ls(LuaString(b"t"), Variable(table))

    vm.exec(
        """
            for k, v in pairs(t) do
                f(k, v)
            end
        """,
    )

    assert tracker.calls == [(k, v) for k, v in src_map.items()]
