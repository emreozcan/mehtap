from freezegun import freeze_time

from mehtap.library.stdlib.os_library import os_time, os_difftime
from mehtap.values import LuaNumber


def test_difftime():
    with freeze_time("2021-02-03 04:05:06"):
        t1, = os_time()
    with freeze_time("2021-02-03 04:05:37"):
        t2, = os_time()

    assert os_difftime(t2, t1) == [LuaNumber(31)]
