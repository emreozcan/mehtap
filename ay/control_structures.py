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
    protected: bool = False

    def has(self, key: LuaString) -> bool:
        assert isinstance(key, LuaString)
        if key in self.locals:
            return True
        if self.parent is not None:
            return self.parent.has(key)
        return False

    def get(self, key: LuaString) -> LuaValue:
        assert isinstance(key, LuaString)
        if key in self.locals:
            return self.locals[key].value
        if self.parent is not None:
            return self.parent.get(key)
        return LuaNil

    def put_local(self, key: LuaString, variable: Variable):
        assert isinstance(key, LuaString)
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected Variable, got {type(variable)}")

        if key in self.locals and self.locals[key].constant:
            raise NotImplementedError()
        self.locals[key] = variable

    def put_nonlocal(self, key: LuaString, variable: Variable):
        assert isinstance(key, LuaString)
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected Variable, got {type(variable)}")

        if key in self.locals:
            self.put_local(key, variable)
            return
        if self.parent is None:
            raise NotImplementedError()  # TODO.
        self.parent.put_nonlocal(key, variable)


class LuaError(Exception):
    __slots__ = ["message", "level"]

    message: LuaValue
    level: int

    def __init__(self, message: LuaValue, level: int = 1):
        if not isinstance(message, LuaValue):
            raise TypeError(f"Expected LuaValue, got {type(message)}")
        self.message = message
        self.level = level
        super().__init__(message, level)
