from io import SEEK_SET

import pytest

from ay.control_structures import LuaError
from ay.library.stdlib.io_library import LuaFile
from ay.values import LuaString
from ay.vm import VirtualMachine


def test_seek_set(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r')")
    vm.exec("fh:seek('set', 5)")
    r = vm.exec("return fh:read('l')")
    assert r == [LuaString(b"ef")]


def test_seek_cur(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r')")
    vm.get_ls(LuaString(b"fh")).io.seek(3, SEEK_SET)
    vm.exec("fh:seek('cur', 5)")
    r = vm.exec("return fh:read('l')")
    assert r == [LuaString(b"ghi")]


def test_seek_end(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r')")
    vm.exec("fh:seek('end', -8)")
    r = vm.exec("return fh:read('a')")
    assert r == [LuaString(b"def\nghi\n")]


def test_seek_invalid_whence(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.touch()
    file_handle = LuaFile(test_file_path.open("rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), file_handle)
    with pytest.raises(LuaError) as excinfo:
        vm.exec("fh:seek('blablabla', -8)")
    assert isinstance(excinfo.value, LuaError)
    assert isinstance(excinfo.value.message, LuaString)
    assert b"invalid whence" in excinfo.value.message.content
