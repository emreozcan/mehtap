from __future__ import annotations

import attrs

from ay.global_table import create_global_table
from ay.values import (
    LuaTable,
    LuaString,
    Variable,
    StackFrame,
    StackExhaustionException,
)


@attrs.define(slots=True, repr=False)
class VirtualMachine:
    globals: LuaTable = attrs.field(factory=create_global_table)
    stack_frame: StackFrame = attrs.field(factory=lambda: StackFrame(None, {}))
    emitting_warnings: bool = False

    def push(self) -> VirtualMachine:
        return VirtualMachine(
            globals=self.globals,
            stack_frame=StackFrame(self.stack_frame, {}),
            emitting_warnings=self.emitting_warnings,
        )

    def has(self, key: LuaString):
        assert isinstance(key, LuaString)
        return self.stack_frame.has(key) or self.globals.has(key)

    def get(self, key: LuaString):
        assert isinstance(key, LuaString)
        if self.stack_frame.has(key):
            return self.stack_frame.get(key)
        return self.globals.get(key)

    def put_local(self, key: LuaString, variable: Variable):
        assert isinstance(key, LuaString)
        assert isinstance(variable, Variable)
        self.stack_frame.put_local(key, variable)

    def put_nonlocal(self, key: LuaString, variable: Variable):
        assert isinstance(key, LuaString)
        assert isinstance(variable, Variable)
        assert not variable.constant
        assert not variable.to_be_closed
        try:
            self.stack_frame.put_nonlocal(key, variable)
        except StackExhaustionException:
            self.globals.put(key, variable.value)
