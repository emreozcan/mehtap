from collections import namedtuple
from pathlib import Path

import lark

from .operations import rel_lt, rel_le, rel_gt, rel_ge, rel_eq, rel_ne, \
    int_overflow_wrap_around, arith_mul, arith_float_div, arith_floor_div, \
    arith_mod, arith_add, arith_sub, arith_exp, arith_unary_minus, bitwise_or, \
    bitwise_and, bitwise_xor, bitwise_unary_not, bitwise_shift_right, \
    bitwise_shift_left, is_false_or_nil, logical_unary_not
from .values import LuaNil, LuaNumber, LuaBool, LuaNumberType, LuaValue, \
    MAX_INT64

with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

lua_parser = lark.Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
)

Env = namedtuple("Env", ["glob", "loc"])


class BlockInterpreter(lark.visitors.Interpreter):
    def __init__(self, env) -> None:
        super().__init__()
        self.env = env

    def stat_assignment(self, tree):
        var_list = tree.children[0].children
        exp_list = tree.children[1].children
        exp_vals = [self.visit(exp) for exp in exp_list]
        for var, exp_val in zip(var_list, exp_vals):
            var_name = str(var.children[0].children[0])
            if var_name in self.env.loc:
                self.env.loc[var_name] = exp_val
            else:
                self.env.glob[var_name] = exp_val

    def stat_if(self, tree):
        condition = tree.children[0]
        true_block = tree.children[1]
        else_ifs = tree.children[2:-1]
        else_block = tree.children[-1]

        if self.visit(condition).true:
            return self.visit(true_block)
        for else_if in else_ifs:
            condition = else_if.children[1]
            block = else_if.children[2]
            if self.visit(condition):
                return self.visit(block)
        if else_block:
            return self.visit(else_block)

    def retstat(self, tree):
        exp_list = tree.children[1]
        return self.visit(exp_list)

    def name(self, tree):
        return str(tree.children[0])

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

    def prefixexp(self, tree):
        return self.visit(tree.children[0])

    def var_name(self, tree):
        name = self.visit(tree.children[0])
        if name in self.env.loc:
            return self.env.loc[name]
        elif name in self.env.glob:
            return self.env.glob[name]
        else:
            return LuaNil()

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
