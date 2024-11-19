import os

from mehtap.values import LuaString, LuaNumber, LuaBool, LuaNil
from mehtap.vm import VirtualMachine

vm = VirtualMachine()


def test_execute_success(capsys, tmp_path):
    os.chdir(tmp_path)

    r = vm.eval(r'''os.execute("echo Hello World > hw.txt")''')
    assert r == [LuaBool(True), LuaString(b"exit"), LuaNumber(0)]
    assert (tmp_path / "hw.txt").read_bytes().strip() == b"Hello World"


def test_execute_fail_exit():
    r = vm.eval(r'''os.execute("exit 1")''')
    assert r == [LuaNil, LuaString(b"exit"), LuaNumber(1)]
