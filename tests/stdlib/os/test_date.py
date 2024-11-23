import datetime

from freezegun import freeze_time
import pytest

from mehtap.library.stdlib.os_library import os_date
from mehtap.values import LuaString, LuaNumber, LuaNil, LuaTable, LuaBool


def test_date_with_no_arguments_utc():
    with freeze_time("2023-11-23 22:03:45", tz_offset=0):
        retval, = os_date()
        now_strftime = datetime.datetime.now().strftime("%c")
    assert isinstance(retval, LuaString)
    retval_str = retval.content.decode("utf-8")
    assert retval_str == now_strftime == "Thu Nov 23 22:03:45 2023"


def test_date_with_no_arguments_offset():
    with freeze_time("2023-11-23 22:03:45", tz_offset=1):
        retval, = os_date()
        now_strftime = datetime.datetime.now().strftime("%c")
    assert isinstance(retval, LuaString)
    retval_str = retval.content.decode("utf-8")
    assert now_strftime == "Thu Nov 23 23:03:45 2023"
    assert retval_str == "Thu Nov 23 23:03:45 2023"


def test_date_with_format_argument_utc():
    format_str = "%Y-%m-%d %H:%M:%S"
    with freeze_time("2023-11-23 22:03:45", tz_offset=0):
        retval, = os_date(LuaString(format_str.encode("utf-8")))
        now_strftime = datetime.datetime.now().strftime(format_str)
    assert isinstance(retval, LuaString)
    retval_str = retval.content.decode("utf-8")
    assert retval_str == now_strftime == "2023-11-23 22:03:45"


def test_date_with_time_argument_utc():
    with freeze_time("2023-11-23 22:03:45", tz_offset=0):
        retval, = os_date(LuaNil, LuaNumber(1600000000))
    assert isinstance(retval, LuaString)
    assert retval.content == b"Sun Sep 13 12:26:40 2020"


def test_date_with_time_argument_in_utc_offset():
    with freeze_time("2023-11-23 22:03:45", tz_offset=1):
        retval, = os_date(LuaString(b"!%c"), LuaNumber(1600000000))
    assert isinstance(retval, LuaString)
    assert retval.content == b"Sun Sep 13 12:26:40 2020"


@pytest.mark.xfail(reason="freezegun can't entirely replicate tz_offset")
def test_date_with_time_argument_in_local_offset():
    with freeze_time("2023-11-23 22:03:45", tz_offset=1):
        retval, = os_date(LuaString(b"%c"), LuaNumber(1600000000))
    assert isinstance(retval, LuaString)
    # 1600000000 is 12:26 UTC, since we are in UTC+1, it should display 13:26
    assert retval.content == b"Sun Sep 13 13:26:40 2020"


def test_date_with_table_output_and_time_argument_in_utc_given_utc():
    with freeze_time("2023-11-23 22:03:45", tz_offset=0):
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


def test_date_with_table_output_and_time_argument_in_utc_given_offset():
    with freeze_time("2023-11-23 21:03:45", tz_offset=1):
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


@pytest.mark.xfail(reason="freezegun can't entirely replicate tz_offset")
def test_date_with_table_output_and_time_argument_in_local_given_offset():
    with freeze_time("2023-11-23 21:03:45", tz_offset=1):
        retval, = os_date(LuaString(b"*t"), LuaNumber(1600000000))
    assert isinstance(retval, LuaTable)
    assert retval.map == {
        LuaString(b"year"): LuaNumber(2020),
        LuaString(b"month"): LuaNumber(9),
        LuaString(b"day"): LuaNumber(13),
        LuaString(b"hour"): LuaNumber(13),
        LuaString(b"min"): LuaNumber(26),
        LuaString(b"sec"): LuaNumber(40),
        LuaString(b"wday"): LuaNumber(1),
        LuaString(b"yday"): LuaNumber(257),
        LuaString(b"isdst"): LuaBool(False),
    }

