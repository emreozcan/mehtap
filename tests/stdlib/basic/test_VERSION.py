from ay import __ay_version__
from ay.values import LuaString
from ay.vm import VirtualMachine


def test_version():
    vm = VirtualMachine()
    assert vm.eval("_VERSION") == [
        LuaString(f"ay {__ay_version__}".encode("utf-8"))
    ]
