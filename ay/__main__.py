from . import lua_parser, LuaInterpreter


def main():
    text = """
x = 0x1F
y = 69
if x > 10 then
    y = 420
end
return y
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
