from . import lua_parser, LuaInterpreter


def main():
    text = """
        x = 0x1F
        y = 69
        z = x + y
        """

    print("\n".join([f"> {line}" for line in text[1:].splitlines()]))
    print()

    parsed_lua = lua_parser.parse(text)
    # print(f"Parse tree:\n{parsed_lua.pretty()}")

    lua_interpreter = LuaInterpreter()
    print(f"Ultimate return value: {lua_interpreter.visit(parsed_lua)}")


if __name__ == "__main__":
    main()
