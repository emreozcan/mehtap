from . import lua_parser, LuaInterpreter


def main():
    text = """
x, y = 0, 0
while true do
    if x > 10 then break end
    x, y = x + 1, y + x
end
x = 0
repeat
    x, y = x + 1, y - 1
until y == 0
return x
"""

    print("\n".join([f"> {line}" for line in text[1:].splitlines()]))
    print()

    parsed_lua = lua_parser.parse(text)
    # print(f"Parse tree:\n{parsed_lua.pretty()}")

    lua_interpreter = LuaInterpreter()
    ret_val = lua_interpreter.visit(parsed_lua)
    print("[" + ", ".join(str(x) for x in ret_val) + "]")


if __name__ == "__main__":
    main()
