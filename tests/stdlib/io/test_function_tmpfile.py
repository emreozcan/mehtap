import os.path
from pathlib import Path

from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_tmpfile():
    vm = VirtualMachine()
    vm.exec("fh = io.tmpfile()")
    fh = vm.get_ls(LuaString(b"fh"))
    vm.exec("fh:write('abc\\ndef\\nghi\\n')")
    vm.exec("fh:seek('set')")
    vm.exec("s = fh:read('a')")
    assert vm.get_ls(LuaString(b"s")) == LuaString(b"abc\ndef\nghi\n")
    vm.exec("fh:close()")
    assert not os.path.exists(fh.io.name)
