from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from ay.values import LuaValue
from operations import str_to_lua_string

if TYPE_CHECKING:
    from ay.ast_nodes import Name


class LuaError(Exception):
    __slots__ = ["message", "level"]

    message: LuaValue
    level: int

    def __init__(self, message: LuaValue | str, level: int = 1):
        if not isinstance(message, LuaValue):
            if isinstance(message, str):
                message = str_to_lua_string(message)
            raise TypeError(f"Expected LuaValue, got {type(message)}")
        self.message = message
        self.level = level
        super().__init__(message, level)


@attrs.define(slots=True)
class FlowControlException(Exception):
    pass


@attrs.define(slots=True)
class BreakException(FlowControlException):
    pass


@attrs.define(slots=True)
class ReturnException(FlowControlException):
    values: list[LuaValue] | None = None


@attrs.define(slots=True)
class GotoException(FlowControlException):
    label: Name
