from __future__ import annotations

import attrs

from ay.global_table import create_global_table
from ay.values import (
    LuaTable,
    LuaString,
    Variable,
    LuaValue, LuaNil,
)


@attrs.define(slots=True, repr=False, init=False)
class VirtualMachine:
    globals: LuaTable
    root_stack_frame: StackFrame
    emitting_warnings: bool = False

    def __init__(self):
        self.globals = create_global_table()
        self.root_stack_frame = StackFrame(self, None)

    def has_ls(self, key: LuaString):
        assert isinstance(key, LuaString)
        return self.root_stack_frame.has_ls(key) or self.globals.has(key)

    def get_ls(self, key: LuaString):
        assert isinstance(key, LuaString)
        if self.root_stack_frame.has_ls(key):
            return self.root_stack_frame.get_ls(key)
        return self.globals.get(key)

    def put_local_ls(self, key: LuaString, variable: Variable):
        assert isinstance(key, LuaString)
        assert isinstance(variable, Variable)
        self.root_stack_frame.put_local_ls(key, variable)

    def put_nonlocal_ls(self, key: LuaString, variable: Variable | LuaValue):
        assert isinstance(key, LuaString)
        if isinstance(variable, Variable):
            assert not variable.constant
            assert not variable.to_be_closed
            self.globals.put(key, variable.value)
            return
        elif isinstance(variable, LuaValue):
            self.globals.put(key, variable)
            return
        assert False


@attrs.define(slots=True, repr=False)
class StackFrame:
    vm: VirtualMachine
    parent: StackFrame | None
    locals: dict[LuaString, Variable] = attrs.field(factory=dict)
    varargs: list[LuaValue] | None = None

    def push(self) -> StackFrame:
        return StackFrame(self.vm, self)

    def __repr__(self):
        values = ",".join(f"({k})=({v})" for k, v in self.locals.items())
        if not self.varargs:
            return f"<StackFrame locals=[{values}]>"
        else:
            varargs = ",".join(str(v) for v in self.varargs)
            return f"<StackFrame locals=[{values}], local varargs=[{varargs}]>"

    def get_varargs(self) -> list[LuaValue] | None:
        # TODO: Figure this out.
        #       Do function closures include varargs?
        if self.varargs is not None:
            return self.varargs
        if self.parent is None:
            return None
        return self.parent.get_varargs()

    def has_ls(self, key: LuaString) -> bool:
        assert isinstance(key, LuaString)
        if key in self.locals:
            return True
        if self.parent is None:
            return False
        return self.parent.has_ls(key)

    def get_ls(self, key: LuaString) -> LuaValue:
        assert isinstance(key, LuaString)
        if key in self.locals:
            return self.locals[key].value
        if self.parent is None:
            return self.vm.get_ls(key)
        return self.parent.get_ls(key)

    def put_local_ls(self, key: LuaString, variable: Variable):
        assert isinstance(key, LuaString)
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected Variable, got {type(variable)}")

        if key in self.locals and self.locals[key].constant:
            raise NotImplementedError()
        self.locals[key] = variable

    def put_nonlocal_ls(self, key: LuaString, value: LuaValue):
        assert isinstance(key, LuaString)
        assert isinstance(value, LuaValue)
        if key in self.locals:
            if self.locals[key].constant:
                raise NotImplementedError()
            self.locals[key] = Variable(value)
            return
        if self.parent is None:
            self.vm.globals.put(key, value)
            return
        return self.parent.put_nonlocal_ls(key, value)
