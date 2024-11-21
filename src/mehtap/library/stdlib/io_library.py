from __future__ import annotations

import subprocess
from io import SEEK_CUR, SEEK_SET, SEEK_END
from os import fsync
from tempfile import TemporaryFile
from typing import TypeVar, BinaryIO, IO

import attrs

from mehtap.ast_nodes import Numeral
from mehtap.ast_transformer import transformer
from mehtap.control_structures import LuaError
from mehtap.library.provider_abc import LibraryProvider
from mehtap.parser import numeral_parser
from mehtap.py2lua import lua_function, PyLuaRet
from mehtap.scope import Scope
from mehtap.values import (
    LuaTable,
    LuaString,
    LuaNil,
    LuaNumber,
    LuaValue,
    LuaUserdata,
    LuaIndexableABC,
    LuaFunction,
    type_of_lv,
)

FAIL = LuaNil


@attrs.define(slots=True, eq=False, repr=False)
class LuaFile(LuaUserdata, LuaIndexableABC):
    io: BinaryIO

    def rawput(self, key: LuaValue, value: LuaValue, *, raw: bool = True) -> None:
        raise LuaError("attempt to set index on a file value")

    def rawget(self, key: LuaValue, *, raw: bool = True) -> LuaValue:
        if not isinstance(key, LuaString):
            raise LuaError("invalid index to a file value")
        match key.content:
            case b"close":
                return _lf_file_method_close
            case b"flush":
                return _lf_file_method_flush
            case b"lines":
                return _lf_file_method_lines
            case b"read":
                return _lf_file_method_read
            case b"seek":
                return _lf_file_method_seek
            case b"setvbuf":
                return _lf_file_method_setvbuf
            case b"write":
                return _lf_file_method_write
            case _:
                raise LuaError("invalid index to a file value")

    T = TypeVar("T")

    def get_with_fallback(self, key: LuaValue, fallback: T) -> LuaValue | T:
        return self.rawget(key)

    def has(self, key: LuaValue) -> bool:
        return isinstance(key, LuaString) and key.content in (
            b"close",
            b"flush",
            b"lines",
            b"read",
            b"seek",
            b"setvbuf",
            b"write",
        )

    def _name(self) -> str:
        if hasattr(self.io, "name"):
            name = self.io.name
            if isinstance(name, bytes):
                return name.decode("utf-8")
            return str(self.io.name)
        return repr(self.io)

    def __str__(self):
        return f"file: {self._name()} ({hex(id(self))})"


@lua_function(name="close")
def _lf_file_method_close(self: LuaFile, /) -> PyLuaRet:
    self.io.close()
    return None


@lua_function(name="flush")
def _lf_file_method_flush(self: LuaFile, /) -> PyLuaRet:
    return _fsync_io(self.io)


def _fsync_io(io: IO, /) -> PyLuaRet:
    io.flush()
    fsync(io.fileno())
    return None


@lua_function(name="lines", gets_scope=True)
def _lf_file_method_lines(scope: Scope, self: LuaFile, /, *formats) -> PyLuaRet:
    return _file_method_lines(scope, self, *formats)


def _file_method_lines(scope: Scope, self: LuaFile, /, *formats) -> PyLuaRet:
    # When no format is given, uses "l" as a default.
    if not formats:
        formats = (LuaString(b"l"),)

    # Returns an iterator function that,
    @lua_function()
    def iterator_function() -> PyLuaRet:
        # each time it is called, reads the file
        # according to the given formats.
        return _file_method_read(scope, self, *formats)

    # As an example, the construction
    #     for c in file:lines(1) do body end
    # will iterate over all characters of the file, starting at the current
    # position.
    # Unlike io.lines, this function does not close the file when the loop ends.
    return [iterator_function]


def _read_format_n(scope: Scope, file: LuaFile) -> LuaNumber | FAIL:
    # "n": reads a numeral and returns it as a float or an integer,
    # following the lexical conventions of Lua.
    # (The numeral may have leading whitespaces and a sign.) This format
    # always reads the longest input sequence that is a valid prefix for a
    # numeral; if that prefix does not form a valid numeral
    # (e.g., an empty string, "0x", or "3.4e-") or it is too long
    # (more than 200 characters), it is discarded and the format returns
    # fail.
    part = file.io.read(201)
    if not part:
        return FAIL
    for length in range(len(part), 0, -1):
        try:
            input = part[:length].decode("ascii")
            parsed = numeral_parser.parse(input)
            transformed: Numeral = transformer.transform(parsed)
            return transformed.evaluate(scope=scope)
        except Exception:
            continue
        finally:
            file.io.seek(201 - len(part), SEEK_CUR)
            if length == 201:
                return FAIL
    file.io.seek(-len(part), SEEK_CUR)
    return FAIL


