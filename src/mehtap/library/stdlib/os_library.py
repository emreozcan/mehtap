from __future__ import annotations

import locale as lc
import os
import subprocess
import sys
import tempfile
import datetime
from time import process_time

import attrs

from mehtap.control_structures import LuaError
from mehtap.operations import str_to_lua_string, index, coerce_to_bool
from mehtap.py2lua import lua_function, PyLuaWrapRet, py2lua, PyLuaRet
from mehtap.library.provider_abc import LibraryProvider
from mehtap.values import (
    LuaTable,
    LuaString,
    LuaNil,
    LuaNumber,
    LuaBool,
    LuaValue,
    LuaFunction,
    type_of_lv,
)

FAIL = LuaNil


def _wday_py2lua(x: int) -> int:
    """transform (monday=0, sunday=6) to (sunday=1, saturday=7)"""
    if x == 6:
        return 1
    return x + 2


def _get_day_number_of_year(date: datetime.date) -> int:
    return date.timetuple().tm_yday


def _oserror_to_errtuple(e: OSError) -> list[LuaValue]:
    return [
        LuaNil,
        LuaString(e.strerror.encode("utf-8")),
        LuaNumber(e.errno),
    ]


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


_str_to_lc_category_map = {
    "all": lc.LC_ALL,
    "collate": lc.LC_COLLATE,
    "ctype": lc.LC_CTYPE,
    "monetary": lc.LC_MONETARY,
    "numeric": lc.LC_NUMERIC,
    "time": lc.LC_TIME,
}


def _get_category_from_luastr(luastr: LuaString) -> int:
    string = luastr.content.decode("utf-8")
    return _str_to_lc_category_map[string]


SYMBOL_YEAR = LuaString(b"year")
SYMBOL_MONTH = LuaString(b"month")
SYMBOL_DAY = LuaString(b"day")
SYMBOL_HOUR = LuaString(b"hour")
SYMBOL_MIN = LuaString(b"min")
SYMBOL_SEC = LuaString(b"sec")
SYMBOL_ISDST = LuaString(b"isdst")
ZERO_TD = datetime.timedelta(0)


@attrs.define(slots=True)
class TimeTuple:
    year: int
    month: int
    """range: 1,12"""
    day: int
    """range: 1,31"""
    hour: int | None = None
    """range: 0-23"""
    min: int | None = None
    """range: 0-59"""
    sec: int | None = None
    """range: 0-61 (Due to leap seconds)"""
    isdst: bool | None = None
    """daylight saving flag, a boolean"""

    def to_table(self) -> LuaTable:
        table_data = {
            SYMBOL_YEAR: LuaNumber(self.year),
            SYMBOL_MONTH: LuaNumber(self.month),
            SYMBOL_DAY: LuaNumber(self.day),
        }
        if self.hour is not None:
            table_data[SYMBOL_HOUR] = LuaNumber(self.hour)
        if self.min is not None:
            table_data[SYMBOL_MIN] = LuaNumber(self.min)
        if self.sec is not None:
            table_data[SYMBOL_SEC] = LuaNumber(self.sec)
        if self.isdst is not None:
            table_data[SYMBOL_ISDST] = LuaBool(self.isdst)
        return LuaTable(map=table_data)

    @classmethod
    def from_table(cls, table: LuaTable) -> TimeTuple:
        year_value = index(table, SYMBOL_YEAR)
        if year_value is LuaNil:
            raise LuaError("table must have field 'year'")
        if not isinstance(year_value, LuaNumber):
            raise LuaError("table field 'year' must be a number")
        year_int = year_value.value

        month_value = index(table, SYMBOL_MONTH)
        if month_value is LuaNil:
            raise LuaError("table must have field 'month'")
        if not isinstance(month_value, LuaNumber):
            raise LuaError("table field 'month' must be a number")
        month_int = month_value.value

        day_value = index(table, SYMBOL_DAY)
        if day_value is LuaNil:
            raise LuaError("table must have field 'day'")
        if not isinstance(day_value, LuaNumber):
            raise LuaError("table field 'day' must be a number")
        day_int = day_value.value

        hour_value = index(table, SYMBOL_HOUR)
        if hour_value is not LuaNil:
            if not isinstance(hour_value, LuaNumber):
                raise LuaError("table field 'hour' must be a number")
            hour_int = hour_value.value
        else:
            hour_int = None
        min_value = index(table, SYMBOL_MIN)
        if min_value is not LuaNil:
            if not isinstance(min_value, LuaNumber):
                raise LuaError("table field 'min' must be a number")
            min_int = min_value.value
        else:
            min_int = None

        sec_value = index(table, SYMBOL_SEC)
        if sec_value is not LuaNil:
            if not isinstance(sec_value, LuaNumber):
                raise LuaError("table field 'sec' must be a number")
            sec_int = sec_value.value
        else:
            sec_int = None

        isdst_value = index(table, SYMBOL_ISDST)
        if isdst_value is not LuaNil:
            isdst_bool = coerce_to_bool(isdst_value).true
        else:
            isdst_bool = None

        return cls(
            year=year_int,
            month=month_int,
            day=day_int,
            hour=hour_int,
            min=min_int,
            sec=sec_int,
            isdst=isdst_bool,
        )

    def to_datetime(self) -> datetime.datetime:
        return datetime.datetime(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            minute=self.min,
            second=self.sec,
            tzinfo=datetime.timezone.utc,
        )

    @classmethod
    def from_datetime(cls, dt: datetime.datetime) -> TimeTuple:
        if dt.tzinfo is not None:
            is_dst = bool(dt.tzinfo.dst(dt))
        else:
            is_dst = None
        return cls(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            min=dt.minute,
            sec=dt.second,
            isdst=is_dst,
        )


