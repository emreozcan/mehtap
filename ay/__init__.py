import dataclasses
import io
import string
from pathlib import Path
from typing import NamedTuple, Self

import lark

from .operations import rel_lt, rel_le, rel_gt, rel_ge, rel_eq, rel_ne, \
    int_overflow_wrap_around, arith_mul, arith_float_div, arith_floor_div, \
    arith_mod, arith_add, arith_sub, arith_exp, arith_unary_minus, bitwise_or, \
    bitwise_and, bitwise_xor, bitwise_unary_not, bitwise_shift_right, \
    bitwise_shift_left, is_false_or_nil, logical_unary_not, coerce_to_bool, \
    coerce_int_to_float, overflow_arith_add, str_to_lua_string, concat, length, \
    adjust, adjust_without_requirement
from .values import LuaNil, LuaNumber, LuaBool, LuaNumberType, LuaValue, \
    MAX_INT64, LuaString, LuaTable, Scope, Variable, LuaFunction

with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

lua_parser = lark.Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
)


class FlowControl(NamedTuple):
    break_flag: bool = False
    return_flag: bool = False
    return_value: list[LuaValue] | None = None


class FuncName(NamedTuple):
    names: list[LuaString]
    method: bool


def flow_return(return_value: list[LuaValue] = None) -> FlowControl:
    if not return_value:
        return FlowControl()
    return FlowControl(return_flag=True, return_value=return_value)


def create_global_table() -> LuaTable:
    global_table = LuaTable()

    def lua_print(*args) -> FlowControl:
        print(*args, sep="\t")
        return flow_return()
    global_table.put(
        LuaString(b"print"),
        LuaFunction(
            param_names=[],
            variadic=True,
            parent_scope=None,
            block=lua_print
        )
    )

    def lua_pairs(t: LuaTable) -> FlowControl:
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
    global_table.put(
        LuaString(b"pairs"),
        LuaFunction(
            param_names=[],
            variadic=False,
            parent_scope=None,
            block=lua_pairs
        )
    )

    def lua_ipairs(t: LuaTable) -> FlowControl:
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
    global_table.put(
        LuaString(b"ipairs"),
        LuaFunction(
            param_names=[],
            variadic=False,
            parent_scope=None,
            block=lua_ipairs
        )
    )

    def debugger() -> FlowControl:
        return flow_return()
    global_table.put(
        LuaString(b"debugger"),
        LuaFunction(
            param_names=[],
            variadic=False,
            parent_scope=None,
            block=debugger
        )
    )

    return global_table


