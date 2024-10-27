import json

from ay.ast_transformer import LuaTransformer
from ay.parser import lua_parser
from ay.vm import VirtualMachine


def main():
    text = """
x = 1
print(x)
return x
"""

    print("\n".join([f"> {line}" for line in text[1:].splitlines()]))
    print()

    parsed_lua = lua_parser.parse(text)
    print(f"Parse tree:\n{parsed_lua.pretty()}")

    lua_transformer = LuaTransformer()
    ast = lua_transformer.transform(parsed_lua)

    serialized_ast = ast.as_dict()
    print(f"Abstract syntax tree:\n{json.dumps(serialized_ast, indent=4)}")

    vm = VirtualMachine()
    r = ast.block.evaluate(vm)
    print(f"Result:\n{r!r}")


if __name__ == "__main__":
    main()
