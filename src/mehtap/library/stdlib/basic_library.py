from __future__ import annotations

import sys
from io import BytesIO
from os.path import basename
from typing import TYPE_CHECKING

from mehtap.ast_nodes import UnaryOperation, UnaryOperator, Chunk
from mehtap.ast_transformer import transformer
from mehtap.py2lua import PyLuaRet, py2lua
from mehtap.library.provider_abc import LibraryProvider
from mehtap.py2lua import lua_function
from mehtap.values import (
    LuaTable,
    LuaValue,
    LuaNil,
    LuaString,
    LuaNumber,
    LuaNumberType,
    MAX_INT64,
    LuaFunction,
    LuaIndexableABC, type_of_lv,
)
from mehtap.control_structures import LuaError
from mehtap.values import LuaBool
from mehtap.parser import chunk_parser, numeral_parser
from mehtap.operations import rel_eq, length, call

if TYPE_CHECKING:
    from mehtap.scope import Scope
    from mehtap.values import LuaNilType


SYMBOL_METATABLE = LuaString(b"__metatable")
SYMBOL_PAIRS = LuaString(b"__pairs")
SYMBOL_TOSTRING = LuaString(b"__tostring")
SYMBOL_NAME = LuaString(b"__name")


FAIL = LuaNil


@lua_function(name="assert")
def lf_assert(v: LuaValue, message: LuaValue = LuaNil, /, *a) -> PyLuaRet:
    return basic_assert(v, message, *a)


def basic_assert(v: LuaValue, message: LuaValue = LuaNil, /, *a) -> PyLuaRet:
    """assert (v [, message])"""
    #  Raises an error if the value of its argument v is false
    #  (i.e., nil or false);
    if v is LuaNil or (isinstance(v, LuaBool) and not v.true):
        #  In case of error, message is the error object;
        if message is not LuaNil:
            raise LuaError(message)
        #  when absent, it defaults to "assertion failed!"
        raise LuaError("assertion failed!")
    #  otherwise, returns all its arguments.
    return [v, message, *a]


@lua_function(name="collectgarbage", gets_scope=True)
def lf_collectgarbage(scope: Scope, opt=None, arg=None, /) -> PyLuaRet:
    return basic_collectgarbage(scope, opt, arg)


def basic_collectgarbage(scope: Scope, opt=None, arg=None, /) -> PyLuaRet:
    """collectgarbage ([opt [, arg]])"""
    lf_warn.call(
        [py2lua("collectgarbage(): mehtap doesn't have garbage collection")],
        scope,
    )
    return [LuaNil]


@lua_function(name="dofile", gets_scope=True)
def lf_dofile(scope: Scope, filename: LuaString | None = None, /) -> PyLuaRet:
    return basic_dofile(scope, filename)


def basic_dofile(
    scope: Scope, filename: LuaString | None = None, /
) -> PyLuaRet:
    """dofile ([filename])"""
    #  Opens the named file and executes its content as a Lua chunk.
    #  When called without arguments, dofile executes the content of the
    #  standard input (stdin).
    infile = sys.stdin
    filename_str = "<stdin>"
    if filename is not None:
        if isinstance(filename, LuaString):
            infile = open(filename.content, "r", encoding="utf-8")
            filename_str = basename(filename.content)
        else:
            raise LuaError("bad argument #1 to 'dofile' (string expected)")
    #  Returns all values returned by the chunk. In case of errors,
    #  dofile propagates the error to its caller.
    #  (That is, dofile does not run in protected mode.)
    parsed_chunk = chunk_parser.parse(infile.read())
    chunk_node = transformer.transform(parsed_chunk, filename=filename_str)
    from mehtap.scope import Scope
    new_scope = Scope(
        vm=scope.vm,
        parent=None,
    )
    r = chunk_node.block.evaluate(new_scope)
    return r