def _read_format_a(file: LuaFile) -> LuaString:
    # "a": reads the whole file, starting at the current position. On end of
    # file, it returns the empty string; this format never fails.
    return LuaString(file.io.read())


def _read_format_l(file: LuaFile) -> LuaString | FAIL:
    # "l": reads the next line skipping the end of line, returning fail on
    # end of file. This is the default format.
    line = file.io.readline()
    if not line:
        return FAIL
    return LuaString(line[:-1])


def _read_format_big_l(file: LuaFile) -> LuaString:
    # "L": reads the next line keeping the end-of-line character (if present),
    # returning fail on end of file.
    line = file.io.readline()
    if not line:
        return FAIL
    return LuaString(line)


def _read_format_number(file: LuaFile, number: int) -> LuaString:
    # number: reads a string with up to this number of bytes, returning fail
    # on end of file.
    # If number is zero,
    if number == 0:
        # it reads nothing and returns an
        # empty string, or fail on end of file.
        check_c = file.io.read(1)
        if not check_c:
            return FAIL
        file.io.seek(-1, SEEK_CUR)
        return LuaString(b"")
    acc = file.io.read(number)
    if not acc:
        return FAIL
    return LuaString(acc)


@lua_function(name="read", gets_scope=True)
def _lf_file_method_read(scope: Scope, self: LuaFile, /, *formats: LuaValue) \
        -> PyLuaRet:
    return _file_method_read(scope, self, *formats)


def _file_method_read(scope: Scope, self: LuaFile, /, *formats: LuaValue) \
        -> PyLuaRet:
    if not formats:
        return [_read_format_l(self)]
    return_vals: list[LuaValue] = []
    for format in formats:
        if isinstance(format, LuaNumber):
            return_vals.append(_read_format_number(self, int(format.value)))
        elif format == LuaString(b"n"):
            return_vals.append(_read_format_n(scope=scope, file=self))
        elif format == LuaString(b"a"):
            return_vals.append(_read_format_a(self))
        elif format == LuaString(b"l"):
            return_vals.append(_read_format_l(self))
        elif format == LuaString(b"L"):
            return_vals.append(_read_format_big_l(self))
        else:
            raise LuaError(
                "invalid format (valid formats are a number, 'n', 'a', 'l', "
                "and 'L'.)"
            )
    return return_vals


SYMBOL__FD = LuaString(b"__fd")


@lua_function(name="seek")
def _lf_file_method_seek(
    self: LuaFile,
    whence: LuaString | None = None,
    offset: LuaNumber | None = None,
    /,
) -> PyLuaRet:
    if whence is None:
        whence = LuaString(b"cur")
    if offset is None:
        offset = LuaNumber(0)
    match whence.content:
        case b"set":
            new_offset = self.io.seek(int(offset.value), SEEK_SET)
        case b"cur":
            new_offset = self.io.seek(int(offset.value), SEEK_CUR)
        case b"end":
            new_offset = self.io.seek(int(offset.value), SEEK_END)
        case _:
            raise LuaError("invalid whence (must be 'set', 'cur', or 'end'.)")
    return [LuaNumber(new_offset)]


@lua_function(name="setvbuf", gets_scope=True)
def _lf_file_method_setvbuf(
    scope: Scope, self: LuaFile, mode, size=None, /
) -> PyLuaRet:
    scope.vm.get_warning("file:setvbuf(): ignored call")
    return None


@lua_function(name="write")
def _lf_file_method_write(
    self: LuaFile,
    /,
    *values: LuaValue,
) -> PyLuaRet:
    return _file_method_write(self, *values)


def _file_method_write(
    self: LuaFile,
    /,
    *values: LuaValue,
) -> PyLuaRet:
    for value in values:
        if isinstance(value, LuaString):
            self.io.write(value.content)
        elif isinstance(value, LuaNumber):
            self.io.write(str(value).encode("ascii"))
    return [self]


@lua_function(name="close", gets_scope=True)
def lf_io_close(scope: Scope, file: LuaFile | None = None, /) -> PyLuaRet:
    return io_close(scope, file)


