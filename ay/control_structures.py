import dataclasses
from typing import NamedTuple, Self

from .values import LuaValue, LuaString, Variable, LuaNil


class FlowControl(NamedTuple):
    break_flag: bool = False
    return_flag: bool = False
    return_value: list[LuaValue] | None = None


@dataclasses.dataclass(slots=True)
class Scope:
    parent: Self | None
    locals: dict[LuaString, Variable]
    varargs: list[LuaValue] | None = None

    def has(self, key: LuaString) -> bool:
        if key in self.locals:
            return True
        if self.parent is not None:
            return self.parent.has(key)
        return False

    def get(self, key: LuaString) -> LuaValue:
        if key in self.locals:
            return self.locals[key].value
        if self.parent is not None:
            return self.parent.get(key)
        return LuaNil

    def put_local(self, key: LuaString, variable: Variable):
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected Variable, got {type(variable)}")

        if key in self.locals and self.locals[key].constant:
            raise NotImplementedError()
        self.locals[key] = variable

    def put_nonlocal(self, key: LuaString, variable: Variable):
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected Variable, got {type(variable)}")

        if key in self.locals:
            self.put_local(key, variable)
            return
        if self.parent is None:
            raise NotImplementedError()  # TODO.
        self.parent.put_nonlocal(key, variable)