@lua_function(name="error", gets_scope=True)
def lf_error(
    scope: Scope,
    message: LuaValue = LuaNil,
    level: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER),
    /,
) -> PyLuaRet:
    return basic_error(scope, message, level)


def basic_error(
    scope: Scope,
    message: LuaValue,
    level: LuaNumber,
    /,
) -> PyLuaRet:
    """error(message[, level])"""
    #  Raises an error (see §2.3) with message as the error object.
    #  This function never returns.
    raise LuaError(message)
    # TODO:
    # Usually, error adds some information about the error position at the
    # beginning of the message, if the message is a string.
    # The level argument specifies how to get the error position.
    # With level 1 (the default), the error position is where the error
    # function was called. Level 2 points the error to where the function
    # that called error was called; and so on. Passing a level 0 avoids the
    # addition of error position information to the message.


@lua_function(name="getmetatable")
def lf_getmetatable(object: LuaValue, /) -> PyLuaRet:
    return basic_getmetatable(object)


def basic_getmetatable(object: LuaValue, /) -> PyLuaRet:
    """getmetatable(object)"""
    # If object does not have a metatable, returns nil.
    # Otherwise, if the object's metatable has a __metatable field,
    # returns the associated value.
    # Otherwise, returns the metatable of the given object.
    mt = object.get_metatable()
    if mt is LuaNil:
        return [mt]
    return [mt.get_with_fallback(SYMBOL_METATABLE, mt)]


@lua_function(name="ipairs")
def lf_ipairs(t: LuaTable, /) -> PyLuaRet:
    return basic_ipairs(t)


@lua_function()
def _ipairs_iterator_function(state, control_variable: LuaNumber, /) \
        -> PyLuaRet:
    index = control_variable.value + 1
    if index > MAX_INT64:
        return None
    index_val = LuaNumber(index, LuaNumberType.INTEGER)
    value = state.rawget(index_val)
    if value is LuaNil:
        return None
    return [index_val, value]


def basic_ipairs(t: LuaTable, /) -> PyLuaRet:
    """ipairs (t)"""

    # Returns three values (an iterator function, the table t, and 0) so
    # that the construction
    #      for i,v in ipairs(t) do body end
    # will iterate over the key–value pairs (1,t[1]), (2,t[2]), ..., up
    # to the first absent index.

    return [_ipairs_iterator_function, t, LuaNumber(0)]


@lua_function(name="load", gets_scope=True)
def lf_load(
    scope: Scope,
    chunk: LuaString | LuaFunction,
    chunk_name: LuaString | None = None,
    mode: LuaString | None = None,
    env: LuaTable | None = None,
    /,
) -> PyLuaRet:
    return basic_load(scope, chunk, chunk_name, mode, env)


