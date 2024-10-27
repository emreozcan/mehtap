from pathlib import Path

from pytest import raises

from ay.__main__ import work_chunk
from ay.control_structures import LuaError
from ay.operations import str_to_lua_string
from ay.values import LuaNumber
from ay.vm import VirtualMachine


def execute(program):
    vm = VirtualMachine()
    return work_chunk(program, vm)


def path_of_this_file():
    return Path(__file__)


def test_dofile_success():
    filename = path_of_this_file().parent / "test_dofile_values.lua"
    assert execute(f"""
        return dofile({str(filename)!r})
    """) == [LuaNumber(42), LuaNumber(-42)]


def test_dofile_error():
    filename = path_of_this_file().parent / "test_dofile_error.lua"
    with raises(LuaError) as excinfo:
        execute(f"""
            return dofile({str(filename)!r})
        """)

    assert excinfo.value.message == str_to_lua_string("i am in another file")
