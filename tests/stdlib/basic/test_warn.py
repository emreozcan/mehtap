from ay.__main__ import work_chunk
from ay.util.py_lua_function import lua_function, PyLuaRet
from ay.values import LuaObject, LuaString, Variable, LuaBool, LuaTable
from ay.vm import VirtualMachine


def test_warn_disabled(capsys):
    work_chunk("""
        warn("@off")
        print("hello")
        warn("hello")
        print("world")
        warn("world")
    """, VirtualMachine())
    captured = capsys.readouterr()
    assert captured.out == "hello\nworld\n"


def test_warn_enabled(capsys):
    work_chunk("""
        warn("@on")
        print("hello")
        warn("hello")
        print("world")
        warn("world")
    """, VirtualMachine())
    captured = capsys.readouterr()

    lines = captured.out.splitlines()
    assert len(lines) == 4
    assert lines[0] == "hello"
    assert "hello" in lines[1]
    assert lines[2] == "world"
    assert "world" in lines[2]
