from mehtap.library.stdlib.io_library import LuaFile
from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_close_method(tmp_path):
    vm = VirtualMachine()
    file = open(tmp_path / "test.txt", "wb")
    vm.put_nonlocal_ls(LuaString(b"file"), LuaFile(file))
    assert not file.closed
    vm.exec("file:close()")
    assert file.closed
