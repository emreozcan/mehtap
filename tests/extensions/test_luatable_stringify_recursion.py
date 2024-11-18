from mehtap.py2lua import py2lua
from mehtap.values import LuaTable


def get_infinite_luatable():
    turtle = LuaTable()
    turtle.rawput(py2lua("turtle"), turtle)
    return turtle


def test_not_crash():
    # If this test doesn't crash, it passes.
    turtle = get_infinite_luatable()
    str(turtle)
    repr(turtle)
