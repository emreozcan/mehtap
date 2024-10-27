from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from ay.ast_nodes import call_function, Unary, Terminal
from ay.ast_transformer import transformer
from ay.util.py_lua_function import LibraryProvider, PyLuaRet
from ay.util.py_lua_function import lua_function
from ay.values import LuaTable, LuaValue, LuaNil, LuaString, LuaNumber, \
    LuaNumberType, MAX_INT64, LuaFunction, LuaNilType, LuaThread, LuaUserdata
from ay.control_structures import LuaError
from ay.values import LuaBool
from ay.parser import chunk_parser, numeral_parser
from ay.operations import rel_eq, length, rel_ne

if TYPE_CHECKING:
    from vm import VirtualMachine


SYMBOL_METATABLE = LuaString(b"__metatable")
SYMBOL_PAIRS = LuaString(b"__pairs")
SYMBOL_TOSTRING = LuaString(b"__tostring")
SYMBOL_NAME = LuaString(b"__name")


FAIL = LuaNil


def provide(table: LuaTable) -> None:
    @lua_function(table, name="assert")
    def assert_(v: LuaValue, message: LuaValue = None) -> PyLuaRet:
        """assert (v [, message])"""
        #  Raises an error if the value of its argument v is false
        #  (i.e., nil or false);
        if v is LuaNil or (isinstance(v, LuaBool) and not v.true):
            #  In case of error, message is the error object;
            if message is not None:
                raise LuaError(message)
            #  when absent, it defaults to "assertion failed!"
            raise LuaError("assertion failed!")
        #  otherwise, returns all its arguments.
        return [v, message]

    @lua_function(table)
    def collectgarbage() -> PyLuaRet:
        """collectgarbage ([opt [, arg]])"""
        raise NotImplementedError()

    @lua_function(table, interacts_with_the_vm=True)
    def dofile(
            vm: VirtualMachine,
            filename: LuaString | None = None,
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
                raise LuaError(
                    "bad argument #1 to 'dofile' (string expected)"
                )
        #  Returns all values returned by the chunk. In case of errors,
        #  dofile propagates the error to its caller.
        #  (That is, dofile does not run in protected mode.)
        parsed_chunk = chunk_parser.parse(infile.read())
        chunk_node = transformer.transform(parsed_chunk)
        r = chunk_node.block.evaluate(vm)
        return r

    @lua_function(table, interacts_with_the_vm=True)
    def error(
            vm: VirtualMachine,
            message: LuaValue,
            level: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER)
    ) -> PyLuaRet:
        """error(message[, level])"""
        raise NotImplementedError()  # todo.

    # _G
    # A global variable (not a function) that holds the global environment
    # (see §2.2).
    # Lua itself does not use this variable; changing its value does not
    # affect any environment, nor vice versa.

    @lua_function(table)
    def getmetatable(object: LuaValue) -> PyLuaRet:
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
    def ipairs(t: LuaTable) -> PyLuaRet:
        """ipairs (t)"""

        # Returns three values (an iterator function, the table t, and 0) so
        # that the construction
        #      for i,v in ipairs(t) do body end
        # will iterate over the key–value pairs (1,t[1]), (2,t[2]), ..., up
        # to the first absent index.
        def iterator_function(state, control_variable: LuaNumber) \
                -> PyLuaRet:
            index = control_variable.value + 1
            if index > MAX_INT64:
                return None
            index_val = LuaNumber(index, LuaNumberType.INTEGER)
            value = t.get(index_val)
            if value is LuaNil:
                return None
            return [index_val, value]

        return [
            LuaFunction(
                param_names=[],
                variadic=False,
                parent_stack_frame=None,
                block=iterator_function
            ),
            t,
            LuaNumber(0, LuaNumberType.INTEGER),
        ]

    @lua_function(table)
    def load(
            chunk: LuaString | LuaFunction,
            chunk_name: LuaString | None = None,
            mode: LuaString | None = None,
            env: LuaTable | None = None
    ) -> PyLuaRet:
        """load (chunk [, chunkname [, mode [, env]]])"""
        raise NotImplementedError()  # todo.

    @lua_function(table)
    def loadfile(
            filename: LuaString | None = None,
            mode: LuaString | None = None,
            env: LuaTable | None = None
    ) -> PyLuaRet:
        """loadfile ([filename [, mode [, env]]])"""
        raise NotImplementedError()  # todo.

    @lua_function(table)
    def next(
            table: LuaTable,
            index: LuaValue = LuaNil
    ) -> PyLuaRet:
        """next (table [, index])"""
        #  Allows a program to traverse all fields of a table.
        #  Its first argument is a table and its second argument is an index
        #  in this table.
        #  A call to next returns the next index of the table and its
        #  associated value.
        #  When called with nil as its second argument, next returns an
        #  initial index and its associated value.
        #  When called with the last index, or with nil in an empty table,
        #  next returns nil.
        #  If the second argument is absent, then it is interpreted as nil.
        #  In particular, you can use next(t) to check whether a table is
        #  empty.
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

    @lua_function(table, interacts_with_the_vm=True)
    def pairs(vm: VirtualMachine, t: LuaTable) -> list[LuaValue] | None:
        """pairs (t)"""
        # If t has a metamethod __pairs, calls it with t as argument and
        # returns the first three results from the call.
        metamethod = t.get_metamethod(SYMBOL_PAIRS)
        if metamethod is not None:
            return call_function(vm, metamethod, [t])
        # Otherwise, returns three values: the next function, the table t, and
        # nil, so that the construction
        #      for k,v in pairs(t) do body end
        # will iterate over all key–value pairs of table t.
        items = iter(t.map.items())
        # TODO: Implement this function in a way that uses state.
        def iterator_function(state, control_variable) -> list[LuaValue] | None:
            try:
                key, value = next(items)
            except StopIteration:
                return
            return [key, value]

        return [
            LuaFunction(
                param_names=[],
                variadic=False,
                parent_stack_frame=None,
                block=iterator_function
            ),
            t,
            LuaNil,
        ]

    @lua_function(table, interacts_with_the_vm=True)
    def pcall(
            vm: VirtualMachine,
            f: LuaFunction,
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
            return_vals = call_function(vm, f, list(args))
        except LuaError as lua_error:
            return [LuaBool(False), lua_error.message]
        else:
            return [LuaBool(True), *return_vals]

    @lua_function(table, name="print", interacts_with_the_vm=True)
    def print_(vm: VirtualMachine, *args: LuaValue) -> PyLuaRet:
        """print (···)"""
        # Receives any number of arguments and prints their values to stdout,
        # converting each argument to a string following the same rules of
        # tostring.
        #
        # The function print is not intended for formatted output, but only as a
        # quick way to show a value, for instance for debugging.
        # For complete control over the output, use string.format and io.write.
        string_lists = (call_function(vm, tostring, [arg]) for arg in args)
        x = "\t".join(
            ",".join(string.content.decode("utf-8") for string in string_list)
            for string_list in string_lists
        )
        print(x)
        return None

    @lua_function(table)
    def rawequal(v1, v2) -> PyLuaRet:
        """rawequal (v1, v2)"""
        # Checks whether v1 is equal to v2, without invoking the __eq
        # metamethod.
        # Returns a boolean.
        return [rel_eq(v1, v2, raw=True)]

    @lua_function(table)
    def rawget(
            table: LuaTable,
            index: LuaValue,
    ) -> PyLuaRet:
        """rawget (table, index)"""
        # Gets the real value of table[index], without using the __index
        # metavalue.
        # table must be a table; index may be any value.
        assert isinstance(table, LuaTable)
        return [table.get(index, raw=True)]

    @lua_function(table)
    def rawlen(v: LuaTable | LuaString) -> PyLuaRet:
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
    def select(index, *a) -> PyLuaRet:
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
            while index < 0:
                index = len(a) + index
            return list(a[index:])
        # Otherwise, index must be the string "#",
        if rel_ne(index, LuaString(b"#")):
            raise LuaError(
                "bad argument #1 to 'select' (integer or '#')"
            )
        # and select returns the total number of extra arguments it received.
        return [LuaNumber(len(a), LuaNumberType.INTEGER)]

    @lua_function(table)
    def setmetatable(
            table: LuaTable,
            metatable: LuaTable | LuaNil,
    ) -> PyLuaRet:
        """setmetatable (table, metatable)"""
        # Sets the metatable for the given table.
        assert isinstance(table, LuaTable)
        # If metatable is nil, removes the metatable of the given table.
        if metatable is LuaNil:
            table.set_metatable(LuaNil)
            return [table]
        # If the original metatable has a __metatable field, raises an error.
        # TODO: Determine the order of this condition in relation to the one
        #       above.
        if table.has_metamethod(SYMBOL_METATABLE):
            raise LuaError("cannot change a protected metatable")
        table.set_metatable(metatable)
        # This function returns table.
        return [table]
        # To change the metatable of other types from Lua code, you must use the
        # debug library (§6.10).

    @lua_function(table, interacts_with_the_vm=True)
    def tonumber(
            vm: VirtualMachine,
            e,
            base=None
    ) -> PyLuaRet:
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
                    e_string = e.content.strip().decode("utf-8")
                    if e_string[0] == "+":
                        e_parsed = numeral_parser.parse(e_string[1:])
                    elif e_string[0] == "-":
                        e_parsed = Unary(
                            op=Terminal("-"),
                            exp=numeral_parser.parse(e_string[1:])
                        )
                    else:
                        e_parsed = numeral_parser.parse(e_string)
                    return [transformer.transform(e_parsed).evaluate(vm)]
                except Exception:
                    return [FAIL]
        # When called with base, then e must be a string to be interpreted as an
        # integer numeral in that base. The base may be any integer between
        # 2 and 36, inclusive.
        # TODO: Determine if e can have leading and trailing spaces and a sign
        #       when base is provided.
        # In bases above 10, the letter 'A' (in either upper or lower case)
        # represents 10, 'B' represents 11, and so forth, with 'Z' representing
        # 35. If the string e is not a valid numeral in the given base, the
        # function returns fail.
        acc = 0
        for i, c in enumerate(e.content.decode("utf-8")):
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
            return [LuaNumber(acc, LuaNumberType.INTEGER)]
        return [LuaNumber(float(acc), LuaNumberType.FLOAT)]

    @lua_function(table, interacts_with_the_vm=True)
    def tostring(vm: VirtualMachine, v: LuaValue) -> PyLuaRet:
        """tostring (v)"""
        # Receives a value of any type and converts it to a string in a
        # human-readable format.
        #
        # If the metatable of v has a __tostring field,
        tostring_field = v.get_metamethod(SYMBOL_TOSTRING)
        if tostring_field is not None:
            # then tostring calls the corresponding value with v as argument,
            call_result = call_function(vm, tostring_field, [v])
            # and uses the result of the call as its result.
            return call_result
        # Otherwise, if the metatable of v has a __name field with a string
        # value,
        name_field = v.get_metamethod(SYMBOL_NAME)
        if name_field is not None and isinstance(name_field, LuaString):
            # tostring may use that string in its final result.
            return [LuaString(f"{name_field.content}: {v}".encode("utf-8"))]
        # For complete control of how numbers are converted, use string.format.
        return [LuaString(str(v).encode("utf-8"))]

    @lua_function(table, name="type")
    def type_(v: LuaValue) -> PyLuaRet:
        """type (v)"""
        #  Returns the type of its only argument, coded as a string.
        #  The possible results of this function are "nil"
        #  (a string, not the value nil),
        #  "number", "string", "boolean", "table", "function", "thread", and
        #  "userdata".
        if isinstance(v, LuaNilType):
            return [LuaString(b"nil")]
        if isinstance(v, LuaNumber):
            return [LuaString(b"number")]
        if isinstance(v, LuaString):
            return [LuaString(b"string")]
        if isinstance(v, LuaBool):
            return [LuaString(b"boolean")]
        if isinstance(v, LuaTable):
            return [LuaString(b"table")]
        if isinstance(v, LuaFunction):
            return [LuaString(b"function")]
        if isinstance(v, LuaThread):
            return [LuaString(b"thread")]
        if isinstance(v, LuaUserdata):
            return [LuaString(b"userdata")]
        raise TypeError(f"Unexpected type: {type(v)}")

    from ay import __ay_version__
    # _VERSION
    #  A global variable (not a function) that holds a string containing the
    #  running Lua version.
    #  The current value of this variable is "Lua 5.4".
    table.put(
        LuaString(b"_VERSION"),
        LuaString(f"ay {__ay_version__}".encode("utf-8"))
    )

    @lua_function(table, interacts_with_the_vm=True)
    def warn(vm: VirtualMachine, msg1: LuaString, *a: LuaString) -> PyLuaRet:
        """warn (msg1, ···)"""
        # Emits a warning with a message composed by the concatenation of all
        # its arguments (which should be strings).
        #
        # By convention, a one-piece message starting with '@' is intended to be
        # a control message, which is a message to the warning system itself.
        if not a and msg1.content[0] == b"@":
            # In particular, the standard warning function in Lua recognizes the
            # control messages
            if msg1.content == b"@off":
                # "@off", to stop the emission of warnings,
                vm.emitting_warnings = False
            elif msg1.content == b"@on":
                # and "@on", to (re)start the emission;
                vm.emitting_warnings = True
            # it ignores unknown control messages.
            return None
        # TODO: Improve warning system.
        if not vm.emitting_warnings:
            return None
        print("Warning:", *a, sep=" ")
        return None

    @lua_function(table, interacts_with_the_vm=True)
    def xpcall(
            vm: VirtualMachine,
            f: LuaFunction,
            msgh: LuaFunction,
            *args: LuaFunction,
    ) -> list[LuaValue] | None:
        #  This function is similar to pcall, except that it sets a new message
        #  handler msgh.
        try:
            return_vals = call_function(vm, f, list(args))
        except LuaError as lua_error:
            # Any error inside f is not propagated;
            # instead, xpcall catches the error,
            # calls msgh with the original error object,
            # and returns a status code.
            return [
                # In case of any error, xpcall returns false
                LuaBool(False),
                # plus the result from msgh.
                *call_function(vm, msgh, [lua_error.message])
            ]
        else:
            return [
                # Its first result is the status code (a boolean),
                # which is true if the call succeeds without errors.
                LuaBool(True),
                # In such case, xpcall also returns all results from the call,
                # after this first result.
                *return_vals
            ]


class BasicLibrary(LibraryProvider):
    def provide(self, table: LuaTable) -> None:
        provide(table)