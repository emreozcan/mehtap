import argparse
import os
import sys
import traceback
from collections.abc import Iterable

import lark.exceptions
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.validation import Validator, ValidationError, \
    ThreadedValidator

from mehtap import __version__ as __version__
from mehtap.control_structures import LuaError
from mehtap.library.stdlib.basic_library import basic_print
from mehtap.operations import str_to_lua_string
from mehtap.parser import repl_parser
from mehtap.vm import VirtualMachine
from mehtap.values import LuaValue, LuaTable, LuaNumber, LuaString

COPYRIGHT_TEXT = f"mehtap {__version__} Copyright (c) 2024-2025 Emre Özcan"


def main():
    try:
        _main()
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        sys.exit(1)
    except LuaError:
        sys.exit(1)


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
        arg_table.rawput(LuaNumber(1), str_to_lua_string(args.script))
        for i, arg in enumerate(args.args, start=2):
            arg_table.rawput(LuaNumber(i), str_to_lua_string(arg))
        vm.root_scope.varargs = [str_to_lua_string(arg) for arg in args.args]
    else:
        for i, arg in enumerate(sys.argv, start=1):
            arg_table.rawput(LuaNumber(i), str_to_lua_string(arg))
    vm.globals.rawput(LuaString(b"arg"), arg_table)

    if not args.ignore_environment:
        env_vars = [
            "MEHTAP_INIT_" + "_".join(__version__.split(".")),
            "MEHTAP_INIT",
            "LUA_INIT_5_4",
            "LUA_INIT",
        ]
        for env_var in env_vars:
            if env_var in os.environ:
                try:
                    if env_var[0] == "@":
                        vm.exec_file(os.environ[env_var][1:])
                    else:
                        vm.exec_file(os.environ[env_var])
                except LuaError as le:
                    print_lua_error(le, vm)
                    sys.exit(1)
                break

    if args.show_version:
        print(COPYRIGHT_TEXT)
        return

    if args.enable_warnings:
        vm.emitting_warnings = True

    try:
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
    except LuaError as le:
        print_lua_error(le, vm)
        sys.exit(1)

    no_execution = not args.script and not args.execute_string
    if args.enter_interactive or no_execution:
        print(COPYRIGHT_TEXT)
        enter_interactive(vm)


class MehtapValidator(Validator):
    def validate(self, document: Document) -> None:
        try:
            repl_parser.parse(document.text)
        except lark.exceptions.UnexpectedEOF as e:
            raise ValidationError(
                e.column,
                f"unexpected EOF: expected {get_expected_terminals(e.expected)}",
            )
        except lark.exceptions.UnexpectedCharacters as e:
            raise ValidationError(
                e.column,
                f"unexpected character {e.char} at column {e.column}",
            )
        except lark.exceptions.UnexpectedToken as e:
            raise ValidationError(
                e.column,
                f"unexpected {e.token}: expected {get_expected_terminals(e.expected)}",
            )


terminal_patterns = {
    d.name: d.pattern.value
    for d in repl_parser.terminals
    if d.pattern.type == "str"
}


def get_expected_terminals(tokens: Iterable[str]) -> str:
    seen_tokens = []
    results = []
    for token in tokens:
        if token in seen_tokens: continue
        seen_tokens.append(token)
        if token in terminal_patterns:
            results.append(f'"{terminal_patterns[token]}"')
        else:
            results.append(token)
    return ", ".join(results)

def get_continuation_prompt(width, _line_number, is_soft_wrap):
    if not is_soft_wrap:
        return "." * (width - 1) + " "
    return " " * (width - 1) + " "


class MehtapPromptSession(PromptSession):
    def _create_prompt_bindings(self) -> KeyBindings:
        kb = super()._create_prompt_bindings()
        kb.remove("enter")

        @kb.add("enter")
        def _accept_input(event: KeyPressEvent) -> None:
            if "\n" not in self.default_buffer.text or (
                self.default_buffer.cursor_position == len(self.default_buffer.text)
                and self.default_buffer.text[-1] == "\n"
            ):
                self.default_buffer.validate_and_handle()
                return
            self.default_buffer.insert_text("\n")

        @kb.add("tab")
        def _add_tab(event: KeyPressEvent) -> None:
            self.default_buffer.insert_text("  ")

        @kb.add("escape", "enter")
        def _add_newline(event: KeyPressEvent) -> None:
            if "\n" in self.default_buffer.text:
                self.default_buffer.validate_and_handle()
                return
            self.default_buffer.insert_text("\n")

        @kb.add("c-c")
        def _clear_line(event: KeyPressEvent) -> None:
            if self.default_buffer.text:
                self.default_buffer.reset()
            else:
                get_app().exit(exception=KeyboardInterrupt)

        return kb


def enter_interactive(vm: VirtualMachine) -> None:
    session = MehtapPromptSession()
    validator = ThreadedValidator(MehtapValidator())
    line = ""
    p1 = os.environ.get("_PROMPT", "> ")
    # p2 = os.environ.get("_PROMPT2", ">> ")
    while True:
        line += session.prompt(
            message=p1,
            prompt_continuation=get_continuation_prompt,
            validator=validator,
            mouse_support=True,
            multiline=True,
        )
        return_value: list[LuaValue] | None = None
        try:
            try:
                return_value = vm.exec(line)
            except lark.exceptions.UnexpectedInput as e:
                try:
                    return_value = vm.eval(line)
                except lark.exceptions.UnexpectedInput:
                    continue
        except LuaError as lua_error:
            print_lua_error(lua_error, vm)
        if return_value is not None:
            d = print_object(return_value)
            if d is not None:
                print(d)
        line = ""


def print_lua_error(lua_error: LuaError, vm: VirtualMachine | None):
    if (
        not isinstance(lua_error.message, LuaString)
        and lua_error.message.has_metavalue(LuaString(b"__tostring"))
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
        print(f"caused by: {type_name}", file=sys.stderr)
    if not lua_error.traceback_messages:
        lua_error.push_tb(
            "no traceback available",
            file="<Python>", line=None,
        )
    print("traceback: (most recent call first)")
    for entry in lua_error.traceback_messages:
        print("\t" + entry, file=sys.stderr)
    if vm.verbose_tb:
        print(traceback.format_exc(), file=sys.stderr)


def print_object(val: list[LuaValue]) -> str | None:
    if not val:
        return None
    return ", ".join([str(v) for v in val])


if __name__ == "__main__":
    main()
