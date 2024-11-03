from mehtap import __version__
from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_version():
    vm = VirtualMachine()
    assert vm.eval("_VERSION") == [
        LuaString(f"mehtap {__version__}".encode("utf-8"))
    ]