class BlockInterpreter(lark.visitors.Interpreter):
    def __init__(self, globals_: LuaTable = None, scope: Scope = None) -> None:
        super().__init__()
        if globals_ is None:
            globals_ = create_global_table()
        self.globals = globals_
        if scope is None:
            scope = Scope(None, {})
        self.scope = scope

    def get_stacked_interpreter(self):
        return BlockInterpreter(self.globals, Scope(self.scope, {}))

    def block(self, tree) -> FlowControl:
        return_stat = tree.children[-1]
        for statement in tree.children[:-1]:
            if statement.data == "stat_break":
                return FlowControl(break_flag=True)
            result = self.visit(statement)
            if isinstance(result, FlowControl) and result.return_flag:
                return result
        if return_stat is not None:
            return FlowControl(
                return_flag=True,
                return_value=self.visit(return_stat)
            )
        return FlowControl()

    def _call_function(self, function: LuaFunction, args: list[LuaValue]) \
            -> list[LuaValue]:
        new_scope = Scope(function.parent_scope, {})
        if not callable(function.block):
            if not function.variadic:
                args = adjust(args, len(function.param_names))
            else:
                raise NotImplementedError()
            new_interpreter = BlockInterpreter(self.globals, new_scope)
            for param_name, arg in zip(function.param_names, args):
                new_scope.put_local(param_name, Variable(arg))
            result: FlowControl = new_interpreter.visit(function.block)
        else:
            result: FlowControl = function.block(*args)
        if result.return_flag and result.return_value:
            return result.return_value
        return [LuaNil]

    def functioncall_regular(self, tree) -> list[LuaValue]:
        function: LuaFunction = self.visit(tree.children[0])
        args: list[LuaValue] = self.visit(tree.children[1])
        return self._call_function(function, args)


    def functioncall_method(self, tree) -> list[LuaValue]:
        # A call v:name(args) is syntactic sugar for v.name(v,args),
        # except that v is evaluated only once.
        v = self.visit(tree.children[0])
        name = self.visit(tree.children[1])
        args = self.visit(tree.children[2])
        return self._call_function(v.get(name), [v] + args)


    def args_list(self, tree) -> list[LuaValue]:
        explist = tree.children[0]
        if explist:
            return self.visit(tree.children[0])
        return []

    def args_value(self, tree) -> list[LuaValue]:
        return [self.visit(tree.children[0])]

    def stat_assignment(self, tree):
        var_list = tree.children[0].children
        exp_list = tree.children[1]
        exp_vals: list[LuaValue] = self.visit(exp_list)
        exp_vals = adjust(exp_vals, len(var_list))
        for var, exp_val in zip(var_list, exp_vals):
            if var.data == "var_name":
                var_name = str_to_lua_string(var.children[0].children[0])
                if self.scope.has(var_name):
                    self.scope.put_nonlocal(var_name, Variable(exp_val))
                else:
                    self.globals.put(var_name, exp_val)
            elif var.data == "var_index":
                prefixexp = self.visit(var.children[0])
                index = self.visit(var.children[1])
                prefixexp.put(index, exp_val)
            else:
                raise ValueError(f"unknown var type {var.data}")

    def stat_localassignment(self, tree):
        attname_list = tree.children[1]
        exp_list = tree.children[2]
        if exp_list:
            exp_vals = [self.visit(exp) for exp in exp_list.children]
            exp_vals = adjust(exp_vals, len(attname_list.children))
        else:
            exp_vals = [LuaNil] * len(attname_list.children)
        used_closed = False
        for attname, exp_val in zip(attname_list.children, exp_vals):
            var_name = self.visit(attname.children[0])
            attrib_rule = attname.children[1].children[0]
            if not attrib_rule:
                self.scope.put_local(var_name, Variable(exp_val))
            else:
                attrib: LuaString = self.visit(attrib_rule)
                if attrib.content == b"close":
                    if used_closed:
                        raise NotImplementedError()
                    used_closed = True
                    self.scope.put_local(
                        var_name,
                        Variable(exp_val, to_be_closed=True)
                    )
                elif attrib.content == b"const":
                    self.scope.put_local(
                        var_name,
                        Variable(exp_val, constant=True)
                    )
                else:
                    # TODO: Create an error
                    raise NotImplementedError()

    def stat_while(self, tree) -> FlowControl:
        condition = tree.children[1]
        block = tree.children[3]
        block_interpreter = self.get_stacked_interpreter()
        while coerce_to_bool(self.visit(condition)).true:
            result: FlowControl = block_interpreter.visit(block)
            if result.break_flag:
                break
            if result.return_flag:
                return result
        return FlowControl()

    def stat_repeat(self, tree) -> FlowControl:
        block = tree.children[1]
        condition = tree.children[3]
        block_interpreter = self.get_stacked_interpreter()
        while True:
            result: FlowControl = block_interpreter.visit(block)
            if result.break_flag:
                break
            if result.return_flag:
                return result
            if coerce_to_bool(block_interpreter.visit(condition)).true:
                break
        return FlowControl()

    def stat_if(self, tree) -> FlowControl:
        condition = tree.children[0]
        true_block = tree.children[1]
        else_ifs = tree.children[2:-1]
        else_block = tree.children[-1]

        if coerce_to_bool(self.visit(condition)).true:
            return self.get_stacked_interpreter().visit(true_block)
        for else_if in else_ifs:
            condition = else_if.children[0]
            block = else_if.children[1]
            if coerce_to_bool(self.visit(condition)).true:
                return self.get_stacked_interpreter().visit(block)
        if else_block:
            return self.get_stacked_interpreter().visit(else_block)
        return FlowControl()

    def stat_do(self, tree) -> FlowControl:
        return self.get_stacked_interpreter().visit(tree.children[1])

    def stat_for(self, tree) -> FlowControl:
        # This for loop is the "numerical" for loop explained in 3.3.5.
        # The given identifier (Name) defines the control variable,
        # which is a new variable local to the loop body (block).
        control_varname: LuaString = self.visit(tree.children[1])
        # The loop starts by evaluating once the three control expressions.
        control_expr_1 = tree.children[2]
        control_expr_2 = tree.children[3]
        control_expr_3 = tree.children[4]
        # Their values are called respectively
        # the initial value,
        initial_value: LuaNumber = self.visit(control_expr_1)
        # the limit,
        limit: LuaNumber = self.visit(control_expr_2)
        # and the step. If the step is absent, it defaults to 1.
        if control_expr_3:
            step: LuaNumber = self.visit(control_expr_3)
        else:
            step: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER)
        # If both the initial value and the step are integers,
        # the loop is done with integers;
        # note that the limit may not be an integer.
        integer_loop = (
                initial_value.type == LuaNumberType.INTEGER and
                step.type == LuaNumberType.INTEGER
        )
        if not integer_loop:
            # Otherwise, the three values are converted to floats
            # and the loop is done with floats.
            initial_value = coerce_int_to_float(initial_value)
            limit = coerce_int_to_float(limit)
            step = coerce_int_to_float(step)
        # After that initialization, the loop body is repeated with the value of
        # the control variable going through an arithmetic progression,
        # starting at the initial value,
        # with a common difference given by the step.
        # A negative step makes a decreasing sequence;
        # a step equal to zero raises an error.
        if step.value == 0:
            raise NotImplementedError()
        # The loop continues while the value is less than or equal to the limit
        # (greater than or equal to for a negative step).
        # If the initial value is already greater than the limit
        # (or less than, if the step is negative),
        # the body is not executed.
        step_negative = step.value < 0
        condition_func = rel_ge if step_negative else rel_le
        # For integer loops, the control variable never wraps around; instead,
        # the loop ends in case of an overflow.
        # You should not change the value of the control variable during the
        # loop.
        # If you need its value after the loop, assign it to another variable
        # before exiting the loop.
        block = tree.children[6]
        control_val = initial_value
        block_interpreter = self.get_stacked_interpreter()
        while condition_func(control_val, limit).true:
            block_interpreter.scope.put_local(
                control_varname,
                Variable(control_val)
            )
            result: FlowControl = block_interpreter.visit(block)
            if result.break_flag:
                break
            if result.return_flag:
                return result
            overflow, control_val = overflow_arith_add(control_val, step)
            if overflow and integer_loop:
                break
        return FlowControl()

    def stat_forin(self, tree) -> FlowControl:
        # The generic for statement works over functions, called iterators.
        # On each iteration, the iterator function is called to produce a new
        # value, stopping when this new value is nil.

        #  A for statement like
        #      for var_1, ···, var_n in explist do body end
        # works as follows.
        # The names var_i declare loop variables local to the loop body.
        body = tree.children[5]
        body_interpreter = self.get_stacked_interpreter()
        body_scope = body_interpreter.scope
        namelist = tree.children[1]
        name_count = len(namelist.children)
        names = [self.visit(name) for name in namelist.children]
        for name in names:
            body_scope.put_local(name, Variable(LuaNil))
        # The first of these variables is the control variable.
        control_variable_name = names[0]
        # The loop starts by evaluating explist to produce four values:
        explist = tree.children[3]
        exp_vals = adjust([self.visit(exp) for exp in explist.children], 4)
        # an iterator function,
        iterator_function = exp_vals[0]
        # a state,
        state = exp_vals[1]
        # an initial value for the control variable,
        initial_value = exp_vals[2]
        body_scope.put_local(control_variable_name, Variable(initial_value))
        # and a closing value.
        closing_value = exp_vals[3]

        while True:
            # Then, at each iteration, Lua calls the iterator function with two
            # arguments: the state and the control variable.
            results = adjust(
                self._call_function(
                    iterator_function,
                    [state, body_scope.get(control_variable_name)]
                ),
                name_count
            )
            # The results from this call are then assigned to the loop
            # variables, following the rules of multiple assignments.
            for name, value in zip(names, results):
                body_scope.put_local(name, Variable(value))
            # If the control variable becomes nil, the loop terminates.
            if results[0] is LuaNil:
                break
            # Otherwise, the body is executed and the loop goes to the next
            # iteration.
            body_interpreter.visit(body)
            continue
        if closing_value is not LuaNil:
            # The closing value behaves like a to-be-closed variable,
            # which can be used to release resources when the loop ends.
            # Otherwise, it does not interfere with the loop.
            raise NotImplementedError()

    def retstat(self, tree) -> list[LuaValue]:
        return self.visit(tree.children[1])

    def stat_localfunction(self, tree):
        # The statement
        #      local function f () body end
        # translates to
        #      local f; f = function () body end
        # not to
        #      local f = function () body end
        # (This only makes a difference
        # when the body of the function contains references to f.)
        name = self.visit(tree.children[1])
        self.scope.put_local(name, Variable(LuaNil))
        function = self._evaluate_funcbody(tree.children[2])
        self.scope.put_local(name, Variable(function))

    def stat_function(self, tree):
        funcname: FuncName = self.visit(tree.children[1])
        function: LuaFunction = self._evaluate_funcbody(tree.children[2])
        if funcname.method:
            function.param_names.insert(0, LuaString(b"self"))
        if len(funcname.names) == 1:
            name = funcname.names[0]
            if self.scope.has(name):
                self.scope.put_nonlocal(name, Variable(function))
            else:
                self.globals.put(name, function)
        else:
            first_name = funcname.names[0]
            if self.scope.has(first_name):
                table = self.scope.get(first_name)
            elif self.globals.has(first_name):
                table = self.globals.get(first_name)
            else:
                raise NotImplementedError()
            for name in funcname.names[1:-1]:
                table = table.get(name)
            table.put(funcname.names[-1], function)

    def funcname(self, tree) -> FuncName:
        root_name = tree.children[0]
        method_name = tree.children[1]
        middle_names = tree.children[1:-1]
        if method_name:
            return FuncName(
                [self.visit(root_name)]
                + [self.visit(name) for name in middle_names]
                + [self.visit(method_name)],
                method=True
            )
        return FuncName(
            [self.visit(root_name)]
            + [self.visit(name) for name in middle_names],
            method=False
        )

    def numeral_dec(self, tree):
        whole_part: str = tree.children[0]
        frac_part: str = tree.children[1]
        exp_sign: str = tree.children[2]
        exp_part: str = tree.children[3]

        if frac_part or exp_part:
            if not exp_sign:
                exp_sign = "+"
            else:
                exp_sign = exp_sign.children[0]
            if not exp_part:
                exp_part = "0"
            if not frac_part:
                frac_part = "0"
            return LuaNumber(
                float(f"{whole_part}.{frac_part}e{exp_sign}{exp_part}"),
                LuaNumberType.FLOAT
            )
        whole_val = int(whole_part)
        if whole_val > MAX_INT64:
            return LuaNumber(float(whole_part), LuaNumberType.FLOAT)
        return LuaNumber(whole_val, LuaNumberType.INTEGER)

    def literalstring(self, tree) -> LuaString:
        literal = tree.children[0]
        bytes_io = io.BytesIO()
        currently_skipping_whitespace = False
        currently_reading_decimal = False
        currently_read_decimal: str = ""
        str_iter = iter(literal[1:-1])
        for character in str_iter:
            if currently_skipping_whitespace:
                if character in string.whitespace:
                    continue
                currently_skipping_whitespace = False
            if currently_reading_decimal:
                if (
                        character in string.digits
                        and len(currently_read_decimal) < 3
                ):
                    currently_read_decimal += character
                    continue
                bytes_io.write(bytes([int(currently_read_decimal)]))
                currently_reading_decimal = False
                currently_read_decimal = ""
            if character == "\\":
                try:
                    escape_char = next(str_iter)
                except StopIteration:
                    bytes_io.write(b"\\")
                    break
                if escape_char == "a":
                    bytes_io.write(b"\a")
                elif escape_char == "b":
                    bytes_io.write(b"\b")
                elif escape_char == "f":
                    bytes_io.write(b"\f")
                elif escape_char == "n":
                    bytes_io.write(b"\n")
                elif escape_char == "r":
                    bytes_io.write(b"\r")
                elif escape_char == "t":
                    bytes_io.write(b"\t")
                elif escape_char == "v":
                    bytes_io.write(b"\v")
                elif escape_char == "\\":
                    bytes_io.write(b"\\")
                elif escape_char == "\"":
                    bytes_io.write(b"\"")
                elif escape_char == "'":
                    bytes_io.write(b"'")
                elif escape_char == "\n":
                    bytes_io.write(b"\n")
                elif escape_char == "z":
                    currently_skipping_whitespace = True
                    continue
                elif escape_char == "x":
                    try:
                        hex_digit_1 = next(str_iter)
                        hex_digit_2 = next(str_iter)
                    except StopIteration:
                        raise NotImplementedError()
                    bytes_io.write(bytes.fromhex(hex_digit_1 + hex_digit_2))
                elif escape_char in string.digits:
                    currently_reading_decimal = True
                    currently_read_decimal = escape_char
                    continue
                elif escape_char == "u":
                    left_brace = next(str_iter)
                    if left_brace != "{":
                        raise NotImplementedError()
                    hex_digits = []
                    while True:
                        hex_digit = next(str_iter)
                        if hex_digit == "}":
                            break
                        hex_digits.append(hex_digit)
                    hex_str = "".join(hex_digit)
                    bytes_io.write(chr(int(hex_str, 16)).encode("utf-8"))
                else:
                    raise NotImplementedError()
                continue
            bytes_io.write(character.encode("utf-8"))
        bytes_io.seek(0)
        return LuaString(bytes_io.read())


    def numeral_hex(self, tree):
        whole_part: str = tree.children[0]
        frac_part: str = tree.children[1]
        exp_sign: str = tree.children[2]
        exp_part: str = tree.children[3]

        if frac_part or exp_part:
            if not exp_sign:
                exp_sign = "+"
            if not exp_part:
                exp_part = "0"
            whole_val = int(whole_part + frac_part, 16)
            frac_val = whole_val / 16**len(frac_part)
            exp_val = 2**int(exp_sign + exp_part)
            return LuaNumber(frac_val * exp_val, LuaNumberType.FLOAT)
        # if the value overflows, it wraps around to fit into a valid integer.
        return int_overflow_wrap_around(int(whole_part, 16))

    def var(self, tree) -> LuaValue:
        return tree.children[0]

    def explist(self, tree) -> list[LuaValue]:
        values = [self.visit(entry) for entry in tree.children]
        return adjust_without_requirement(values)

    def exp(self, tree) -> LuaValue:
        val = self.visit(tree.children[0])
        if isinstance(val, list):
            return adjust(val, 1)[0]
        return val

    def var_name(self, tree) -> LuaValue:
        name: LuaString = self.visit(tree.children[0])
        local = self.scope.get(name)
        if local is LuaNil and self.globals.has(name):
            return self.globals.get(name)
        return local

    def var_index(self, tree) -> LuaValue:
        prefixexp: LuaTable = self.visit(tree.children[0])
        index: LuaValue = self.visit(tree.children[2])
        return prefixexp.get(index)

    def name(self, tree) -> LuaString:
        return str_to_lua_string(tree.children[0])

    def var_index(self, tree) -> LuaValue:
        prefixexp: LuaTable = self.visit(tree.children[0])
        index: LuaValue = self.visit(tree.children[1])
        return prefixexp.get(index)

    def var_field(self, tree) -> LuaValue:
        prefixexp: LuaTable = self.visit(tree.children[0])
        field: LuaString = self.visit(tree.children[2])
        return prefixexp.get(field)

    def _evaluate_funcbody(self, funcbody) -> LuaFunction:
        parlist = funcbody.children[0]
        block = funcbody.children[1]
        parameter_names = [
            self.visit(name) for name in parlist.children[0].children
        ] if parlist else []
        is_variadic = parlist.data == "parlist_vararg" if parlist else False
        return LuaFunction(
            param_names=parameter_names,
            variadic=is_variadic,
            block=block,
            parent_scope=self.scope,
        )

    def exp_functiondef(self, tree) -> LuaFunction:
        funcbody = tree.children[0]
        return self._evaluate_funcbody(funcbody)


    def exp_concat(self, tree):
        return concat(
            self.visit(tree.children[0]),
            self.visit(tree.children[1])
        )

    def exp_sum(self, tree):
        left = self.visit(tree.children[0])
        op = tree.children[1].children[0]
        right = self.visit(tree.children[2])
        match op:
            case "+":
                return arith_add(left, right)
            case "-":
                return arith_sub(left, right)
            case _:
                raise ValueError(f"Unknown sum operator: {op}")

    def exp_product(self, tree):
        left = self.visit(tree.children[0])
        op = tree.children[1].children[0]
        right = self.visit(tree.children[2])
        match op:
            case "*":
                return arith_mul(left, right)
            case "/":
                return arith_float_div(left, right)
            case "//":
                return arith_floor_div(left, right)
            case "%":
                return arith_mod(left, right)
            case _:
                raise ValueError(f"Unknown product operator: {op}")

    def exp_pow(self, tree):
        left = self.visit(tree.children[0])
        right = self.visit(tree.children[1])
        return arith_exp(left, right)

    def exp_unop(self, tree):
        op = tree.children[0].children[0]
        right = self.visit(tree.children[1])
        if op == "-":
            return arith_unary_minus(right)
        elif op == "#":
            return length(right)
        elif op == "~":
            return bitwise_unary_not(right)
        elif op == "not":
            return logical_unary_not(right)
        else:
            raise ValueError(f"Unknown unary operator: {op}")

    def exp_cmp(self, tree) -> LuaBool:
        left: LuaValue = self.visit(tree.children[0])
        op = tree.children[1].children[0]
        right: LuaValue = self.visit(tree.children[2])
        match op:
            case "<":
                return rel_lt(left, right)
            case "<=":
                return rel_le(left, right)
            case ">":
                return rel_gt(left, right)
            case ">=":
                return rel_ge(left, right)
            case "==":
                return rel_eq(left, right)
            case "~=":
                return rel_ne(left, right)
            case _:
                raise ValueError(f"Unknown comparison operator: {op}")

    def exp_bit_or(self, tree) -> LuaNumber:
        return bitwise_or(
            self.visit(tree.children[0]),
            self.visit(tree.children[1])
        )

    def exp_bit_xor(self, tree) -> LuaNumber:
        return bitwise_xor(
            self.visit(tree.children[0]),
            self.visit(tree.children[1])
        )

    def exp_bit_and(self, tree) -> LuaNumber:
        return bitwise_and(
            self.visit(tree.children[0]),
            self.visit(tree.children[1])
        )

    def exp_bit_shift(self, tree) -> LuaNumber:
        left: LuaValue = self.visit(tree.children[0])
        op = tree.children[1].children[0]
        right: LuaValue = self.visit(tree.children[2])
        match op:
            case "<<":
                return bitwise_shift_left(left, right)
            case ">>":
                return bitwise_shift_right(left, right)
            case _:
                raise ValueError(f"Unknown shift operator: {op}")

    def exp_logical_or(self, tree):
        left: LuaValue = self.visit(tree.children[0])
        # The disjunction operator or returns its first argument
        # if this value is different from nil and false;
        # otherwise, or returns its second argument.
        if not is_false_or_nil(left):
            return left
        return self.visit(tree.children[1])

    def exp_logical_and(self, tree):
        left: LuaValue = self.visit(tree.children[0])
        # The conjunction operator and returns its first argument
        # if this value is false or nil;
        # otherwise, and returns its second argument.
        if is_false_or_nil(left):
            return left
        return self.visit(tree.children[1])

    def exp_nil(self, tree) -> LuaValue:
        return LuaNil

    def exp_true(self, tree):
        return LuaBool(True)

    def exp_false(self, tree):
        return LuaBool(False)

    def tableconstructor(self, tree) -> LuaTable:
        table = LuaTable()
        field_list = tree.children[0]
        if not field_list:
            return table
        counter = 1
        field_iter = iter(field_list.children)
        for field in field_iter:
            if field.data == "field_with_key":
                key = self.visit(field.children[0])
                value = self.visit(field.children[1])
                table.put(key, value)
            elif field.data == "field_counter_key":
                key = LuaNumber(counter, LuaNumberType.INTEGER)
                counter += 1
                value = self.visit(field.children[0])
                table.put(key, value)
            else:
                RuntimeError(f"unknown field type {field.data}")
            try:
                next(field_iter)
            except StopIteration:
                break
        return table


class LuaInterpreter(lark.visitors.Interpreter):
    def __init__(self) -> None:
        super().__init__()

    def chunk(self, tree):
        block = tree.children[0]
        return self.visit(block)

    def block(self, tree):
        return_stat = tree.children[-1]
        block_interpreter = BlockInterpreter()
        for statement in tree.children[:-1]:
            block_interpreter.visit(statement)
        if return_stat is not None:
            return block_interpreter.visit(return_stat)
        return None
