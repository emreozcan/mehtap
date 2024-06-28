class LuaValue:
    def __init__(self) -> None:
        pass


class LuaNil(LuaValue):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return str(self)


class LuaInt64(LuaValue):
    __slots__ = ["value"]

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"LuaInt64({self.value})"


class LuaDouble(LuaValue):
    __slots__ = ["value"]

    def __init__(self, value) -> None:
        super().__init__()
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"LuaDouble({self.value})"
