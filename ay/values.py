from enum import Enum
from typing import NamedTuple, TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .control_structures import Scope


class LuaValue:
    def get_metatable(self) -> "LuaNilType | LuaTable":
        cls = self.__class__
        if not hasattr(cls, "_metatable"):
            return LuaNil
        return cls._metatable

    def set_metatable(self, value: "LuaValue"):
        cls = self.__class__
        cls._metatable = value

    def __eq__(self, other) -> bool:
        from .operations import rel_eq
        return rel_eq(self, other).true

    def __ne__(self, other) -> bool:
        from .operations import rel_ne
        return rel_ne(self, other).true


class SingletonType(type):
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = (
                super(SingletonType, cls).__call__(*args, **kwargs)
            )
        return cls._instances[cls]



class LuaNilType(LuaValue, metaclass=SingletonType):
    __slots__ = []

    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return "LuaNil"

    def __hash__(self):
        return hash(None)

    def __call__(self, *args, **kwargs):
        return self


LuaNil = LuaNilType()


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
        return self.content.decode("utf-8")

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


class LuaUserdata(LuaObject):
    __slots__ = []

    def __init__(self):
        super().__init__()


class LuaThread(LuaObject):
    __slots__ = []

    def __init__(self):
        super().__init__()


class LuaTable(LuaObject):
    __slots__ = ["map", "_metatable"]

    def __init__(self):
        super().__init__()
        self.map: dict[LuaValue, LuaValue] = {}
        self._metatable = LuaNil

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

    def __repr__(self):
        return f"LuaTable({self.map})"

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


class LuaFunction(LuaObject):
    __slots__ = ["param_names", "variadic", "parent_scope", "block"]

    def __init__(
            self,
            *,
            param_names: list[LuaString],
            variadic: bool,
            parent_scope: Optional["Scope"],
            block,
    ):
        super().__init__()
        self.param_names = param_names
        self.variadic = variadic
        self.parent_scope = parent_scope
        self.block = block

