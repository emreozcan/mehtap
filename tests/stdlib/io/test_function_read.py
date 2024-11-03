from io import BytesIO

from mehtap.values import LuaString, LuaNil
from mehtap.vm import VirtualMachine


def test_read_default_input():
    input_file = BytesIO(b"abc\ndef\nghi\n")
    vm = VirtualMachine()
    vm.default_input = input_file
    vm.exec("s = io.read()")
    assert vm.get_ls(LuaString(b"s")) == LuaString(b"abc")
    vm.exec("s = io.read()")
    assert vm.get_ls(LuaString(b"s")) == LuaString(b"def")
    vm.exec("s = io.read()")
    assert vm.get_ls(LuaString(b"s")) == LuaString(b"ghi")
    vm.exec("s = io.read()")
    assert vm.get_ls(LuaString(b"s")) == LuaNil
    vm.exec("s = io.read()")
    assert vm.get_ls(LuaString(b"s")) == LuaNil
    assert not vm.default_input.closed
