from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias, TYPE_CHECKING

from ay.values import LuaValue, LuaTable, LuaString, LuaFunction, \
    LuaNil, LuaNumber, MAX_INT64, LuaNumberType, LuaBool
from ay.control_structures import LuaError, ReturnException
from ast_nodes import call_function

if TYPE_CHECKING:
    from ay.vm import VirtualMachine


PyLuaFunction = Callable[..., list[LuaValue] | None]
LuaDecorator: TypeAlias = Callable[[PyLuaFunction], LuaFunction]


def lua_function(
        table: LuaTable = None,
        *,
        name: str = None,
        interacts_with_the_vm: bool = False
) -> LuaDecorator:
    def decorator(func: PyLuaFunction) -> LuaFunction:
        if name:
            func.__name__ = name

        def new_function(*args: LuaValue) -> None:
            return_values: list[LuaValue] | None = func(*args)
            raise ReturnException(return_values)
            
        lf = LuaFunction(
            param_names=[],
            variadic=True,
            parent_stack_frame=None,
            block=new_function,
            interacts_with_the_vm=interacts_with_the_vm,
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
    def print_(*args) -> list[LuaValue] | None:
        print(*args, sep="\t")
        return None

    @lua_function(global_table)
    def pairs(t: LuaTable) -> list[LuaValue] | None:
        # TODO: Implement this function in a way that uses state.
        # If t has a metamethod __pairs, calls it with t as argument and
        # returns the first three results from the call.
        # Otherwise, returns three values: the next function, the table t, and
        # nil, so that the construction
        #      for k,v in pairs(t) do body end
        # will iterate over all key–value pairs of table t.
        items = iter(t.map.items())
        
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

    @lua_function(global_table)
    def ipairs(t: LuaTable) -> list[LuaValue] | None:
        # Returns three values (an iterator function, the table t, and 0) so
        # that the construction
        #      for i,v in ipairs(t) do body end
        # will iterate over the key–value pairs (1,t[1]), (2,t[2]), ..., up to
        # the first absent index.
        def iterator_function(state, control_variable: LuaNumber) \
                -> list[LuaValue] | None:
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

    @lua_function(global_table)
    def debugger() -> list[LuaValue] | None:
        return None

    @lua_function(global_table)
    def error(
            message: LuaValue,
            level: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER)
    ) -> list[LuaValue] | None:
        raise LuaError(message, int(level.value))

    @lua_function(global_table, interacts_with_the_vm=True)
    def pcall(
            vm: VirtualMachine,
            f: LuaFunction,
            *args: LuaValue
    ) -> list[LuaValue] | None:
        try:
            return_vals = call_function(vm, f, list(args))
        except LuaError as lua_error:
            if lua_error.level == 1:
                return [LuaBool(False), lua_error.message]
            else:
                raise LuaError(lua_error.message, lua_error.level - 1)
        else:
            return [LuaBool(True), *return_vals]

    @lua_function(global_table, interacts_with_the_vm=True)
    def xpcall(
            vm: VirtualMachine,
            f: LuaFunction,
            err: LuaFunction,
    ) -> list[LuaValue] | None:
        # xpcall calls function f in protected mode,
        # using err as the error handler.
        try:
            return_vals = call_function(vm, f, [])
        except LuaError as lua_error:
            # Any error inside f is not propagated;
            # instead, xpcall catches the error,
            # calls the err function with the original error object,
            # and returns a status code.
            return [
                # In case of any error, xpcall returns false
                LuaBool(False),
                # plus the result from err.
                *call_function(vm, err, [lua_error.message])
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

    return global_table
