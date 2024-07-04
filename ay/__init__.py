import io
import string
from pathlib import Path
from typing import NamedTuple

import lark

from .operations import rel_lt, rel_le, rel_gt, rel_ge, rel_eq, rel_ne, \
    int_overflow_wrap_around, arith_mul, arith_float_div, arith_floor_div, \
    arith_mod, arith_add, arith_sub, arith_exp, arith_unary_minus, bitwise_or, \
    bitwise_and, bitwise_xor, bitwise_unary_not, bitwise_shift_right, \
    bitwise_shift_left, is_false_or_nil, logical_unary_not, coerce_to_bool, \
    coerce_int_to_float, overflow_arith_add, str_to_lua_string
from .values import LuaNil, LuaNumber, LuaBool, LuaNumberType, LuaValue, \
    MAX_INT64, LuaString, LuaTable

with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

lua_parser = lark.Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
)


class Env(NamedTuple):
    glob: dict[LuaString, LuaValue]
    loc: dict[LuaString, LuaValue]


class FlowControl(NamedTuple):
    break_flag: bool = False
    return_flag: bool = False
    return_value: LuaValue | None = None


class BlockInterpreter(lark.visitors.Interpreter):
    def __init__(self, env: Env) -> None:
        super().__init__()
        self.env: Env = env

    def block(self, tree) -> FlowControl:
        return_stat = tree.children[-1]
        block_interpreter = BlockInterpreter(self.env)
        for statement in tree.children[:-1]:
            if statement.data == "stat_break":
                return FlowControl(break_flag=True)
            result = block_interpreter.visit(statement)
            if isinstance(result, FlowControl):
                return result
        if return_stat is not None:
            return FlowControl(
                return_flag=True,
                return_value=block_interpreter.visit(return_stat)
            )
        return FlowControl()

    def stat_assignment(self, tree):
        var_list = tree.children[0].children
        exp_list = tree.children[1].children
        exp_vals = [self.visit(exp) for exp in exp_list]
        for var, exp_val in zip(var_list, exp_vals):
            var_name = str_to_lua_string(var.children[0].children[0])
            if var_name in self.env.loc:
                self.env.loc[var_name] = exp_val
            else:
                self.env.glob[var_name] = exp_val

    def stat_while(self, tree) -> FlowControl:
        condition = tree.children[1]
        block = tree.children[3]
        while coerce_to_bool(self.visit(condition)).true:
            result: FlowControl = self.visit(block)
            if result.break_flag:
                break
            if result.return_flag:
                return result
        return FlowControl()

    def stat_repeat(self, tree) -> FlowControl:
        block = tree.children[1]
        condition = tree.children[3]
        while True:
            result: FlowControl = self.visit(block)
            if result.break_flag:
                break
            if result.return_flag:
                return result
            if coerce_to_bool(self.visit(condition)).true:
                break
        return FlowControl()

    def stat_if(self, tree) -> FlowControl:
        condition = tree.children[0]
        true_block = tree.children[1]
        else_ifs = tree.children[2:-1]
        else_block = tree.children[-1]

        if coerce_to_bool(self.visit(condition)).true:
            return self.visit(true_block)
        for else_if in else_ifs:
            condition = else_if.children[1]
            block = else_if.children[2]
            if self.visit(condition):
                return self.visit(block)
        if else_block:
            return self.visit(else_block)

    def stat_do(self, tree) -> FlowControl:
        return self.visit(tree.children[1])

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
        while condition_func(control_val, limit).true:
            self.env.loc[control_varname] = control_val
            result: FlowControl = self.visit(block)
            if result.break_flag:
                break
            if result.return_flag:
                return result
            overflow, control_val = overflow_arith_add(control_val, step)
            if overflow and integer_loop:
                break
        return FlowControl()

    def retstat(self, tree) -> list[LuaValue]:
        exp_list = tree.children[1]
        return self.visit(exp_list)

    def numeral_dec(self, tree):
        whole_part: str = tree.children[0]
        frac_part: str = tree.children[1]
        exp_sign: str = tree.children[2]
        exp_part: str = tree.children[3]

        if frac_part or exp_part:
            if not exp_sign:
                exp_sign = "+"
            if not exp_part:
                exp_part = "0"
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
            exp_val = 2**int(exp_part)
            return LuaNumber(frac_val * exp_val, LuaNumberType.FLOAT)
        # if the value overflows, it wraps around to fit into a valid integer.
        return int_overflow_wrap_around(int(whole_part, 16))

    # varlist: var ("," var)*
    # var: name -> var_name
    #    | prefixexp "[" exp "]" -> var_index
    #    | prefixexp "." name -> var_field

    def var(self, tree) -> LuaValue:
        return tree.children[0]

    def prefixexp(self, tree) -> LuaValue:
        return self.visit(tree.children[0])

    def var_name(self, tree) -> LuaValue:
        name: LuaString = self.visit(tree.children[0])
        if name in self.env.loc:
            return self.env.loc[name]
        elif name in self.env.glob:
            return self.env.glob[name]
        else:
            return LuaNil()

    def name(self, tree) -> LuaString:
        return str_to_lua_string(tree.children[0])

    def var_index(self, tree) -> LuaValue:
        prefixexp: LuaTable = self.visit(tree.children[0])
        index: LuaValue = self.visit(tree.children[2])
        return prefixexp.get(index)

    def var_field(self, tree) -> LuaValue:
        prefixexp: LuaTable = self.visit(tree.children[0])
        field: LuaString = self.visit(tree.children[2])
        return prefixexp.get(field)

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

    def exp_unary(self, tree):
        op = tree.children[0].children[0]
        right = self.visit(tree.children[1])
        if op == "-":
            return arith_unary_minus(right)
        elif op == "#":
            raise NotImplementedError()
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

    def exp_nil(self, tree):
        return LuaNil()

    def exp_true(self, tree):
        return LuaBool(True)

    def exp_false(self, tree):
        return LuaBool(False)

    def tableconstructor(self, tree) -> LuaTable:
        table = LuaTable()
        field_list = tree.children[0].children
        counter = 1
        field_iter = iter(field_list)
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
        block_interpreter = BlockInterpreter(Env({}, {}))
        for statement in tree.children[:-1]:
            block_interpreter.visit(statement)
        if return_stat is not None:
            return block_interpreter.visit(return_stat)
        return None
