from enum import Enum


class LuaValue:
    __slots__ = ["metatable"]

    def __init__(self) -> None:
        self.metatable = None

    def __eq__(self, other) -> bool:
        from .operations import rel_eq
        return rel_eq(self, other).true


class LuaNil(LuaValue):
    __slots__ = []

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return "LuaNil()"

    def __hash__(self):
        return hash(None)


class LuaBool(LuaValue):
    __slots__ = ["true"]

    def __init__(self, true) -> None:
        super().__init__()
        self.true = true

    def __str__(self) -> str:
        return "true" if self.true else "false"

    def __repr__(self):
        return f"LuaBool({self.true})"

    def __hash__(self):
        return hash(self.true)


class LuaNumberType(Enum):
    INTEGER = 1
    FLOAT = 2


MAX_INT64 = 2**63 - 1
MIN_INT64 = -2**63
SIGN_BIT = 1 << 63
ALL_SET = 2**64 - 1


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
        return f"LuaNumber({self.value})"

    def __hash__(self):
        return hash(self.value)


class LuaString(LuaValue):
    __slots__ = ["content"]

    def __init__(self, value: bytes):
        super().__init__()
        self.content = value

    def __str__(self) -> str:
        return repr(self.content)

    def __repr__(self):
        return f"LuaString({self.content!r})"

    def __hash__(self):
        return hash(self.content)


class LuaObject(LuaValue):
    __slots__ = []

    def __init__(self):
        super().__init__()

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"<{self.__class__.__name__} {hex(id(self))}>"

    def __hash__(self):
        return hash(id(self))


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
    __slots__ = ["map", "metatable"]

    def __init__(self):
        super().__init__()
        self.map: dict[LuaValue, LuaValue] = {}

    def __str__(self):
        return (
            "{"
            + ", ".join(f"{k!s}: {v!s}" for k, v in self.map.items())
            + "}"
        )

    def __repr__(self):
        return f"LuaTable({self.map})"

    def put(self, key: LuaValue, value: LuaValue):
        if isinstance(key, LuaNil):
            raise NotImplementedError()
        if isinstance(key, LuaNumber):
            if key.type == LuaNumberType.FLOAT:
                if key.value == float("nan"):
                    raise NotImplementedError()
                if key.value.is_integer():
                    key = LuaNumber(int(key.value), LuaNumberType.INTEGER)

        if isinstance(value, LuaNil):
            del self.map[key]
        else:
            self.map[key] = value

    def get(self, key: LuaValue) -> LuaValue:
        if key in self.map:
            return self.map[key]
        return LuaNil()

    def has(self, key: LuaValue) -> bool:
        return key in self.map
