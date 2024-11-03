from ay.library.stdlib.io_library import LuaFile
from ay.values import LuaString
from ay.vm import VirtualMachine


def test_method_write(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    test_file_path.write_bytes(b"abc\n")
    lua_file = LuaFile(open(test_file_path, "wb"))
    vm.put_nonlocal_ls(LuaString(b"fh"), lua_file)
    vm.exec("fh:write('def')")
    lua_file.io.flush()
    assert test_file_path.read_bytes() == b"def"
    vm.exec("fh:write(12.25)")
    lua_file.io.flush()
    assert test_file_path.read_bytes() == b"def12.25"
    vm.exec("fh:write('jkl')")
    lua_file.io.flush()
    assert test_file_path.read_bytes() == b"def12.25jkl"
