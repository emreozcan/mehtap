import os
from os import close

from mehtap.values import LuaString
from mehtap.vm import VirtualMachine

vm = VirtualMachine()


def test_tmpname(tmp_path):
    os.chdir(tmp_path)

    r = vm.eval('os.tmpname()')
    assert len(r) == 1
    assert isinstance(r[0], LuaString)

    fd = os.open(r[0].content, os.O_CREAT)
    close(fd)
