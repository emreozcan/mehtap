from . import lua_parser, LuaInterpreter


def main():
    text = """
t = {"a", "b", "c", "d", "e", "f"}
for number, letter in pairs(t) do
    print(letter, number)
end
"""

    print("\n".join([f"> {line}" for line in text[1:].splitlines()]))
    print()

    parsed_lua = lua_parser.parse(text)
    # print(f"Parse tree:\n{parsed_lua.pretty()}")

    lua_interpreter = LuaInterpreter()
    ret_val = lua_interpreter.visit(parsed_lua)
    if ret_val:
        print("[" + ", ".join(str(x) for x in ret_val) + "]")


if __name__ == "__main__":
    main()
