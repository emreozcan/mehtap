from _pytest.python_api import raises

from ay.__main__ import work_chunk
from ay.control_structures import LuaError
from ay.values import LuaNumber
from ay.vm import VirtualMachine


def execute(chunk):
    vm = VirtualMachine()
    return work_chunk(chunk, vm)


def test_select_positive():
    assert (
        execute(
            """
        return select(6, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    """
        )
        == [LuaNumber(x) for x in [6, 7, 8, 9, 10]]
    )


def test_select_negative():
    assert (
        execute(
            """
        return select(0-2, 1, 2)
    """
        )
        == [LuaNumber(1), LuaNumber(2)]
    )


def test_select_invalid():
    with raises(LuaError) as excinfo:
        execute("select(0, 1, 2)")
    assert "range" in str(excinfo.value.message)

    with raises(LuaError) as excinfo:
        execute("select(0-3, 1, 2)")
    assert "range" in str(excinfo.value.message)

    with raises(LuaError) as excinfo:
        execute("select('hello', 1, 2)")
    assert "bad argument" in str(excinfo.value.message)


def test_select_count():
    assert (
        execute(
            """
        return select("#", 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    """
        )
        == [LuaNumber(10)]
    )

    assert (
        execute(
            """
        return select("#")
    """
        )
        == [LuaNumber(0)]
    )