@lua_function(name="clock")
def lf_os_clock() -> PyLuaRet:
    return os_clock()


def os_clock() -> PyLuaRet:
    # Returns an approximation of the amount in seconds of CPU time used by
    # the program, as returned by the underlying ISO C function clock.
    return [LuaNumber(process_time())]


@lua_function(name="date")
def lf_os_date(format=LuaNil, time=LuaNil, /) -> PyLuaRet:
    return os_date(format, time)


SYMBOL_WDAY = LuaString(b"wday")
SYMBOL_YDAY = LuaString(b"yday")


def os_date(format=LuaNil, time=LuaNil, /) -> PyLuaRet:
    # Returns a string or a table containing date and time, formatted according
    # to the given string format.
    # If the time argument is present, this is the time to be formatted (see the
    # os.time function for a description of this value).
    # Otherwise, date formats the current time.
    if time is LuaNil:
        time_dt = _utcnow()
    else:
        if not isinstance(time, LuaNumber):
            time_type = type_of_lv(time)
            raise LuaError(
                f"bad argument #2 to 'date' (expected number, got {time_type})"
            )
        time_dt = datetime.datetime.fromtimestamp(
            time.value,
            datetime.timezone.utc
        )
    if format is LuaNil:
        # If format is absent, it defaults to "%c", which gives a human-readable
        # date and time representation using the current locale.
        format_str = "%c"
    elif not isinstance(format, LuaString):
        type_of_format = type_of_lv(format)
        raise LuaError(
            f"bad argument #1 to 'date' (expected string, got {type_of_format})"
        )
    else:
        format_str = format.content.decode("utf-8")
    if format_str and format_str[0] == "!":
        # If format starts with '!', then the date is formatted in Coordinated
        # Universal Time.
        # (strftime already converts to UTC if the time is not in UTC)
        format_str = format_str[1:]
    else:
        time_dt = time_dt.astimezone()
    # After this optional character, if format is the string
    # "*t", then date returns a table with the following fields:
    # year, month (1–12), day (1–31),
    # hour (0–23), min (0–59), sec (0–61, due to leap seconds),
    # wday (weekday, 1–7, Sunday is 1), yday (day of the year, 1–366),
    # and isdst (daylight saving flag, a boolean).
    # This last field may be absent if the information is not available.
    if format_str == "*t":
        timetuple = time_dt.timetuple()
        table = TimeTuple.from_datetime(time_dt).to_table()
        table.rawput(SYMBOL_WDAY, LuaNumber(_wday_py2lua(timetuple.tm_wday)))
        table.rawput(SYMBOL_YDAY, LuaNumber(timetuple.tm_yday))
        return [table]
    # If format is not "*t", then date returns the date as a string, formatted
    # according to the same rules as the ISO C function strftime.
    return [LuaString(time_dt.strftime(format_str).encode("utf-8"))]
    # On non-POSIX systems, this function may be not thread safe because of its
    # reliance on C function gmtime and C function localtime.


