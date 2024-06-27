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
x = 2 + 3 * 9
"""

print("\n".join([f"> {l}" for l in text[1:].splitlines()]))
print()

parsed_lua = lua_parser.parse(text)
# print(f"Parse tree:\n{parsed_lua.pretty()}")

Env = namedtuple("Env", ["glob", "loc"])

class BlockInterpreter(lark.visitors.Interpreter):
    def __init__(self, env) -> None:
        super().__init__()
        self.env = env

    def stat_assignment(self, tree):
        var_list = self.visit(tree.children[0])
        exp_list = self.visit(tree.children[1])
        for var, exp in zip(var_list, exp_list):
            self.env.loc[var] = exp

    def name(self, tree):
        return str(tree.children[0])

    def numeral(self, tree):
        return int(tree.children[0])

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
