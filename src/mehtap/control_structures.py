from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from mehtap.ast_nodes import Name
    from mehtap.values import LuaValue


class LuaError(BaseException):
    __slots__ = ["message", "level"]

    message: LuaValue
    level: int
    caused_by: Exception | None = None
    traceback_messages: list[str]

    def __init__(
        self,
        message: LuaValue | str,
        level: int = 1,
        caused_by: Exception | None = None
    ):
        if isinstance(message, str):
            from mehtap.values import LuaString
            message = LuaString(message.encode("ascii"))
        self.message = message
        self.level = level
        self.caused_by = caused_by
        self.traceback_messages = []
        super().__init__(message, level)

    def __repr__(self):
        return f"<error level {self.level}: {self.message}>"

    def __str__(self):
        return str(self.message)

    def push_tb(
        self,
        tb: str,
        *,
        file: str | None = None,
        line: int | None = None
    ):
        if file is not None and line is not None:
            self.traceback_messages.append(f'{file}:{line}: {tb}')
            return
        if file is not None and line is None:
            self.traceback_messages.append(f'{file}: {tb}')
            return
        if file is None and line is not None:
            self.traceback_messages.append(f'{line}: {tb}')
            return
        self.traceback_messages.append(tb)


@attrs.define(slots=True)
class FlowControlException(BaseException):
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
