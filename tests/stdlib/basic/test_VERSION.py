from ay import __version__
from ay.values import LuaString
from ay.vm import VirtualMachine


def test_version():
    vm = VirtualMachine()
    assert vm.eval("_VERSION") == [
        LuaString(f"ay {__version__}".encode("utf-8"))
    ]
