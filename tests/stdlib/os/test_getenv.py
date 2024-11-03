import os

from ay.values import LuaNil, LuaString
from ay.vm import VirtualMachine

vm = VirtualMachine()


def test_getenv():
    if "AY_TEST" in os.environ:
        del os.environ["AY_TEST"]
    assert "AY_TEST" not in os.environ

    os.environ["AY_TEST"] = "950aaaa"
    r = vm.exec(r'''os.getenv("AY_TEST")''')
    assert r == [LuaString(b"950aaaa")]

    del os.environ["AY_TEST"]
    r = vm.exec(r'''os.getenv("AY_TEST")''')
    assert r == [LuaNil]
