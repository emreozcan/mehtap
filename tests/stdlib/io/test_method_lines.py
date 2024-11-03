from ay.library.stdlib.io_library import LuaFile
from ay.values import LuaString, LuaNil
from ay.vm import VirtualMachine


def test_lines_file_input(tmp_path):
    path = tmp_path / "test.txt"
    path.write_bytes(b"abc\ndef\nghi\n")
    vm = VirtualMachine()
    fh = LuaFile(open(path, "rb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), fh)
    vm.exec(f"iterator_function = fh:lines()")
    assert vm.exec("iterator_function()") == [LuaString(b"abc")]
    assert vm.exec("iterator_function()") == [LuaString(b"def")]
    assert vm.exec("iterator_function()") == [LuaString(b"ghi")]
    assert not fh.io.closed
    assert vm.exec("iterator_function()") == [LuaNil]
    assert not fh.io.closed
    assert path.exists()
    assert path.read_bytes() == b"abc\ndef\nghi\n"
