from . import lua_parser, LuaInterpreter


def main():
    text = """
dog = {
    name = "dog"
}

function dog:speak(params)
    local what = params.what or "bark"
    local count = params.count or 1
    print(self.name .." says " .. what .. " " .. count .. " times!")
end

dog:speak{what = "woof", count = 3}
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