def basic_load(
    scope: Scope,
    chunk: LuaString | LuaFunction,
    chunkname: LuaString | None = None,
    mode: LuaString | None = None,
    env: LuaTable | None = None,
    /,
) -> PyLuaRet:
    """load (chunk [, chunkname [, mode [, env]]])"""
    # Loads a chunk.
    #
    chunk_content = BytesIO()
    # If chunk is a string, the chunk is this string.
    if isinstance(chunk, LuaString):
        # chunkname is used as the name of the chunk for error messages and
        # debug information (see §4.7). When absent, it defaults to chunk,
        # if chunk is a string, or to "=(load)" otherwise.
        if chunkname is None:
            chunkname = LuaString(b"chunk")
        chunk_content.write(chunk.content)
        chunk_content.seek(0)
    # If chunk is a function, load calls it repeatedly to get the chunk pieces.
    elif isinstance(chunk, LuaFunction):
        # chunkname is used as the name of the chunk for error messages and
        # debug information (see §4.7). When absent, it defaults to chunk,
        # if chunk is a string, or to "=(load)" otherwise.
        if chunkname is None:
            chunkname = LuaString(b"=(load)")
        while True:
            # Each call to chunk must return a string that concatenates with
            # previous results.
            # A return of an empty string, nil, or no value signals the end of
            # the chunk.
            chunk_piece = call(chunk, [], scope=None)
            if (
                not chunk_piece
                or chunk_piece[0] is LuaNil
                or (
                    isinstance(chunk_piece[0], LuaString)
                    and not chunk_piece[0].content
                )
            ):
                break
            if not isinstance(chunk_piece[0], LuaString):
                raise LuaError("load: chunk() must return a string")
            chunk_content.write(chunk_piece[0].content)
        chunk_content.seek(0)
    else:
        raise LuaError("load: chunk must be a string or a function")
    # If there are no syntactic errors, load returns the compiled chunk as a
    # function; otherwise, it returns fail plus the error message.
    try:
        chunk_name_str = chunkname.content.decode("utf-8")
        parsed_chunk = chunk_parser.parse(chunk_content.read().decode("utf-8"))
        chunk_node: Chunk = transformer.transform(
            parsed_chunk, filename=chunk_name_str
        )
        from mehtap.scope import Scope

        return LuaFunction(
            param_names=[],
            variadic=False,
            parent_scope=Scope(scope.vm, None),
            block=chunk_node.block,
            gets_scope=False,
        )
    except Exception as e:
        return [FAIL, py2lua(str(e))]
    # TODO: The following is not implemented:
    # When you load a main chunk, the resulting function will always have
    # exactly one upvalue, the _ENV variable (see §2.2). However, when you load
    # a binary chunk created from a function (see string.dump), the resulting
    # function can have an arbitrary number of upvalues, and there is no
    # guarantee that its first upvalue will be the _ENV variable. (A non-main
    # function may not even have an _ENV upvalue.)
    #
    # Regardless, if the resulting function has any upvalues, its first upvalue
    # is set to the value of env, if that parameter is given, or to the value of
    # the global environment. Other upvalues are initialized with nil. All
    # upvalues are fresh, that is, they are not shared with any other function.
    #
    # The string mode controls whether the chunk can be text or binary (that is,
    # a precompiled chunk). It may be the string "b" (only binary chunks), "t"
    # (only text chunks), or "bt" (both binary and text). The default is "bt".
    #
    # It is safe to load malformed binary chunks; load signals an appropriate
    # error. However, Lua does not check the consistency of the code inside
    # binary chunks; running maliciously crafted bytecode can crash the
    # interpreter.


@lua_function(name="loadfile", gets_scope=True)
def lf_loadfile(
    scope: Scope,
    filename: LuaString | None = None,
    mode: LuaString | None = None,
    env: LuaTable | None = None,
    /,
) -> PyLuaRet:
    return basic_loadfile(scope, filename, mode, env)


def basic_loadfile(
    scope: Scope,
    filename: LuaString | None = None,
    mode: LuaString | None = None,
    env: LuaTable | None = None,
    /,
) -> PyLuaRet:
    """loadfile ([filename [, mode [, env]]])"""
    # Similar to load, but gets the chunk from file filename
    # or from the standard input, if no file name is given.
    try:
        if filename is None:
            return basic_load(
                scope,
                LuaString(input().encode("utf-8")),
                LuaString(b"stdin"), mode, env,
            )
        if not isinstance(filename, LuaString):
            raise LuaError("bad argument #1 to 'loadfile' (string expected)")
        with open(filename.content, "rb") as f:
            return basic_load(
                scope,
                LuaString(f.read()),
                filename,
                mode, env,
            )
    except Exception as e:
        return [FAIL, py2lua(str(e))]


@lua_function(name="next")
def lf_next(table: LuaTable, index: LuaValue = LuaNil, /) -> PyLuaRet:
    return basic_next(table, index)


