import time

from mehtap.library.stdlib.os_library import os_time
from mehtap.py2lua import py2lua


def test_time_now():
    lua_time, = os_time()
    real_time = time.time()
    assert abs(lua_time.value - real_time) < 2


def test_time_with_table():
    time_tuple = py2lua({"year": 2021, "month": 2, "day": 3, "hour": 4, "min": 5, "sec": 6})
    retval, = os_time(time_tuple)
    assert retval.value == 1612314306
