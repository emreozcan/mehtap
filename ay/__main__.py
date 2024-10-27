from ay.abstract_syntax_tree import nodes
from ay.abstract_syntax_tree.transformer import LuaTransformer
from ay import lua_parser, LuaInterpreter


def main():
    text = """
a = {}
local x = 20
for i = 1, 10 do
    local y = 0
    a[i] = function () y = y + 1; return x + y end
end

for i,f in ipairs(a) do
    print(f())
end
"""

    print("\n".join([f"> {line}" for line in text[1:].splitlines()]))
    print()

    parsed_lua = lua_parser.parse(text)
    print(f"Parse tree:\n{parsed_lua.pretty()}")

    lua_transformer = LuaTransformer()
    ast: nodes.Chunk = lua_transformer.transform(parsed_lua)

    print(f"Abstract syntax tree:\n{ast!r}")


if __name__ == "__main__":
    main()
