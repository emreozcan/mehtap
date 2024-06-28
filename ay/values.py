from enum import Enum


class LuaValue:
    __slots__ = []

    def __init__(self) -> None:
        pass


class LuaNil(LuaValue):
    __slots__ = []

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return "LuaNil()"


class LuaBool(LuaValue):
    __slots__ = ["true"]

    def __init__(self, true) -> None:
        super().__init__()
        self.true = true

    def __str__(self) -> str:
        return "true" if self.true else "false"

    def __repr__(self):
        return f"LuaBool({self.true})"


class LuaNumberType(Enum):
    INTEGER = 1
    FLOAT = 2


MAX_INT64 = 2**63 - 1
MIN_INT64 = -2**63


class LuaNumber(LuaValue):
    __slots__ = ["value", "type"]

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

    def __repr__(self) -> str:
        return f"LuaNumber({self.value}, {self.type})"


class LuaString(LuaValue):
    __slots__ = ["content"]

    def __init__(self, value):
        super().__init__()
        self.content = value

    def __str__(self) -> str:
        return self.content

    def __repr__(self):
        return f"<LuaString {hex(id(self))} {hex(id(self.content))}>"


class LuaObject(LuaValue):
    __slots__ = []

    def __init__(self):
        super().__init__()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"<{self.__class__.__name__} {hex(id(self))}>"


class LuaFunction(LuaObject):
    __slots__ = []

    def __init__(self):
        super().__init__()


class LuaUserdata(LuaObject):
    __slots__ = []

    def __init__(self):
        super().__init__()


class LuaThread(LuaObject):
    __slots__ = []

    def __init__(self):
        super().__init__()


class LuaTable(LuaObject):
    __slots__ = ["map"]

    def __init__(self):
        super().__init__()
        self.map: dict[LuaValue, LuaValue] = {}

    def __str__(self):
        return str(self.map)

    def __repr__(self):
        return f"LuaTable({self.map})"
