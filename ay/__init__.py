from pathlib import Path

from lark import Lark

with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

lua_parser = Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
)

text = """
function f()
    print("Hello, world!")
    return (1 + 2).toString()
end

print(f() .. "1")
"""

print("\n".join([f"> {l}" for l in text[1:].splitlines()]))
print("\nParse tree:")

parsed_lua = lua_parser.parse(text)
print(parsed_lua.pretty())
