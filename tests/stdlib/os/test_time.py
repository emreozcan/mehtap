from datetime import datetime

from freezegun import freeze_time

from mehtap.library.stdlib.os_library import os_time
from mehtap.py2lua import py2lua


def test_time_now():
    with freeze_time(datetime.utcfromtimestamp(1600000000), tz_offset=0):
        lua_time, = os_time()
        real_time = datetime.now().timestamp()
    assert lua_time.value == real_time == 1600000000


def test_time_offset():
    with freeze_time(datetime.utcfromtimestamp(1600000000), tz_offset=1):
        lua_time, = os_time()
        real_time = datetime.now().timestamp()
    assert lua_time.value == real_time == 1600000000


time_tuple = py2lua(
    {"year": 2021, "month": 2, "day": 3, "hour": 4, "min": 5, "sec": 6}
)

def test_time_with_table_utc():
    with freeze_time("2023-11-23 22:03:45", tz_offset=0):
        retval, = os_time(time_tuple)
    assert retval.value == 1612325106

def test_time_with_table_offset():
    with freeze_time("2023-11-23 22:03:45", tz_offset=1):
        retval, = os_time(time_tuple)
    assert retval.value == 1612325106