def io_close(scope: Scope, file: LuaFile | None = None, /) -> PyLuaRet:
    if file is None:
        binary_io = scope.vm.default_output
    else:
        binary_io = file.io
    binary_io.close()
    return None


@lua_function(name="flush", gets_scope=True)
def lf_io_flush(scope: Scope, /) -> PyLuaRet:
    return io_flush(scope)


def io_flush(scope: Scope, /) -> PyLuaRet:
    _fsync_io(scope.vm.default_output)
    return None


@lua_function(name="input", gets_scope=True)
def lf_io_input(
    scope: Scope, file: LuaFile | LuaString | None = None, /
) -> PyLuaRet:
    return io_input(scope, file)


def io_input(scope: Scope, file: LuaFile | LuaString | None = None, /):
    # When called with a file name, it opens the named file (in text mode),
    # and sets its handle as the default input file.
    try:
        if isinstance(file, LuaString):
            file = open(file.content, "rb")
            scope.vm.default_input = file
            return None
        # When called with a file handle, it simply sets this file handle as
        # the default input file.
        if isinstance(file, LuaFile):
            scope.vm.default_input = file.io
            return None
        # When called without arguments, it returns the
        # current default input file.
        if file is None:
            return [LuaFile(scope.vm.default_input)]
        # In case of errors this function raises the error, instead of
        # returning an error code.
    except Exception as e:
        raise LuaError(f"io.input(): {e!s}")


@lua_function(name="lines", gets_scope=True)
def lf_io_lines(
    scope: Scope, filename: LuaString | None = None, /, *formats
) -> PyLuaRet:
    return io_lines(scope, filename, *formats)


def io_lines(
    scope: Scope, filename: LuaString | None = None, /, *formats
) -> PyLuaRet:
    # The call io.lines() (with no file name) is equivalent to
    # io.input():lines("l"); that is, it iterates over the lines of the
    # default input file.
    # In this case, the iterator does not close the file when the loop ends.
    if filename is None:
        file_handle = LuaFile(scope.vm.default_input)
        to_close = False
    else:
        file_handle = LuaFile(open(filename.content, "rb"))
        to_close = True

    # Opens the given file name in read mode and returns an iterator
    # function that works like file:lines(···) over the opened file.
    # When the iterator function fails to read any value, it automatically
    # closes the file.
    @lua_function()
    def iterator_function() -> PyLuaRet:
        f = _file_method_read(scope, file_handle, *formats)
        if to_close and (
            f is None
            or any(r is LuaNil for r in f)
        ):
            file_handle.io.close()
        return f
    # Besides the iterator function, io.lines returns three other
    # values: two nil values as placeholders, plus the created file
    # handle.
    # Therefore, when used in a generic for loop, the file is closed
    # also if the loop is interrupted by an error or a break.
    return [iterator_function, LuaNil, LuaNil, file_handle]


@lua_function(name="open")
def lf_io_open(
    filename: LuaString, mode: LuaString | None = None, /
) -> PyLuaRet:
    return io_open(filename, mode)


def io_open(filename: LuaString, mode: LuaString | None = None, /) -> PyLuaRet:
    # This function opens a file, in the mode specified in the string mode.
    # In case of success, it returns a new file handle.
    #
    # The mode string can be any of the following:
    #
    #     "r": read mode (the default);
    #     "w": write mode;
    #     "a": append mode;
    #     "r+": update mode, all previous data is preserved;
    #     "w+": update mode, all previous data is erased;
    #     "a+": append update mode, previous data is preserved, writing is
    #           only allowed at the end of file.
    #
    # The mode string can also have a 'b' at the end, which is needed in
    # some systems to open the file in binary mode.
    if mode is None:
        mode = LuaString(b"r")
    if not isinstance(mode, LuaString):
        raise LuaError("'mode' must be a string")
    match mode.content:
        case b"r" | b"rb":
            mode_str = "rb"
        case b"w" | b"wb":
            mode_str = "wb"
        case b"a" | b"ab":
            mode_str = "ab"
        case b"r+" | b"r+b":
            mode_str = "r+b"
        case b"w+" | b"w+b":
            mode_str = "w+b"
        case b"a+" | b"a+b":
            mode_str = "a+b"
        case _:
            raise LuaError("invalid mode (must match /[rwa]+?b?/.)")
    return [LuaFile(open(filename.content, mode_str))]


@lua_function(name="output", gets_scope=True)
def lf_io_output(
    scope: Scope, file: LuaFile | LuaString | None = None, /
) -> PyLuaRet:
    return io_output(scope, file)


