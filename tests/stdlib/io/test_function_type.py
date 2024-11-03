from ay.values import LuaString, LuaNil
from ay.vm import VirtualMachine


def test_type_open(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r')")
    r = vm.exec("return io.type(fh)")
    assert r == [LuaString(b"file")]


def test_type_closed(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\ndef\nghi\n")
    vm.exec(f"fh = io.open({str(test_file_path)!r}, 'r')")
    vm.exec("fh:close()")
    r = vm.exec("return io.type(fh)")
    assert r == [LuaString(b"closed file")]


def test_type_fail():
    vm = VirtualMachine()
    r = vm.exec("return io.type(1)")
    assert r == [LuaNil]
