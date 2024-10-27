from __future__ import annotations

from enum import Enum
from typing import NamedTuple, TYPE_CHECKING, Optional

import attrs

from abstract_syntax_tree.nodes import Block
from util.node import Node

if TYPE_CHECKING:
    from .control_structures import Scope


@attrs.define(slots=True)
class LuaValue(Node):
    def get_metatable(self) -> LuaNilType | LuaTable:
        cls = self.__class__
        if hasattr(cls, "_metatable"):
            return cls._metatable
        return LuaNil

    def set_metatable(self, value: LuaValue):
        cls = self.__class__
        cls._metatable = value

    def __eq__(self, other) -> bool:
        from .operations import rel_eq
        return rel_eq(self, other).true

    def __ne__(self, other) -> bool:
        from .operations import rel_ne
        return rel_ne(self, other).true


@attrs.define(slots=True, repr=False)
class LuaNilType(LuaValue):
    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return "LuaNil"

    def __hash__(self):
        return hash(None)


LuaNil = LuaNilType()
LuaNilType.__new__ = lambda cls: LuaNil


@attrs.define(slots=True)
class LuaBool(LuaValue):
    true: bool

    def __str__(self) -> str:
        return "true" if self.true else "false"

    def __hash__(self):
        return hash(self.true)


class LuaNumberType(Enum):
    INTEGER = 1
    FLOAT = 2


MAX_INT64 = 2**63 - 1
MIN_INT64 = -2**63
SIGN_BIT = 1 << 63
ALL_SET = 2**64 - 1


@attrs.define(slots=True, init=False)
class LuaNumber(LuaValue):
    value: int | float
    type: LuaNumberType | None

    def __init__(
            self,
            value: int | float,
            type: LuaNumberType | None
    ) -> None:
        super().__init__()
        self.value = value
        if type is None:
            if isinstance(value, int):
                self.type = LuaNumberType.INTEGER
            else:
                self.type = LuaNumberType.FLOAT
        else:
            self.type = type
            if type == LuaNumberType.INTEGER and not isinstance(value, int):
                raise ValueError("Value is not an integer")
            elif type == LuaNumberType.FLOAT and not isinstance(value, float):
                raise ValueError("Value is not a float")

    def __str__(self) -> str:
        return str(self.value)


@attrs.define(slots=True)
class LuaString(LuaValue):
    content: bytes

    def __str__(self) -> str:
        return self.content.decode("utf-8")



@attrs.define(slots=True)
class LuaObject(LuaValue):
    def __str__(self):
        return repr(self)


@attrs.define(slots=True)
class LuaUserdata(LuaObject):
    pass


@attrs.define(slots=True)
class LuaThread(LuaObject):
    pass


@attrs.define(slots=True)
class LuaTable(LuaObject):
    map: dict[LuaValue, LuaValue] = attrs.field(default=dict)
    _metatable: LuaValue = LuaNil

    def get_metatable(self):
        return self._metatable

    def set_metatable(self, value: "LuaValue"):
        self._metatable = value

    def __str__(self):
        return (
            "{"
            + ", ".join(f"{k!s}: {v!s}" for k, v in self.map.items())
            + "}"
        )

    def put(self, key: LuaValue, value: LuaValue):
        if key is LuaNil:
            raise NotImplementedError()
        if isinstance(key, LuaNumber):
            if key.type == LuaNumberType.FLOAT:
                if key.value == float("nan"):
                    raise NotImplementedError()
                if key.value.is_integer():
                    key = LuaNumber(int(key.value), LuaNumberType.INTEGER)

        # Note: Do not optimize by deleting keys that are assigned LuaNil,
        # as Lua allows you to set existing fields in a table to nil while
        # traversing it by using next().
        self.map[key] = value

    def get(self, key: LuaValue) -> LuaValue:
        if key in self.map:
            return self.map[key]
        return LuaNil

    def has(self, key: LuaValue) -> bool:
        return key in self.map


class Variable(NamedTuple):
    value: LuaValue
    constant: bool = False
    to_be_closed: bool = False

    def __repr__(self):
        if self.constant:
            return f"<const {self.value}>"
        if self.to_be_closed:
            return f"<close {self.value}>"
        return f"<var {self.value}>"


@attrs.define(slots=True)
class LuaFunction(LuaObject):
    param_names: list[LuaString]
    variadic: bool
    parent_scope: Optional[Scope]
    block: Block
    interacts_with_the_interpreter: bool = False
