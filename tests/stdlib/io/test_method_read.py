import pytest

from mehtap.control_structures import LuaError
from mehtap.library.stdlib.io_library import LuaFile
from mehtap.values import LuaString, LuaNumber, LuaNil, Variable
from mehtap.vm import VirtualMachine


def test_format_number(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abcdef\n")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read(5)")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"abcde"
    r = vm.exec(f"return fh:read(5)")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"f\n"


def test_format_number_eof(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abcdef\n")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read(5)")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"abcde"
    r = vm.exec(f"return fh:read(5)")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"f\n"
    r = vm.exec(f"return fh:read(5)")
    assert r[0] is LuaNil


def test_format_n(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"1112.5")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read('n')")
    assert isinstance(r[0], LuaNumber)
    assert r[0].value == 1112.5


def test_format_n_succeed_limit(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"1" + b"0" * 199)
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read('n')")
    assert isinstance(r[0], LuaNumber)
    assert r[0].value == 1e199


def test_format_n_fail_too_long(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"1" * 201)
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read('n')")
    assert r[0] is LuaNil


def test_format_a(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abcdef\n")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read('a')")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"abcdef\n"
    r = vm.exec(f"return fh:read('a')")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b""


def test_format_small_l(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\n")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read('l')")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"abc"
    r = vm.exec(f"return fh:read('l')")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"def"
    r = vm.exec(f"return fh:read('l')")
    assert r[0] is LuaNil


def test_format_big_l(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\n")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    r = vm.exec(f"return fh:read('L')")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"abc\n"
    r = vm.exec(f"return fh:read('L')")
    assert isinstance(r[0], LuaString)
    assert r[0].content == b"def\n"
    r = vm.exec(f"return fh:read('L')")
    assert r[0] is LuaNil


def test_format_invalid(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\n")
    fh = LuaFile(open(test_file_path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), Variable(fh))
    with pytest.raises(LuaError) as excinfo:
        vm.exec(f"return fh:read('blablabla')")
    assert isinstance(excinfo.value, LuaError)
    assert isinstance(excinfo.value.message, LuaString)
    assert b"invalid format" in excinfo.value.message.content