def basic_next(table: LuaTable, index: LuaValue = LuaNil, /) -> PyLuaRet:
    """next (table [, index])"""
    # Allows a program to traverse all fields of a table.
    # Its first argument is a table and its second argument is an index
    # in this table.
    # A call to next returns the next index of the table and its
    # associated value.
    # When called with nil as its second argument, next returns an
    # initial index and its associated value.
    # When called with the last index, or with nil in an empty table,
    # next returns nil.
    # If the second argument is absent, then it is interpreted as nil.
    # In particular, you can use next(t) to check whether a table is
    # empty.
    #
    # The order in which the indices are enumerated is not specified,
    # even for numeric indices.
    # (To traverse a table in numerical order, use a numerical for.)
    #
    # You should not assign any value to a non-existent field in a table
    # during its traversal.
    # You may however modify existing fields.
    # In particular, you may set existing fields to nil.
    if not isinstance(table, LuaTable):
        table_type = type_of_lv(table)
        raise LuaError(
            f"bad argument #1 to 'next' (table expected, got {table_type})"
        )
    if index is LuaNil:
        iterator = iter(table.map.items())
        try:
            k, v = next(iterator)
        except StopIteration:
            return [LuaNil]
        return [k, v]
    iterator = iter(table.map.items())
    for k, v in iterator:
        if rel_eq(k, index).true:
            break
    else:
        return [LuaNil]
    # return the next pair for which v isn't nil
    while True:
        try:
            k, v = next(iterator)
        except StopIteration:
            return [LuaNil]
        if v is not LuaNil:
            return [k, v]


@lua_function(name="pairs", gets_scope=True)
def lf_pairs(scope: Scope, t: LuaTable, /) -> list[LuaValue] | None:
    return basic_pairs(scope, t)


def basic_pairs(scope: Scope, t: LuaTable, /) -> list[LuaValue] | None:
    """pairs (t)"""
    # If t has a metamethod __pairs, calls it with t as argument and
    # returns the first three results from the call.
    metamethod = t.get_metavalue(SYMBOL_PAIRS)
    if metamethod is not None:
        return call(metamethod, [t], scope)
    # Otherwise, returns three values: the next function, the table t, and
    # nil, so that the construction
    #      for k,v in pairs(t) do body end
    # will iterate over all key–value pairs of table t.
    return [lf_next, t, LuaNil]


@lua_function(name="pcall", gets_scope=True)
def lf_pcall(
    scope: Scope,
    f: LuaFunction,
    /,
    *args: LuaValue,
):
    return basic_pcall(scope, f, *args)


def basic_pcall(
    scope: Scope,
    f: LuaFunction,
    /,
    *args: LuaValue,
):
    """pcall (f [, arg1, ···])"""
    #  Calls the function f with the given arguments in protected mode.
    #  This means that any error inside f is not propagated;
    #  instead, pcall catches the error and returns a status code.
    #  Its first result is the status code (a boolean), which is true
    #  if the call succeeds without errors.
    #  In such case, pcall also returns all results from the call,
    #  after this first result.
    #  In case of any error, pcall returns false plus the error object.
    #  Note that errors caught by pcall do not call a message handler.
    try:
        return_vals = call(f, list(args), scope)
    except LuaError as lua_error:
        return [LuaBool(False), lua_error.message]
    else:
        return [LuaBool(True), *return_vals]


@lua_function(name="print", gets_scope=True)
def lf_print(scope: Scope, /, *args: LuaValue) -> PyLuaRet:
    return basic_print(scope, *args)


def basic_print(scope: Scope, /, *args: LuaValue) -> PyLuaRet:
    """print (···)"""
    # Receives any number of arguments and prints their values to stdout,
    # converting each argument to a string following the same rules of
    # tostring.
    #
    # The function print is not intended for formatted output, but only as a
    # quick way to show a value, for instance for debugging.
    # For complete control over the output, use string.format and io.write.
    string_lists = (basic_tostring(scope, v) for v in args)
    x = "\t".join(
        ",".join(string.content.decode("utf-8") for string in string_list)
        for string_list in string_lists
    )
    print(x)
    return None


