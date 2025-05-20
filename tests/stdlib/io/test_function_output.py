import os
from collections.abc import Sequence
from io import BytesIO

from mehtap.library.stdlib.io_library import LuaFile
from mehtap.values import LuaString, Variable
from mehtap.vm import VirtualMachine


def test_output_filename(tmp_path):
    os.chdir(tmp_path)
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.touch()
    vm.exec(f"io.output({str(test_file_path)!r})")
    assert vm.default_output.name == bytes(test_file_path)


def test_output_filehandle(tmp_path):
    os.chdir(tmp_path)
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.touch()
    test_file = open(test_file_path, "rb")
    vm.put_nonlocal_ls(LuaString(b"handle"), Variable(LuaFile(test_file)))
    vm.exec(f"io.output(handle)")
    assert vm.default_output is test_file


def test_output_empty():
    vm = VirtualMachine()
    vm.default_output = BytesIO()
    r = vm.eval("io.output()")
    assert isinstance(r, Sequence)
    assert isinstance(r[0], LuaFile)
    assert r[0].io == vm.default_output
