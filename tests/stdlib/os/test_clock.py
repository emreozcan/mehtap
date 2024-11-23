import time

from mehtap.library.stdlib.os_library import os_clock
from mehtap.values import LuaNumber


def test_clock():
    clock = time.process_time()
    clock_retval = os_clock()[0]
    assert isinstance(clock_retval, LuaNumber)
    assert abs(clock_retval.value - clock) < 1e-5