@lua_function(name="difftime")
def lf_os_difftime(t2, t1, /) -> PyLuaRet:
    return os_difftime(t2, t1)


def os_difftime(t2, t1, /) -> PyLuaRet:
    if not isinstance(t2, LuaNumber):
        t2_type = type_of_lv(t2)
        raise LuaError(
            f"bad argument #1 (t2) to 'difftime' "
            f"(number expected, got {t2_type})"
        )
    if not isinstance(t1, LuaNumber):
        t1_type = type_of_lv(t1)
        raise LuaError(
            f"bad argument #2 (t1) to 'difftime' "
            f"(number expected, got {t1_type})"
        )
    return [LuaNumber(t2.value - t1.value)]


@lua_function(name="execute")
def lf_os_execute(command=None, /) -> PyLuaRet:
    return os_execute(command)


def os_execute(command=None, /) -> PyLuaRet:
    # When called without a command, os.execute returns a boolean that is
    # true if a shell is available.
    if command is None:
        return [LuaBool(True)]

    # This function is equivalent to the ISO C function system.
    # It passes command to be executed by an operating system shell.
    if not isinstance(command, LuaString):
        raise LuaError("'command' must be a string")
    retcode = subprocess.call(
        command.content.decode("utf-8"),
        shell=True,
    )
    # Its first result is true if the command terminated successfully,
    # or fail otherwise.
    # After this first result the function returns a string plus a number,
    # as follows:
    #     "exit": the command terminated normally; the following number is
    #             the exit status of the command.
    #     "signal": the command was terminated by a signal; the following
    #               number is the signal that terminated the command.
    return [
        LuaBool(True) if retcode == 0 else FAIL,
        str_to_lua_string("exit" if retcode >= 0 else "signal"),
        LuaNumber(abs(retcode)),
    ]


@lua_function(name="exit")
def lf_os_exit(code=None, close=None, /) -> PyLuaRet:
    return os_exit(code, close)


def os_exit(code=None, close=None, /) -> PyLuaRet:
    # Calls the ISO C function exit to terminate the host program.
    # If code is true, the returned status is EXIT_SUCCESS;
    # if code is false, the returned status is EXIT_FAILURE;
    # if code is a number, the returned status is this number.
    # The default value for code is true.
    if code is None:
        code = 0
    elif isinstance(code, LuaNumber):
        code = code.value
    elif isinstance(code, LuaBool):
        code = 0 if code.true else 1
    else:
        raise LuaError("'code' must be a number or a boolean")

    # If the optional second argument close is true, the function closes the
    # Lua state before exiting (see lua_close).
    if close == LuaBool(True):
        sys.exit(code)
    else:
        os._exit(code)
    return []


@lua_function(name="getenv")
def lf_os_getenv(varname, /) -> PyLuaRet:
    return os_getenv(varname)


def os_getenv(varname, /) -> PyLuaRet:
    #  Returns the value of the process environment variable varname or fail
    #  if the variable is not defined.
    if not isinstance(varname, LuaString):
        raise LuaError("'varname' must be a string")
    value = os.getenv(varname.content.decode("utf-8"))
    if value is None:
        return [FAIL]
    return [str_to_lua_string(value)]


@lua_function(name="remove")
def lf_os_remove(filename, /) -> PyLuaRet:
    return os_remove(filename)


def os_remove(filename, /) -> PyLuaRet:
    # Deletes the file (or empty directory, on POSIX systems) with the
    # given name.
    if not isinstance(filename, LuaString):
        raise LuaError("'filename' must be a string")
    try:
        try:
            os.unlink(filename.content)
        except OSError as e:
            if os.name == "posix" and e.errno == 21:
                os.rmdir(filename.content)
            else:
                raise e
    except OSError as e:
        # If this function fails, it returns fail plus a string describing
        # the error and the error code.
        return _oserror_to_errtuple(e)
    # Otherwise, it returns true.
    return [LuaBool(True)]