@lua_function(name="rawequal")
def lf_rawequal(v1, v2, /) -> PyLuaRet:
    return basic_rawequal(v1, v2)


def basic_rawequal(v1, v2, /) -> PyLuaRet:
    """rawequal (v1, v2)"""
    # Checks whether v1 is equal to v2, without invoking the __eq
    # metamethod.
    # Returns a boolean.
    return [rel_eq(v1, v2, raw=True)]


@lua_function(name="rawget")
def lf_rawget(
    table: LuaTable,
    index: LuaValue,
    /,
) -> PyLuaRet:
    return basic_rawget(table, index)


def basic_rawget(
    table: LuaTable,
    index: LuaValue,
    /,
) -> PyLuaRet:
    """rawget (table, index)"""
    # Gets the real value of table[index], without using the __index
    # metavalue.
    # table must be a table; index may be any value.
    if not isinstance(table, LuaTable):
        raise LuaError("'table' must be a table")
    return [table.rawget(index)]


@lua_function(name="rawlen")
def lf_rawlen(v: LuaTable | LuaString, /) -> PyLuaRet:
    return basic_rawlen(v)


def basic_rawlen(v: LuaTable | LuaString, /) -> PyLuaRet:
    """rawlen (v)"""
    # Returns the length of the object v, which must be a table or a string,
    # without invoking the __len metamethod. Returns an integer.
    if not isinstance(v, (LuaTable, LuaString)):
        raise LuaError("'v' must be a table or a string")
    return [length(v, raw=True)]


@lua_function(name="rawset")
def lf_rawset(table: LuaTable, index: LuaValue, value: LuaValue, /) -> PyLuaRet:
    return basic_rawset(table, index, value)


def basic_rawset(
    table: LuaTable, index: LuaValue, value: LuaValue, /
) -> PyLuaRet:
    """rawset (table, index, value)"""
    #  Sets the real value of table[index] to value, without using the
    #  __newindex metavalue.
    #  table must be a table, index any value different from nil and NaN,
    #  and value any Lua value.
    #
    # This function returns table.
    table.rawput(index, value)
    return [table]


@lua_function(name="select")
def lf_select(index, /, *a) -> PyLuaRet:
    return basic_select(index, *a)


def basic_select(index, /, *a) -> PyLuaRet:
    """select (index, ···)"""
    # If index is a number,
    if isinstance(index, LuaNumber):
        # returns all arguments after argument number index;
        if index.type == LuaNumberType.FLOAT:
            raise LuaError(
                "bad argument #1 to 'select' (integer expected, got float)"
            )
        index = int(index.value)
        # a negative number indexes from the end (-1 is the last argument).
        if index == 0 or index < -len(a):
            raise LuaError("bad argument #1 to 'select' (index out of range)")
        return list(a[index - 1 :])
    # Otherwise, index must be the string "#",
    if index != LuaString(b"#"):
        raise LuaError(
            "bad argument #1 to 'select' " "(must be integer or the string '#')"
        )
    # and select returns the total number of extra arguments it received.
    return [LuaNumber(len(a), LuaNumberType.INTEGER)]


@lua_function(name="setmetatable")
def lf_setmetatable(
    table: LuaTable,
    metatable: LuaTable | LuaNilType,
    /,
) -> PyLuaRet:
    return basic_setmetatable(table, metatable)


def basic_setmetatable(
    table: LuaTable,
    metatable: LuaTable | LuaNilType,
    /,
) -> PyLuaRet:
    """setmetatable (table, metatable)"""
    # Sets the metatable for the given table.
    # If the original metatable has a __metatable field, raises an error.
    if table.has_metavalue(SYMBOL_METATABLE):
        raise LuaError("cannot change a protected metatable")
    # If metatable is nil, removes the metatable of the given table.
    if metatable is LuaNil:
        table.remove_metatable()
        return [table]
    table.set_metatable(metatable)
    # This function returns table.
    return [table]
    # To change the metatable of other types from Lua code, you must use the
    # debug library (§6.10).


