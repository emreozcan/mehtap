from io import BytesIO

import pytest

from ay.control_structures import LuaError
from ay.values import LuaString, LuaNil
from ay.vm import VirtualMachine


def test_lines_default_input():
    input_file = BytesIO(b"abc\ndef\nghi\n")
    vm = VirtualMachine()
    vm.default_input = input_file
    vm.exec("iterator_function, nil1, nil2, fh = io.lines()")
    assert vm.get_ls(LuaString(b"fh")).io is input_file
    assert vm.get_ls(LuaString(b"nil1")) is LuaNil
    assert vm.get_ls(LuaString(b"nil2")) is LuaNil
    assert vm.exec("iterator_function()") == [LuaString(b"abc")]
    assert vm.exec("iterator_function()") == [LuaString(b"def")]
    assert vm.exec("iterator_function()") == [LuaString(b"ghi")]
    assert vm.exec("iterator_function()") == [LuaNil]
    assert vm.exec("iterator_function()") == [LuaNil]
    assert not vm.default_input.closed


def test_lines_file_input(tmp_path):
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm = VirtualMachine()
    vm.exec(
        f"iterator_function, nil1, nil2, fh = io.lines({str(test_file_path)!r})"
    )
    fh = vm.get_ls(LuaString(b"fh"))
    assert fh.io.name == bytes(test_file_path)
    assert vm.get_ls(LuaString(b"nil1")) is LuaNil
    assert vm.get_ls(LuaString(b"nil2")) is LuaNil
    assert vm.exec("iterator_function()") == [LuaString(b"abc")]
    assert vm.exec("iterator_function()") == [LuaString(b"def")]
    assert vm.exec("iterator_function()") == [LuaString(b"ghi")]
    assert not fh.io.closed
    assert vm.exec("iterator_function()") == [LuaNil]
    assert fh.io.closed
    with pytest.raises(LuaError):
        assert vm.exec("iterator_function()") == [LuaNil]
    assert fh.io.closed
    assert test_file_path.exists()
    assert test_file_path.read_bytes() == b"abc\ndef\nghi\n"