@lua_function(name="rename")
def lf_os_rename(oldname, newname, /) -> PyLuaRet:
    return os_rename(oldname, newname)


def os_rename(oldname, newname, /) -> PyLuaRet:
    # Renames the file or directory named oldname to newname.
    if not isinstance(oldname, LuaString):
        raise LuaError("'oldname' must be a string")
    if not isinstance(newname, LuaString):
        raise LuaError("'newname' must be a string")
    try:
        os.rename(oldname.content, newname.content)
    except OSError as e:
        # If this function fails, it returns fail,
        # plus a string describing the error and the error code.
        return _oserror_to_errtuple(e)
    # Otherwise, it returns true.
    return [LuaBool(True)]


@lua_function(name="setlocale")
def lf_os_setlocale(locale, category=None, /) -> PyLuaRet:
    return os_setlocale(locale, category)


def os_setlocale(locale, category=None, /) -> PyLuaRet:
    # category is an optional string describing which category to change:
    # "all", "collate", "ctype", "monetary", "numeric", or "time";
    # the default category is "all".
    if category is None:
        category = lc.LC_ALL
    else:
        category = _get_category_from_luastr(category)
    # When called with nil as the first argument, this function only returns
    # the name of the current locale for the given category.
    if locale is LuaNil:
        current_lc = lc.getlocale(category)
        return [
            py2lua(current_lc[0]),
            py2lua(current_lc[1]),
        ]

    # Sets the current locale of the program.
    # locale is a system-dependent string specifying a locale;
    if not isinstance(locale, LuaString):
        raise LuaError("'locale' must be a string")
    # If locale is the empty string, the current locale is set to an
    # implementation-defined native locale.
    if not locale.content:
        locale = None
    else:
        locale = locale.content.decode("utf-8")
    # If locale is the string "C", the current locale is set to the standard
    # C locale.
    try:
        new_locale_name = lc.setlocale(category, locale)
        # The function returns the name of the new locale,
        # or fail if the request cannot be honored.
    except lc.Error:
        return [FAIL]
    else:
        return [str_to_lua_string(new_locale_name)]


@lua_function(name="time")
def lf_os_time(table=LuaNil, /) -> PyLuaRet:
    return os_time(table)


def os_time(table=LuaNil, /) -> PyLuaRet:
    # Returns the current time when called without arguments, or a time
    # representing the local date and time specified by the given table.
    #
    # When the function is called, the values in these fields do not need to be
    # inside their valid ranges.
    # For instance, if sec is -10, it means 10 seconds before the time specified
    # by the other fields; if hour is 1000, it means 1000 hours after the time
    # specified by the other fields.
    #
    # The returned value is a number, whose meaning depends on your system. In
    # POSIX, Windows, and some other systems, this number counts the number of
    # seconds since some given start time (the "epoch"). In other systems, the
    # meaning is not specified, and the number returned by time can be used only
    # as an argument to os.date and os.difftime.
    #
    # When called with a table, os.time also normalizes all the fields
    # documented in the os.date function, so that they represent the same time
    # as before the call but with values inside their valid ranges.
    if table is LuaNil:
        return [LuaNumber(datetime.datetime.now().timestamp())]
    return [LuaNumber(TimeTuple.from_table(table).to_datetime().timestamp())]


@lua_function(name="tmpname")
def lf_os_tmpname() -> PyLuaRet:
    return os_tmpname()


def os_tmpname() -> PyLuaRet:
    fd, name = tempfile.mkstemp()
    return [str_to_lua_string(name)]


class OSLibrary(LibraryProvider):
    def provide(self, global_table: LuaTable) -> None:
        os_table = LuaTable()
        global_table.rawput(LuaString(b"os"), os_table)

        for name_of_global, value_of_global in globals().items():
            if name_of_global.startswith("lf_os_"):
                assert isinstance(value_of_global, LuaFunction)
                assert value_of_global.name
                os_table.rawput(
                    LuaString(value_of_global.name.encode("ascii")),
                    value_of_global,
                )