@lua_function(name="tonumber", gets_scope=True)
def lf_tonumber(scope: Scope, e, base=None, /) -> PyLuaRet:
    return basic_tonumber(scope, e, base)


def basic_tonumber(scope: Scope, e, base=None, /) -> PyLuaRet:
    """tonumber (e [, base])"""
    # When called with no base, tonumber tries to convert its argument to a
    # number.
    # If the argument is already a number or a string convertible to a
    # number, then tonumber returns this number; otherwise, it returns fail.
    #
    # The conversion of strings can result in integers or floats, according
    # to the lexical conventions of Lua (see §3.1). The string may have
    # leading and trailing spaces and a sign.
    if base is None:
        if isinstance(e, LuaNumber):
            return [e]
        if isinstance(e, LuaString):
            try:
                e_str = e.content.strip().decode("utf-8")
                if e_str[0] == "-":
                    return [
                        UnaryOperation(
                            op=UnaryOperator.NEG,
                            exp=transformer.transform(
                                numeral_parser.parse(e_str[1:])
                            ),
                        ).evaluate_single(scope)
                    ]

                if e_str[0] == "+":
                    e_str = e_str[1:]
                return [
                    transformer.transform(
                        numeral_parser.parse(e_str)
                    ).evaluate_single(scope)
                ]
            except Exception:
                return [FAIL]
    # When called with base, then e must be a string to be interpreted as an
    # integer numeral in that base. The base may be any integer between
    # 2 and 36, inclusive.
    if not isinstance(e, LuaString):
        raise LuaError(
            f"bad argument to 'tonumber' "
            f"(string expected, got {type_of_lv(e)})"
        )
    # In bases above 10, the letter 'A' (in either upper or lower case)
    # represents 10, 'B' represents 11, and so forth, with 'Z' representing
    # 35. If the string e is not a valid numeral in the given base, the
    # function returns fail.
    acc = 0
    e_str = e.content.strip().decode("utf-8")
    if e_str[0] in ("+", "-"):
        start = 1
    else:
        start = 0
    for i, c in enumerate(e_str[start:]):
        if "0" <= c <= "9":
            digit = int(c)
        elif "a" <= c <= "z":
            digit = ord(c) - ord("a") + 10
        elif "A" <= c <= "Z":
            digit = ord(c) - ord("A") + 10
        else:
            return [FAIL]
        if digit >= base.value:
            return [FAIL]
        acc = acc * base.value + digit
    if acc < MAX_INT64:
        number = LuaNumber(acc, LuaNumberType.INTEGER)
    else:
        number = LuaNumber(-1, LuaNumberType.INTEGER)
    if e_str[0] == "-":
        number.value = -number.value
    return [number]


@lua_function(name="tostring", gets_scope=True)
def lf_tostring(scope: Scope, v: LuaValue, /) -> PyLuaRet:
    return basic_tostring(scope, v)


def basic_tostring(scope: Scope, v: LuaValue, /) -> PyLuaRet:
    """tostring (v)"""
    # Receives a value of any type and converts it to a string in a
    # human-readable format.
    #
    # If the metatable of v has a __tostring field,
    tostring_field = v.get_metavalue(SYMBOL_TOSTRING)
    if tostring_field is not None:
        # then tostring calls the corresponding value with v as argument,
        # and uses the result of the call as its result.
        return call(tostring_field, [v], scope)
    # Otherwise, if the metatable of v has a __name field with a string
    # value,
    name_field = v.get_metavalue(SYMBOL_NAME)
    if name_field is not None and isinstance(name_field, LuaString):
        # tostring may use that string in its final result.
        decoded_name = name_field.content.decode("utf-8")
        return [LuaString(f"{decoded_name}: {v}".encode("utf-8"))]
    # For complete control of how numbers are converted, use string.format.
    return [LuaString(str(v).encode("utf-8"))]


