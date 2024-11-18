from __future__ import annotations

import locale as lc
import os
import subprocess
import sys
import tempfile
import time as py_time
import datetime

from mehtap.control_structures import LuaError
from mehtap.operations import str_to_lua_string
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
)

FAIL = LuaNil


def _py_wday_to_lua_wday(x: int) -> int:
    if x == 7:
        return 1
    return x + 1


def _get_day_number_of_year(date: datetime.date) -> int:
    return date.timetuple().tm_yday


def _oserror_to_errtuple(e: OSError) -> list[LuaValue]:
    return [
        LuaNil,
        LuaString(e.strerror.encode("utf-8")),
        LuaNumber(e.errno),
    ]


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


@lua_function(name="clock")
def lf_os_clock() -> PyLuaRet:
    return os_clock()


def os_clock() -> PyLuaRet:
    # Returns an approximation of the amount in seconds of CPU time used by
    # the program, as returned by the underlying ISO C function clock.
    return [LuaNumber(py_time.process_time())]


@lua_function(name="date")
def lf_os_date(format=None, time=None, /) -> PyLuaRet:
    return os_date(format, time)


def os_date(format=None, time=None, /) -> PyLuaRet:
    raise NotImplementedError()


@lua_function(name="difftime")
def lf_os_difftime(t2, t1, /) -> PyLuaRet:
    return os_difftime(t2, t1)


def os_difftime(t2, t1, /) -> PyLuaRet:
    raise NotImplementedError()


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
def lf_os_time(table=None, /) -> PyLuaRet:
    return os_time(table)


def os_time(table=None, /) -> PyLuaRet:
    raise NotImplementedError()


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
