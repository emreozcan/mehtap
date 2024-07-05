from . import lua_parser, LuaInterpreter


def main():
    text = """
function f() return "first", "second", "third", "etc" end
function g() return "cte", "driht", "dnoces", "tsrif" end
x = -999
w = 1000

     print(x, f())      -- prints x and all results from f().
     print(x, (f()))    -- prints x and the first result from f().
     print(f(), x)      -- prints the first result from f() and x.
     print(1 .. f())     -- prints 1 added to the first result from f().
     x,y,z = w, f()     -- x gets w, y gets the first result from f(),
                        -- z gets the second result from f().
     print(x, y, z)
     x,y,z = f()        -- x gets the first result from f(),
                        -- y gets the second result from f(),
                        -- z gets the third result from f().
     print(x, y, z)
     x,y,z = f(), g()   -- x gets the first result from f(),
                        -- y gets the first result from g(),
                        -- z gets the second result from g().
     print(x, y, z)
     x,y,z = (f())      -- x gets the first result from f(), y and z get nil.
     print(x, y, z)
     print({f()})       -- creates a list with all results from f().
     print({f(), 5})    -- creates a list with the first result from f() and 5.
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
