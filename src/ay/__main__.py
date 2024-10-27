import argparse
import json
import sys

import lark.exceptions

from ay import __version__ as __ay_version__
from ay.ast_transformer import LuaTransformer, transformer
from ay.parser import chunk_parser, expr_parser
from ay.vm import VirtualMachine
from ay.values import LuaValue


def main_debug():
    text = """
local x <const> = 1
print(x)
return x
"""

    print("\n".join([f"> {line}" for line in text[1:].splitlines()]))
    print()

    parsed_lua = chunk_parser.parse(text)
    print(f"Parse tree:\n{parsed_lua.pretty()}")

    lua_transformer = LuaTransformer()
    ast = lua_transformer.transform(parsed_lua)

    serialized_ast = ast.as_dict()
    print(f"Abstract syntax tree:\n{json.dumps(serialized_ast, indent=4)}")

    vm = VirtualMachine()
    r = ast.block.evaluate(vm)
    print(f"Result:\n{r!r}")


COPYRIGHT_TEXT = f"ay {__ay_version__} Copyright (c) 2024 Emre Özcan"


def main():
    try:
        sys.exit(_main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        sys.exit(1)


def _main():
    arg_parser = argparse.ArgumentParser(
        description="Lua interpreter in Python",
    )
    arg_parser.add_argument(
        "-e", metavar="stat",
        help="execute string 'stat'",
    )
    arg_parser.add_argument(
        "-i", action="store_true",
        help="enter interactive mode after executing 'script'",
    )
    arg_parser.add_argument(
        "-l", metavar="name",
        help="require library 'name' into global 'name'",
    )
    arg_parser.add_argument(
        "-v", action="store_true",
        help="show version information",
    )
    arg_parser.add_argument(
        "-E", action="store_true",
        help="ignore environment variables",
    )
    arg_parser.add_argument(
        "-W", action="store_true",
        help="turn warnings on",
    )
    arg_parser.add_argument(
        "script", default=None, nargs="?",
        help="script to execute",
    )

    args = arg_parser.parse_args()
    if args.v:
        print(COPYRIGHT_TEXT)
        return

    transformer = LuaTransformer()
    vm = VirtualMachine()

    if args.e:
        work_chunk(args.e, vm)

    infile = None
    try:
        if args.script is None:
            enter_interactive(vm)
        else:
            if args.script == "-":
                infile = sys.stdin
            else:
                infile = open(args.script, "r", encoding="utf-8")
            work_chunk(infile.read(), vm)
            if args.i:
                enter_interactive(vm)
    finally:
        if infile:
            infile.close()


def enter_interactive(vm: VirtualMachine) -> None:
    print(COPYRIGHT_TEXT)
    collected_line = ""
    while True:
        try:
            line = input("> " if not collected_line else ">> ")
            collected_line += line
        except EOFError:
            break
        r = None
        try:
            r = work_chunk(collected_line, vm)
        except lark.exceptions.UnexpectedEOF as e:
            continue
        except lark.exceptions.UnexpectedInput as e:
            if e.line == 1 and e.column == 1:
                try:
                    r = work_expr(collected_line, vm)
                except lark.exceptions.UnexpectedEOF:
                    continue
        if r is not None:
            d = display_object(r)
            if d is not None:
                print(d)
        collected_line = ""


def display_object(val: LuaValue | list[LuaValue]) -> str | None:
    if isinstance(val, LuaValue):
        return str(val)
    if len(val) == 0:
        return None
    return ", ".join([str(v) for v in val])


def work_expr(
        expr: str,
        vm: VirtualMachine,
) -> LuaValue | list[LuaValue]:
    parsed_lua = expr_parser.parse(expr)
    ast = transformer.transform(parsed_lua)
    r = ast.evaluate(vm)
    return r


def work_chunk(
        chunk: str,
        vm: VirtualMachine,
) -> list[LuaValue]:
    parsed_lua = chunk_parser.parse(chunk)
    ast = transformer.transform(parsed_lua)
    r = ast.block.evaluate(vm)
    return r


if __name__ == "__main__":
    main()