@lua_function(name="type")
def lf_type(v: LuaValue, /) -> PyLuaRet:
    return basic_type(v)


def basic_type(v: LuaValue, /) -> PyLuaRet:
    """type (v)"""
    #  Returns the type of its only argument, coded as a string.
    #  The possible results of this function are "nil"
    #  (a string, not the value nil),
    #  "number", "string", "boolean", "table", "function", "thread", and
    #  "userdata".
    return [LuaString(type_of_lv(v).encode("ascii"))]


@lua_function(name="warn", gets_scope=True)
def lf_warn(scope: Scope, msg1: LuaString, /, *a: LuaString) -> PyLuaRet:
    return basic_warn(scope, msg1, *a)


def basic_warn(scope: Scope, msg1: LuaString, /, *a: LuaString) -> None:
    """warn (msg1, ···)"""
    # Emits a warning with a message composed by the concatenation of all
    # its arguments (which should be strings).
    #
    # By convention, a one-piece message starting with '@' is intended to be
    # a control message, which is a message to the warning system itself.
    for i, v in enumerate([msg1, *a], start=1):
        if not isinstance(v, LuaString):
            raise LuaError(
                f"bad argument #{i} to 'warn' "
                f"(string expected, got {type_of_lv(v)})"
            )
    if not a and msg1.content.startswith(b"@"):
        # In particular, the standard warning function in Lua recognizes the
        # control messages
        if msg1.content == b"@off":
            # "@off", to stop the emission of warnings,
            scope.vm.emitting_warnings = False
        elif msg1.content == b"@on":
            # and "@on", to (re)start the emission;
            scope.vm.emitting_warnings = True
        # it ignores unknown control messages.
        return None
    if not scope.vm.emitting_warnings:
        return None
    scope.vm.get_warning(msg1, *a)
    return None


@lua_function(name="xpcall", gets_scope=True)
def lf_xpcall(
    scope: Scope,
    f: LuaFunction,
    msgh: LuaFunction,
    /,
    *args: LuaFunction,
) -> list[LuaValue] | None:
    return basic_xpcall(scope, f, msgh, *args)


def basic_xpcall(
    scope: Scope,
    f: LuaFunction,
    msgh: LuaFunction,
    /,
    *args: LuaFunction,
) -> list[LuaValue] | None:
    #  This function is similar to pcall, except that it sets a new message
    #  handler msgh.
    try:
        return_vals = call(f, list(args), scope)
    except LuaError as lua_error:
        # Any error inside f is not propagated;
        # instead, xpcall catches the error,
        # calls msgh with the original error object,
        # and returns a status code.
        return [
            # In case of any error, xpcall returns false
            LuaBool(False),
            # plus the result from msgh.
            *call(msgh, [lua_error.message], scope),
        ]
    else:
        return [
            # Its first result is the status code (a boolean),
            # which is true if the call succeeds without errors.
            LuaBool(True),
            # In such case, xpcall also returns all results from the call,
            # after this first result.
            *return_vals,
        ]


class BasicLibrary(LibraryProvider):
    def provide(self, global_table: LuaTable) -> None:
        from mehtap import __version__

        # _VERSION
        #  A global variable (not a function) that holds a string containing the
        #  running Lua version.
        #  The current value of this variable is "Lua 5.4".
        global_table.rawput(
            LuaString(b"_VERSION"),
            LuaString(f"mehtap {__version__}".encode("ascii")),
        )

        # _G
        # A global variable (not a function) that holds the global environment
        # (see §2.2).
        # Lua itself does not use this variable; changing its value does not
        # affect any environment, nor vice versa.
        global_table.rawput(LuaString(b"_G"), global_table)

        for name_of_global, value_of_global in globals().items():
            if name_of_global.startswith("lf_"):
                assert isinstance(value_of_global, LuaFunction)
                assert value_of_global.name
                global_table.rawput(
                    LuaString(value_of_global.name.encode("ascii")),
                    value_of_global,
                )
