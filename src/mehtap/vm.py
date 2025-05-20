from __future__ import annotations

import sys
from typing import BinaryIO

import attrs

from mehtap.global_table import create_global_table
from mehtap.scope import Scope, AnyPath, ExecutionContext
from mehtap.values import (
    LuaTable,
    LuaString,
    Variable,
    LuaValue,
)


@attrs.define(slots=True, repr=False, init=False)
class VirtualMachine(ExecutionContext):
    globals: LuaTable
    root_scope: Scope
    emitting_warnings: bool
    verbose_tb: bool
    default_input: BinaryIO
    default_output: BinaryIO

    def __init__(self):
        self.globals = create_global_table()
        self.root_scope = Scope(self, None, varargs=[])
        self.emitting_warnings = False
        if hasattr(sys.stdin, "buffer"):
            self.default_input = sys.stdin.buffer
        else:
            self.default_input = sys.stdin
        if hasattr(sys.stdout, "buffer"):
            self.default_output = sys.stdout.buffer
        else:
            self.default_output = sys.stdout
        self.verbose_tb = False

    def eval(self, expr: str):
        return self.root_scope.eval(expr)

    def exec(
        self, chunk: str, *, filename: str | None = None
    ) -> list[LuaValue]:
        return self.root_scope.exec(chunk, filename=filename)

    def exec_file(self, file_path: AnyPath) -> list[LuaValue]:
        return self.root_scope.exec_file(file_path)

    def get_varargs(self) -> list[LuaValue] | None:
        return self.root_scope.get_varargs()

    def has_ls(self, key: LuaString):
        return self.root_scope.has_ls(key) or self.globals.has(key)

    def get_ls(self, key: LuaString):
        if self.root_scope.has_ls(key):
            return self.root_scope.get_ls(key)
        return self.globals.rawget(key)

    def put_local_ls(self, key: LuaString, variable: Variable):
        self.root_scope.put_local_ls(key, variable)

    def put_nonlocal_ls(self, key: LuaString, value: LuaValue | Variable):
        if isinstance(value, Variable):
            # TODO. Remove this. (Only used in tests)
            value = value.value
        self.globals.rawput(key, value)

    def get_warning(self, *messages: str | bytes | LuaString):
        if self.emitting_warnings:
            print(f"Warning: ", *messages, sep="", file=sys.stderr)
