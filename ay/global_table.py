from collections.abc import Callable
from typing import TypeAlias

from .values import LuaValue, LuaTable, LuaString, LuaFunction, \
    LuaNil, LuaNumber, MAX_INT64, LuaNumberType
from .control_structures import FlowControl


PyLuaFunction = Callable[..., FlowControl]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(table: LuaTable = None, *, name: str = None) -> LuaDecorator:
    def decorator(func: PyLuaFunction) -> LuaFunction:
        if name:
            func.__name__ = name
        lf = LuaFunction(
            param_names=[],
            variadic=True,
            parent_scope=None,
            block=func
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

    return global_table


def flow_return(return_value: list[LuaValue] = None) -> FlowControl:
    if not return_value:
        return FlowControl()
    return FlowControl(return_flag=True, return_value=return_value)
