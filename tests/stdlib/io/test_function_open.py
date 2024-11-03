import pytest

from mehtap.control_structures import LuaError
from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_open_read(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r')")
    fh = vm.get_ls(LuaString(b"fh"))
    assert fh.io.name == bytes(test_file_path)
    assert fh.io.mode == "rb"
    assert fh.io.closed is False
    assert fh.io.read() == b"abc\ndef\nghi\n"


def test_open_write(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'w')")
    fh = vm.get_ls(LuaString(b"fh"))
    assert fh.io.name == bytes(test_file_path)
    assert fh.io.mode == "wb"
    assert fh.io.closed is False
    vm.exec("fh:write('abc\\ndef\\nghi\\n')")
    assert fh.io.closed is False
    fh.io.close()
    assert fh.io.closed is True
    assert test_file_path.read_bytes() == b"abc\ndef\nghi\n"


def test_open_append(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'a')")
    fh = vm.get_ls(LuaString(b"fh"))
    assert fh.io.name == bytes(test_file_path)
    assert fh.io.mode == "ab"
    assert fh.io.closed is False
    vm.exec("fh:write('jkl\\nmno\\npqr\\n')")
    assert fh.io.closed is False
    fh.io.close()
    assert fh.io.closed is True
    assert test_file_path.read_bytes() == b"abc\ndef\nghi\njkl\nmno\npqr\n"


def test_open_truncate(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r+')")
    fh = vm.get_ls(LuaString(b"fh"))
    assert fh.io.name == bytes(test_file_path)
    assert fh.io.mode == "rb+"
    assert fh.io.closed is False
    vm.exec("fh:write('jkl\\nmno\\npqr\\n')")
    assert fh.io.closed is False
    fh.io.close()
    assert fh.io.closed is True
    assert test_file_path.read_bytes() == b"jkl\nmno\npqr\n"


def test_open_invalid_mode():
    vm = VirtualMachine()
    with pytest.raises(LuaError) as excinfo:
        vm.exec("io.open('test.txt', 'x')")
    assert isinstance(excinfo.value, LuaError)
    assert isinstance(excinfo.value.message, LuaString)
    assert b"invalid mode" in excinfo.value.message.content
