from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ay import operations
from ay.ast_nodes import call_function, UnaryOperation, Terminal, UnaryOperator
from ay.ast_transformer import transformer
from ay.util.py_lua_function import LibraryProvider, PyLuaRet
from ay.util.py_lua_function import lua_function
from ay.values import (
    LuaTable,
    LuaValue,
    LuaNil,
    LuaString,
    LuaNumber,
    LuaNumberType,
    MAX_INT64,
    LuaFunction
)
from ay.control_structures import LuaError
from ay.values import LuaBool
from ay.parser import chunk_parser, numeral_parser
from ay.operations import rel_eq, length

if TYPE_CHECKING:
    from ay.vm import StackFrame
    from ay.values import LuaNilType


SYMBOL_METATABLE = LuaString(b"__metatable")
SYMBOL_PAIRS = LuaString(b"__pairs")
SYMBOL_TOSTRING = LuaString(b"__tostring")
SYMBOL_NAME = LuaString(b"__name")


FAIL = LuaNil


def provide(table: LuaTable) -> None:
    @lua_function(table, name="assert")
    def assert_(v: LuaValue, message: LuaValue = LuaNil, /, *a) -> PyLuaRet:
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

    @lua_function(table, gets_stack_frame=True)
    def collectgarbage(vm, /) -> PyLuaRet:
        """collectgarbage ([opt [, arg]])"""
        call_function(
            vm,
            warn,
            [
                LuaString(
                    b"collectgarbage(): ay doesn't have garbage collection."
                )
            ],
        )
        return [LuaNil]

    @lua_function(table, gets_stack_frame=True)
    def dofile(
        frame: StackFrame,
        filename: LuaString | None = None,
        /,
    ) -> PyLuaRet:
        """dofile ([filename])"""
        #  Opens the named file and executes its content as a Lua chunk.
        #  When called without arguments, dofile executes the content of the
        #  standard input (stdin).
        infile = sys.stdin
        if filename is not None:
            if isinstance(filename, LuaString):
                infile = open(filename.content, "r", encoding="utf-8")
            else:
                raise LuaError("bad argument #1 to 'dofile' (string expected)")
        #  Returns all values returned by the chunk. In case of errors,
        #  dofile propagates the error to its caller.
        #  (That is, dofile does not run in protected mode.)
        parsed_chunk = chunk_parser.parse(infile.read())
        chunk_node = transformer.transform(parsed_chunk)
        r = chunk_node.block.evaluate(frame)
        return r

    @lua_function(table, gets_stack_frame=True)
    def error(
        frame: StackFrame,
        message: LuaValue = LuaNil,
        level: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER),
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

    # _G
    # A global variable (not a function) that holds the global environment
    # (see §2.2).
    # Lua itself does not use this variable; changing its value does not
    # affect any environment, nor vice versa.
    table.put(LuaString(b"_G"), table)

    @lua_function(table)
    def getmetatable(object: LuaValue, /) -> PyLuaRet:
        """getmetatable(object)"""
        # If object does not have a metatable, returns nil.
        # Otherwise, if the object's metatable has a __metatable field,
        # returns the associated value.
        # Otherwise, returns the metatable of the given object.
        mt = object.get_metatable()
        if mt is LuaNil:
            return [mt]
        return [mt.get_with_fallback(SYMBOL_METATABLE, mt)]

    @lua_function(table)
    def ipairs(t: LuaTable, /) -> PyLuaRet:
        """ipairs (t)"""

        # Returns three values (an iterator function, the table t, and 0) so
        # that the construction
        #      for i,v in ipairs(t) do body end
        # will iterate over the key–value pairs (1,t[1]), (2,t[2]), ..., up
        # to the first absent index.
        @lua_function()
        def iterator_function(state, control_variable: LuaNumber, /) -> PyLuaRet:
            index = control_variable.value + 1
            if index > MAX_INT64:
                return None
            index_val = LuaNumber(index, LuaNumberType.INTEGER)
            value = t.get(index_val)
            if value is LuaNil:
                return None
            return [index_val, value]

        return [
            iterator_function,
            t,
            LuaNumber(0, LuaNumberType.INTEGER),
        ]

    @lua_function(table)
    def load(
        chunk: LuaString | LuaFunction,
        chunk_name: LuaString | None = None,
        mode: LuaString | None = None,
        env: LuaTable | None = None,
        /,
    ) -> PyLuaRet:
        """load (chunk [, chunkname [, mode [, env]]])"""
        raise NotImplementedError()  # todo.

    @lua_function(table)
    def loadfile(
        filename: LuaString | None = None,
        mode: LuaString | None = None,
        env: LuaTable | None = None,
        /,
    ) -> PyLuaRet:
        """loadfile ([filename [, mode [, env]]])"""
        raise NotImplementedError()  # todo.

    @lua_function(table, name="next")
    def next_(table: LuaTable, index: LuaValue = LuaNil, /) -> PyLuaRet:
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
        raise NotImplementedError()  # todo.

    @lua_function(table, gets_stack_frame=True)
    def pairs(frame: StackFrame, t: LuaTable, /) -> list[LuaValue] | None:
        """pairs (t)"""
        # If t has a metamethod __pairs, calls it with t as argument and
        # returns the first three results from the call.
        metamethod = t.get_metamethod(SYMBOL_PAIRS)
        if metamethod is not None:
            if not isinstance(metamethod, LuaFunction):
                raise NotImplementedError()
            return call_function(frame, metamethod, [t])
        # Otherwise, returns three values: the next function, the table t, and
        # nil, so that the construction
        #      for k,v in pairs(t) do body end
        # will iterate over all key–value pairs of table t.
        items = iter(t.map.items())

        # TODO: Implement this function in a way that uses state.
        @lua_function()
        def iterator_function(state, control_variable, /) -> PyLuaRet:
            try:
                key, value = next(items)
            except StopIteration:
                return None
            return [key, value]

        return [
            iterator_function,
            t,
            LuaNil,
        ]

    @lua_function(table, gets_stack_frame=True)
    def pcall(
        frame: StackFrame,
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
            return_vals = call_function(frame, f, list(args))
        except LuaError as lua_error:
            return [LuaBool(False), lua_error.message]
        else:
            return [LuaBool(True), *return_vals]

    @lua_function(table, name="print", gets_stack_frame=True)
    def print_(frame: StackFrame, /, *args: LuaValue) -> PyLuaRet:
        """print (···)"""
        # Receives any number of arguments and prints their values to stdout,
        # converting each argument to a string following the same rules of
        # tostring.
        #
        # The function print is not intended for formatted output, but only as a
        # quick way to show a value, for instance for debugging.
        # For complete control over the output, use string.format and io.write.
        string_lists = (call_function(frame, tostring, [arg]) for arg in args)
        x = "\t".join(
            ",".join(string.content.decode("utf-8") for string in string_list)
            for string_list in string_lists
        )
        print(x)
        return None

    @lua_function(table)
    def rawequal(v1, v2, /) -> PyLuaRet:
        """rawequal (v1, v2)"""
        # Checks whether v1 is equal to v2, without invoking the __eq
        # metamethod.
        # Returns a boolean.
        return [rel_eq(v1, v2, raw=True)]

    @lua_function(table)
    def rawget(
        table: LuaTable,
        index: LuaValue,
        /,
    ) -> PyLuaRet:
        """rawget (table, index)"""
        # Gets the real value of table[index], without using the __index
        # metavalue.
        # table must be a table; index may be any value.
        assert isinstance(table, LuaTable)
        return [table.get(index, raw=True)]

    @lua_function(table)
    def rawlen(v: LuaTable | LuaString, /) -> PyLuaRet:
        """rawlen (v)"""
        # Returns the length of the object v, which must be a table or a string,
        # without invoking the __len metamethod. Returns an integer.
        assert isinstance(v, (LuaTable, LuaString))
        return [length(v, raw=True)]

    @lua_function(table)
    def rawset(
        table: LuaTable,
        index: LuaValue,
        value: LuaValue,
        /,
    ) -> PyLuaRet:
        """rawset (table, index, value)"""
        #  Sets the real value of table[index] to value, without using the
        #  __newindex metavalue.
        #  table must be a table, index any value different from nil and NaN,
        #  and value any Lua value.
        #
        # This function returns table.
        table.put(index, value, raw=True)
        return [table]

    @lua_function(table, name="select")
    def select(index, /, *a) -> PyLuaRet:
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
                raise LuaError(
                    "bad argument #1 to 'select' (index out of range)"
                )
            return list(a[index - 1:])
        # Otherwise, index must be the string "#",
        if index != LuaString(b"#"):
            raise LuaError(
                "bad argument #1 to 'select' "
                "(must be integer or the string '#')"
            )
        # and select returns the total number of extra arguments it received.
        return [LuaNumber(len(a), LuaNumberType.INTEGER)]

    @lua_function(table)
    def setmetatable(
        table: LuaTable,
        metatable: LuaTable | LuaNilType,
        /,
    ) -> PyLuaRet:
        """setmetatable (table, metatable)"""
        # Sets the metatable for the given table.
        assert isinstance(table, LuaTable)
        # If the original metatable has a __metatable field, raises an error.
        if table.has_metamethod(SYMBOL_METATABLE):
            raise LuaError("cannot change a protected metatable")
        # If metatable is nil, removes the metatable of the given table.
        if metatable is LuaNil:
            table.set_metatable(LuaNil)
            return [table]
        table.set_metatable(metatable)
        # This function returns table.
        return [table]
        # To change the metatable of other types from Lua code, you must use the
        # debug library (§6.10).

    @lua_function(table, gets_stack_frame=True)
    def tonumber(frame: StackFrame, e, base=None, /) -> PyLuaRet:
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
                            ).evaluate(frame)
                        ]

                    if e_str[0] == "+":
                        e_str = e_str[1:]
                    return [
                        transformer.transform(
                            numeral_parser.parse(e_str)
                        ).evaluate(frame)
                    ]
                except Exception:
                    return [FAIL]
        # When called with base, then e must be a string to be interpreted as an
        # integer numeral in that base. The base may be any integer between
        # 2 and 36, inclusive.
        if not isinstance(e, LuaString):
            raise LuaError(
                f"bad argument to 'tonumber' "
                f"(string expected, got {operations.type_(e)!s})"
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

    @lua_function(table, gets_stack_frame=True)
    def tostring(frame: StackFrame, v: LuaValue, /) -> PyLuaRet:
        """tostring (v)"""
        # Receives a value of any type and converts it to a string in a
        # human-readable format.
        #
        # If the metatable of v has a __tostring field,
        tostring_field = v.get_metamethod(SYMBOL_TOSTRING)
        if tostring_field is not None:
            # then tostring calls the corresponding value with v as argument,
            if not isinstance(tostring_field, LuaFunction):
                raise NotImplementedError()
            call_result = call_function(frame, tostring_field, [v])
            # and uses the result of the call as its result.
            return call_result
        # Otherwise, if the metatable of v has a __name field with a string
        # value,
        name_field = v.get_metamethod(SYMBOL_NAME)
        if name_field is not None and isinstance(name_field, LuaString):
            # tostring may use that string in its final result.
            decoded_name = name_field.content.decode("utf-8")
            return [LuaString(f"{decoded_name}: {v}".encode("utf-8"))]
        # For complete control of how numbers are converted, use string.format.
        return [LuaString(str(v).encode("utf-8"))]

    @lua_function(table, name="type")
    def type_(v: LuaValue, /) -> PyLuaRet:
        """type (v)"""
        #  Returns the type of its only argument, coded as a string.
        #  The possible results of this function are "nil"
        #  (a string, not the value nil),
        #  "number", "string", "boolean", "table", "function", "thread", and
        #  "userdata".
        return [operations.type_(v)]

    from ay import __ay_version__

    # _VERSION
    #  A global variable (not a function) that holds a string containing the
    #  running Lua version.
    #  The current value of this variable is "Lua 5.4".
    table.put(
        LuaString(b"_VERSION"),
        LuaString(f"ay {__ay_version__}".encode("utf-8")),
    )

    @lua_function(table, gets_stack_frame=True)
    def warn(frame: StackFrame, msg1: LuaString, /, *a: LuaString) -> PyLuaRet:
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
                    f"(string expected, got {operations.type_(v)!s})"
                )
        if not a and msg1.content.startswith(b"@"):
            # In particular, the standard warning function in Lua recognizes the
            # control messages
            if msg1.content == b"@off":
                # "@off", to stop the emission of warnings,
                frame.vm.emitting_warnings = False
            elif msg1.content == b"@on":
                # and "@on", to (re)start the emission;
                frame.vm.emitting_warnings = True
            # it ignores unknown control messages.
            return None
        if not frame.vm.emitting_warnings:
            return None
        print("Warning: ", msg1, *a, sep="", file=sys.stderr)
        return None

    @lua_function(table, gets_stack_frame=True)
    def xpcall(
        frame: StackFrame,
        f: LuaFunction,
        msgh: LuaFunction,
        /,
        *args: LuaFunction,
    ) -> list[LuaValue] | None:
        #  This function is similar to pcall, except that it sets a new message
        #  handler msgh.
        try:
            return_vals = call_function(frame, f, list(args))
        except LuaError as lua_error:
            # Any error inside f is not propagated;
            # instead, xpcall catches the error,
            # calls msgh with the original error object,
            # and returns a status code.
            return [
                # In case of any error, xpcall returns false
                LuaBool(False),
                # plus the result from msgh.
                *call_function(frame, msgh, [lua_error.message]),
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


library_table = LuaTable()
provide(library_table)


class BasicLibrary(LibraryProvider):
    def provide(self, table: LuaTable) -> None:
        provide(table)
