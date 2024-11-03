import os
from collections.abc import Sequence
from io import BytesIO

from mehtap.library.stdlib.io_library import LuaFile
from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_input_filename(tmp_path):
    os.chdir(tmp_path)
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.touch()
    vm.exec(f"io.input({str(test_file_path)!r})")
    assert vm.default_input.name == bytes(test_file_path)


def test_input_filehandle(tmp_path):
    os.chdir(tmp_path)
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.touch()
    test_file = open(test_file_path, "rb")
    vm.put_nonlocal_ls(LuaString(b"handle"), LuaFile(test_file))
    vm.exec(f"io.input(handle)")
    assert vm.default_input is test_file


def test_input_empty():
    vm = VirtualMachine()
    vm.default_input = BytesIO()
    r = vm.exec("io.input()")
    assert isinstance(r, Sequence)
    assert isinstance(r[0], LuaFile)
    assert r[0].io == vm.default_input
