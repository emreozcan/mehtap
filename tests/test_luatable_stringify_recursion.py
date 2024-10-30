from ay.py_to_lua import py_to_lua
from ay.values import LuaTable


def get_infinite_luatable():
    turtle = LuaTable()
    turtle.put(py_to_lua("turtle"), turtle)
    return turtle


def test_not_crash():
    # If this test doesn't crash, it passes.
    turtle = get_infinite_luatable()
    str(turtle)
    repr(turtle)
