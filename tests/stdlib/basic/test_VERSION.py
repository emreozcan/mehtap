from ay import __ay_version__
from ay.__main__ import work_chunk
from ay.values import LuaString
from ay.vm import VirtualMachine


def test_version():
    vm = VirtualMachine()
    assert work_chunk(
        "return _VERSION",
        vm
    ) == [LuaString(f"ay {__ay_version__}".encode("utf-8"))]
