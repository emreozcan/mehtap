from io import BytesIO

import pytest

from mehtap.control_structures import LuaError
from mehtap.library.stdlib.io_library import LuaFile
from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_set():
    vm = VirtualMachine()
    vm.put_nonlocal_ls(
        LuaString(b"fh"),
        LuaFile(BytesIO()),
    )
    with pytest.raises(LuaError) as excinfo:
        vm.exec("fh.hello = 'there'")
    assert isinstance(excinfo.value, LuaError)
    assert isinstance(excinfo.value.message, LuaString)
    assert b"index" in excinfo.value.message.content


def test_get():
    vm = VirtualMachine()
    vm.put_nonlocal_ls(
        LuaString(b"fh"),
        LuaFile(BytesIO()),
    )
    with pytest.raises(LuaError) as excinfo:
        vm.exec("print(fh.hello)")
    assert isinstance(excinfo.value, LuaError)
    assert isinstance(excinfo.value.message, LuaString)
    assert b"index" in excinfo.value.message.content


