import argparse
import os
import sys
import traceback

import lark.exceptions

from ay import __version__ as __version__
from ay.control_structures import LuaError
from ay.library.stdlib.basic_library import basic_print
from ay.operations import str_to_lua_string
from ay.vm import VirtualMachine
from ay.values import LuaValue, LuaTable, LuaNumber, LuaString

COPYRIGHT_TEXT = f"ay {__version__} Copyright (c) 2024 Emre Özcan"


def main():
    try:
        _main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        sys.exit(1)
    except LuaError as le:
        handle_luaerror(le, None)
        sys.exit(2)


def _main():
    arg_parser = argparse.ArgumentParser(
        description="Lua interpreter in Python",
    )
    arg_parser.add_argument(
        "-e",
        metavar="stat",
        help="execute string 'stat'",
        dest="execute_string",
    )
    arg_parser.add_argument(
        "-i",
        action="store_true",
        help="enter interactive mode after executing 'script'",
        dest="enter_interactive",
    )
    arg_parser.add_argument(
        "-l",
        metavar="name|g=mod",
        help="require library 'name' into global 'name' or 'g'",
        action="append",
        dest="require_libraries",
    )
    arg_parser.add_argument(
        "-v",
        action="store_true",
        help="show version information",
        dest="show_version",
    )
    arg_parser.add_argument(
        "-E",
        action="store_true",
        help="ignore environment variables",
        dest="ignore_environment",
    )
    arg_parser.add_argument(
        "-W",
        action="store_true",
        help="turn warnings on",
        dest="enable_warnings",
    )
    arg_parser.add_argument(
        "script",
        default=None,
        nargs="?",
        help="script to execute",
    )
    arg_parser.add_argument(
        "args",
        metavar="args",
        nargs="*",
        help="arguments to script, if any",
    )
    arg_parser.add_argument(
        "-V", "--verbose",
        action="store_true",
        help="show verbose traceback",
    )

    args = arg_parser.parse_args()
    vm = VirtualMachine()
    vm.verbose_tb = bool(args.verbose)

    arg_table = LuaTable()
    if args.script:
        arg_table.put(LuaNumber(1), str_to_lua_string(args.script))
        for i, arg in enumerate(args.args, start=2):
            arg_table.put(LuaNumber(i), str_to_lua_string(arg))
        vm.root_scope.varargs = [str_to_lua_string(arg) for arg in args.args]
    else:
        for i, arg in enumerate(sys.argv, start=1):
            arg_table.put(LuaNumber(i), str_to_lua_string(arg))
    vm.globals.put(LuaString(b"arg"), arg_table)

    if not args.ignore_environment:
        env_vars = [
            "AY_INIT_" + "_".join(__version__.split(".")),
            "AY_INIT",
            "LUA_INIT_5_4",
            "LUA_INIT",
        ]
        for env_var in env_vars:
            if env_var in os.environ:
                if env_var[0] == "@":
                    vm.exec_file(os.environ[env_var][1:])
                else:
                    vm.exec_file(os.environ[env_var])
                break

    if args.show_version:
        print(COPYRIGHT_TEXT)
        return

    if args.enable_warnings:
        vm.emitting_warnings = True

    if args.require_libraries:
        for lib_spec in args.require_libraries:
            if "=" in lib_spec:
                name, mod = lib_spec.split("=")
            else:
                name = mod = lib_spec
            # TODO: Replace this to not depend on the function 'require'
            vm.exec(f"{name} = require('{mod}')")

    if args.execute_string:
        vm.exec(args.execute_string)

    if args.script:
        if args.script != "-":
            vm.exec_file(args.script)
        else:
            vm.exec(sys.stdin.read())

    no_execution = not args.script and not args.execute_string
    if args.enter_interactive or no_execution:
        print(COPYRIGHT_TEXT)
        enter_interactive(vm)


def enter_interactive(vm: VirtualMachine) -> None:
    collected_line = ""
    p1 = os.environ.get("_PROMPT", "> ")
    p2 = os.environ.get("_PROMPT2", ">> ")
    while True:
        prompt = p1 if not collected_line else p2
        try:
            line = input(prompt)
            collected_line += line
        except EOFError:
            break
        r: list[LuaValue] | None = None
        try:
            r = vm.exec(collected_line)
        except lark.exceptions.UnexpectedInput as e:
            try:
                r = vm.eval(collected_line)
            except lark.exceptions.UnexpectedInput:
                print_lark_error_shower(collected_line, e, prompt)
                continue
            except LuaError as lua_error:
                handle_luaerror(lua_error, vm)
        except LuaError as lua_error:
            handle_luaerror(lua_error, vm)
        if r is not None:
            d = display_object(r)
            if d is not None:
                print(d)
        collected_line = ""


def print_lark_error_shower(collected_line, e, prompt):
    print(" " * len(prompt) + collected_line.splitlines()[e.line - 1])
    print(f"{' ' * len(prompt)}{' ' * (e.column - 1)}^")
    print(f"error: unexpected input, " f"line {e.line}, column {e.column}")


def handle_luaerror(lua_error: LuaError, vm: VirtualMachine | None):
    if (
        not isinstance(lua_error.message, LuaString)
        and lua_error.message.has_metamethod(LuaString(b"__tostring"))
        and vm is not None
    ):
        save = sys.stdout
        sys.stdout = sys.stderr
        try:
            basic_print(vm.root_scope, lua_error.message)
        finally:
            sys.stdout = save
    else:
        print(f"error:\t{lua_error.message!s}", file=sys.stderr)
    if lua_error.caused_by:
        type_name = lua_error.caused_by.__class__.__name__
        stringifed = str(lua_error.caused_by)
        if stringifed:
            print(
                f"caused by: {type_name} ({lua_error.caused_by})",
                file=sys.stderr
            )
        else:
            print(f"caused by: {lua_error.caused_by}", file=sys.stderr)
    if not lua_error.traceback:
        lua_error.traceback.append("no traceback available")
    print("traceback: (most recent call last)")
    for entry in reversed(lua_error.traceback):
        print("\t" + entry, file=sys.stderr)


def display_object(val: list[LuaValue]) -> str | None:
    if not val:
        return None
    return ", ".join([str(v) for v in val])


if __name__ == "__main__":
    main()
