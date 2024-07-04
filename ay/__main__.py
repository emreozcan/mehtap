from . import lua_parser, LuaInterpreter


def main():
    text = """
x = 10                    -- global variable
do                        -- new block
    local x = x           -- new 'x', with value 10
    print(x)              --> 10
    x = x+1
    do                    -- another block
        local x = x+1     -- another 'x'
        print(x)          --> 12
    end
    print(x)              --> 11
end
print(x)                  --> 10  (the global one)
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
