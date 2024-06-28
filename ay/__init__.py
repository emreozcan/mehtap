from collections import namedtuple
from pathlib import Path

import lark

with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

lua_parser = lark.Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
)

text = """
x = 0x1F
y = 69
z = x + y
"""

print("\n".join([f"> {l}" for l in text[1:].splitlines()]))
print()

parsed_lua = lua_parser.parse(text)
# print(f"Parse tree:\n{parsed_lua.pretty()}")

Env = namedtuple("Env", ["glob", "loc"])

class LuaValue():
    def __init__(self) -> None:
        pass

class LuaNil(LuaValue):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return str(self)

class LuaInt64(LuaValue):
    __slots__ = ["value"]

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"LuaInt64({self.value})"

class LuaDouble(LuaValue):
    __slots__ = ["value"]

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"LuaDouble({self.value})"


MAX_INT64 = 2**63 - 1


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
            return LuaDouble(
                float(f"{whole_part}.{frac_part}e{exp_sign}{exp_part}")
            )
        whole_val = int(whole_part)
        if whole_val > MAX_INT64:
            return LuaDouble(float(whole_part))
        return LuaInt64(whole_val)

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
            return LuaDouble(frac_val * exp_val)
        # if the value overflows, it wraps around to fit into a valid integer.
        whole_val = int(whole_part, 16)
        if whole_val < MAX_INT64:
            return LuaInt64(whole_val)
        whole_val, sign = divmod(whole_val, MAX_INT64)
        if sign & 1:
            return LuaInt64(-whole_val)
        return LuaInt64(whole_val)

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
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        else:
            raise ValueError(f"Unknown sum operator: {op}")

    def exp_product(self, tree):
        left = self.visit(tree.children[0])
        op = tree.children[1].children[0]
        right = self.visit(tree.children[2])
        if op == "*":
            return left * right
        elif op == "/":
            return left / right
        elif op == "//":
            return left // right
        elif op == "%":
            return left % right
        else:
            raise ValueError(f"Unknown product operator: {op}")

class LuaInterpreter(lark.visitors.Interpreter):
    def __init__(self) -> None:
        super().__init__()

    def chunk(self, tree):
        block = tree.children[0]
        self.visit(block)

    def block(self, tree):
        try:
            return_stat = tree.children[-1]
            block_interpreter = BlockInterpreter(Env({}, {}))
            for statement in tree.children[:-1]:
                block_interpreter.visit(statement)
            if return_stat is not None:
                return block_interpreter.visit(return_stat)
            return None
        finally:
            print(f"Block env: {block_interpreter.env}")

lua_interpreter = LuaInterpreter()
print(f"Ultimate return value: {lua_interpreter.visit(parsed_lua)}")
