from collections.abc import Callable
from typing import TypeAlias, TYPE_CHECKING

from .values import LuaValue, LuaTable, LuaString, LuaFunction, \
    LuaNil, LuaNumber, MAX_INT64, LuaNumberType, LuaBool
from .control_structures import FlowControl, LuaError

if TYPE_CHECKING:
    from . import BlockInterpreter


PyLuaFunction = Callable[..., FlowControl]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(
        table: LuaTable = None,
        *,
        name: str = None,
        interacts_with_the_interpreter: bool = False
) -> LuaDecorator:
    def decorator(func: PyLuaFunction) -> LuaFunction:
        if name:
            func.__name__ = name
        lf = LuaFunction(
            param_names=[],
            variadic=True,
            parent_scope=None,
            block=func,
            interacts_with_the_interpreter=interacts_with_the_interpreter,
        )
        if table is not None:
            table.put(
                LuaString(func.__name__.encode("utf-8")),
                lf
            )
        return lf
    return decorator


def create_global_table() -> LuaTable:
    global_table = LuaTable()

    @lua_function(global_table, name="print")
    def print_(*args) -> FlowControl:
        print(*args, sep="\t")
        return flow_return()

    @lua_function(global_table)
    def pairs(t: LuaTable) -> FlowControl:
        # TODO: Implement this function in a way that uses state.
        # If t has a metamethod __pairs, calls it with t as argument and
        # returns the first three results from the call.
        # Otherwise, returns three values: the next function, the table t, and
        # nil, so that the construction
        #      for k,v in pairs(t) do body end
        # will iterate over all key–value pairs of table t.
        items = iter(t.map.items())
        def iterator_function(state, control_variable) -> FlowControl:
            try:
                key, value = next(items)
            except StopIteration:
                return flow_return()
            return flow_return([key, value])
        return flow_return([
            LuaFunction(
                param_names=[],
                variadic=False,
                parent_scope=None,
                block=iterator_function
            ),
            t,
            LuaNil,
        ])

    @lua_function(global_table)
    def ipairs(t: LuaTable) -> FlowControl:
        # Returns three values (an iterator function, the table t, and 0) so
        # that the construction
        #      for i,v in ipairs(t) do body end
        # will iterate over the key–value pairs (1,t[1]), (2,t[2]), ..., up to
        # the first absent index.
        def iterator_function(state, control_variable: LuaNumber) -> FlowControl:
            index = control_variable.value + 1
            if index > MAX_INT64:
                return flow_return()
            index_val = LuaNumber(index, LuaNumberType.INTEGER)
            value = t.get(index_val)
            if value is LuaNil:
                return flow_return()
            return flow_return([index_val, value])
        return flow_return([
            LuaFunction(
                param_names=[],
                variadic=False,
                parent_scope=None,
                block=iterator_function
            ),
            t,
            LuaNumber(0, LuaNumberType.INTEGER),
        ])

    @lua_function(global_table)
    def debugger() -> FlowControl:
        return flow_return()

    @lua_function(global_table)
    def error(
            message: LuaValue,
            level: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER)
    ) -> FlowControl:
        raise LuaError(message, int(level.value))

    @lua_function(global_table, interacts_with_the_interpreter=True)
    def pcall(
            interpreter: "BlockInterpreter",
            f: LuaFunction,
            *args: LuaValue
    ) -> FlowControl:
        try:
            return_vals = interpreter.call_function(f, list(args))
        except LuaError as lua_error:
            if lua_error.level == 1:
                return flow_return([LuaBool(False), lua_error.message])
            else:
                raise LuaError(lua_error.message, lua_error.level - 1)
        else:
            return flow_return([LuaBool(True), *return_vals])

    @lua_function(global_table, interacts_with_the_interpreter=True)
    def xpcall(
            interpreter: "BlockInterpreter",
            f: LuaFunction,
            err: LuaFunction,
    ) -> FlowControl:
        # xpcall calls function f in protected mode,
        # using err as the error handler.
        try:
            return_vals = interpreter.call_function(f, [])
        except LuaError as lua_error:
            # Any error inside f is not propagated;
            # instead, xpcall catches the error,
            # calls the err function with the original error object,
            # and returns a status code.
            return flow_return([
                # In case of any error, xpcall returns false
                LuaBool(False),
                # plus the result from err.
                *interpreter.call_function(err, [lua_error.message])
            ])
        else:
            return flow_return([
                # Its first result is the status code (a boolean),
                # which is true if the call succeeds without errors.
                LuaBool(True),
                # In such case, xpcall also returns all results from the call,
                # after this first result.
                *return_vals
            ])

    return global_table


def flow_return(return_value: list[LuaValue] = None) -> FlowControl:
    if not return_value:
        return FlowControl()
    return FlowControl(return_flag=True, return_value=return_value)
