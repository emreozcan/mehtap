from mehtap.library.stdlib.io_library import LuaFile
from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_flush_method(tmp_path):
    vm = VirtualMachine()
    file_path = tmp_path / "test.txt"
    file_path.write_bytes(b"abcde")
    lua_file = LuaFile(open(file_path, "ab"))
    vm.put_nonlocal_ls(LuaString(b"file"), lua_file)
    lua_file.io.write(b"12345")
    assert file_path.read_bytes() == b"abcde"
    vm.exec("file:flush()")
    assert file_path.read_bytes() == b"abcde12345"
