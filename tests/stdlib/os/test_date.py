from time import strftime

from freezegun import freeze_time

from mehtap.library.stdlib.os_library import os_date
from mehtap.values import LuaString, LuaNumber, LuaNil, LuaTable, LuaBool


def test_date_with_no_arguments():
    retval, = os_date()
    now_strftime = strftime("%c")
    assert isinstance(retval, LuaString)
    retval_str = retval.content.decode("utf-8")
    assert retval_str == now_strftime


def test_date_with_format_argument():
    format_str = "%Y-%m-%d %H:%M:%S"
    retval, = os_date(LuaString(format_str.encode("utf-8")))
    now_strftime = strftime(format_str)
    assert isinstance(retval, LuaString)
    retval_str = retval.content.decode("utf-8")
    assert retval_str == now_strftime


def test_date_with_time_argument():
    retval, = os_date(LuaNil, LuaNumber(1600000000))
    assert isinstance(retval, LuaString)
    assert retval.content == b"Sun Sep 13 15:26:40 2020"


def test_date_with_utc_time_argument():
    with freeze_time("2024-11-23 22:03:45", tz_offset=3):
        retval, = os_date(LuaString(b"!%c"), LuaNumber(1600000000))
    assert isinstance(retval, LuaString)
    assert retval.content == b"Sun Sep 13 12:26:40 2020"

    with freeze_time("2024-11-23 22:03:45", tz_offset=3):
        retval, = os_date(LuaString(b"%c"), LuaNumber(1600000000))
    assert isinstance(retval, LuaString)
    assert retval.content == b"Sun Sep 13 15:26:40 2020"


def test_date_with_table_output():
    retval, = os_date(LuaString(b"!*t"), LuaNumber(1600000000))
    assert isinstance(retval, LuaTable)
    assert retval.map == {
        LuaString(b"year"): LuaNumber(2020),
        LuaString(b"month"): LuaNumber(9),
        LuaString(b"day"): LuaNumber(13),
        LuaString(b"hour"): LuaNumber(12),
        LuaString(b"min"): LuaNumber(26),
        LuaString(b"sec"): LuaNumber(40),
        LuaString(b"wday"): LuaNumber(1),
        LuaString(b"yday"): LuaNumber(257),
        LuaString(b"isdst"): LuaBool(False),
    }