def io_output(
    scope: Scope, file: LuaFile | LuaString | None = None, /):
    # Similar to io.input, but operates over the default output file.

    # When called with a file name, it opens the named file (in text mode),
    # and sets its handle as the default input file.
    try:
        if isinstance(file, LuaString):
            scope.vm.default_output = open(file.content, "rb")
            return None
        # When called with a file handle, it simply sets this file handle as
        # the default input file.
        if isinstance(file, LuaFile):
            scope.vm.default_output = file.io
            return None
        # When called without arguments, it returns the
        # current default input file.
        if file is None:
            return [LuaFile(scope.vm.default_output)]
        # In case of errors this function raises the error, instead of
        # returning an error code.
    except Exception as e:
        raise LuaError(f"io.output(): {e!s}")


@lua_function(name="popen")
def lf_io_popen(prog, mode=None, /) -> PyLuaRet:
    return io_popen(prog, mode)


def io_popen(prog, mode=None, /):
    # io.popen (prog [, mode])
    # This function is system dependent and is not available on all
    # platforms.
    # Starts the program prog in a separated process and returns a file
    # handle that you can use to read data from this program
    # (if mode is "r", the default) or to write data to this program
    # (if mode is "w").
    if not isinstance(prog, LuaString):
        type_of_prog = type_of_lv(prog)
        raise LuaError(
            f"bad argument #1 to 'popen' "
            f"(string expected, got {type_of_prog})"
        )
    if mode is not None:
        if not isinstance(mode, LuaString):
            type_of_mode = type_of_lv(mode)
            raise LuaError(
                f"bad argument #2 to 'popen' "
                f"(string expected, got {type_of_mode})"
            )
        if mode.content not in (b"r", b"w"):
            raise LuaError(
                f"invalid argument #2 to popen ('r' or 'w' expected)"
            )
        mode_str = mode.content.decode("ascii")
    else:
        mode_str = "r"
    popen = subprocess.Popen(
        prog.content,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )
    if mode_str == "r":
        return [LuaFile(popen.stdout)]
    return [LuaFile(popen.stdin)]


@lua_function(name="read", gets_scope=True)
def lf_io_read(scope: Scope, /, *formats) -> PyLuaRet:
    return io_read(scope, *formats)


def io_read(scope: Scope, /, *formats) -> PyLuaRet:
    # io.read (···)
    #
    # Equivalent to io.input():read(···).
    return _file_method_read(scope, io_input(scope)[0])


@lua_function(name="tmpfile")
def lf_io_tmpfile() -> PyLuaRet:
    return io_tmpfile()


def io_tmpfile() -> PyLuaRet:
    # io.tmpfile ()
    #
    # In case of success, returns a handle for a temporary file. This file
    # is opened in update mode and it is automatically removed when the
    # program ends.
    return [LuaFile(TemporaryFile())]


@lua_function(name="type")
def lf_io_type(obj: LuaValue, /) -> PyLuaRet:
    return io_type(obj)


def io_type(obj: LuaValue, /) -> PyLuaRet:
    # io.type (obj)
    #
    # Checks whether obj is a valid file handle. Returns the string "file"
    # if obj is an open file handle, "closed file" if obj is a closed file
    # handle, or fail if obj is not a file handle.
    if not isinstance(obj, LuaFile):
        return [FAIL]
    if obj.io.closed:
        return [LuaString(b"closed file")]
    return [LuaString(b"file")]


@lua_function(name="write", gets_scope=True)
def lf_io_write(scope: Scope, /, *values: LuaValue) -> PyLuaRet:
    return io_write(scope, *values)


def io_write(scope: Scope, /, *values: LuaValue) -> PyLuaRet:
    # io.write (···)
    #
    # Equivalent to io.output():write(···).
    return _file_method_write(LuaFile(scope.vm.default_output), *values)


SYMBOL_IO = LuaString(b"io")


class IOLibrary(LibraryProvider):
    def provide(self, global_table: LuaTable) -> None:
        io_table = LuaTable()
        global_table.rawput(SYMBOL_IO, io_table)

        for name_of_global, value_of_global in globals().items():
            if name_of_global.startswith("lf_io_"):
                assert isinstance(value_of_global, LuaFunction)
                assert value_of_global.name
                io_table.rawput(
                    LuaString(value_of_global.name.encode("ascii")),
                    value_of_global,
                )
