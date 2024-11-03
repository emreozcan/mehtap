import os

from mehtap.values import LuaNil, LuaString
from mehtap.vm import VirtualMachine

vm = VirtualMachine()


def test_getenv():
    if "MEHTAP_TEST" in os.environ:
        del os.environ["MEHTAP_TEST"]
    assert "MEHTAP_TEST" not in os.environ

    os.environ["MEHTAP_TEST"] = "950aaaa"
    r = vm.exec(r'''os.getenv("MEHTAP_TEST")''')
    assert r == [LuaString(b"950aaaa")]

    del os.environ["MEHTAP_TEST"]
    r = vm.exec(r'''os.getenv("MEHTAP_TEST")''')
    assert r == [LuaNil]
