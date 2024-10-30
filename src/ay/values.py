from __future__ import annotations

from abc import ABC
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from ay.ast_nodes import Block
    from ay.scope import Scope


@attrs.define(slots=True, eq=False)
class LuaValue(ABC):
    def get_metatable(self) -> LuaNilType | LuaTable:
        if hasattr(self, "_metatable"):
            return self._metatable
        return LuaNil

    def has_metamethod(self, name: LuaString) -> bool:
        metatable = self.get_metatable()
        if metatable is LuaNil:
            return False
        return metatable.has(name)

    def get_metamethod(self, name: LuaString) -> LuaValue | None:
        metatable = self.get_metatable()
        if metatable is LuaNil:
            return None
        return metatable.get_with_fallback(name, fallback=None)

    def set_metatable(self, value: LuaTable):
        if "_metatable" in self.__slots__:
            self._metatable = value
        else:
            raise NotImplementedError()

    def __eq__(self, other) -> bool:
        from .operations import rel_eq

        return rel_eq(self, other).true

    def __ne__(self, other) -> bool:
        from .operations import rel_ne

        return rel_ne(self, other).true


@attrs.define(slots=True, eq=False, repr=False)
class LuaNilType(LuaValue):
    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return "LuaNil"

    def __hash__(self):
        return hash(None)


LuaNil = LuaNilType()
del LuaNilType


@attrs.define(slots=True, eq=False)
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
MIN_INT64 = -(2**63)
SIGN_BIT = 1 << 63
ALL_SET = 2**64 - 1


@attrs.define(slots=True, init=False, eq=False)
class LuaNumber(LuaValue):
    value: int | float
    type: LuaNumberType | None

    def __init__(
        self,
        value: int | float,
        type: LuaNumberType | None = None,
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

    def __hash__(self):
        return hash(self.value)


@attrs.define(slots=True, eq=False, frozen=True)
class LuaString(LuaValue):
    content: bytes

    def __str__(self) -> str:
        return self.content.decode("utf-8")

    def __hash__(self):
        return hash(self.content)


@attrs.define(slots=True, eq=False)
class LuaObject(LuaValue, ABC):
    def __str__(self):
        return repr(self)


@attrs.define(slots=True, eq=False)
class LuaUserdata(LuaObject):
    pass


@attrs.define(slots=True, eq=False)
class LuaThread(LuaObject):
    pass


@attrs.define(slots=True, eq=False, repr=False)
class LuaTable(LuaObject):
    map: dict[LuaValue, LuaValue] = attrs.field(factory=dict)
    _metatable: LuaTable = LuaNil

    def __repr__(self):
        if not self._metatable:
            return f"<LuaTable {self!s}>"
        return f"<LuaTable {self!s} metatable={self._metatable}>"

    def get_metatable(self):
        return self._metatable

    def set_metatable(self, value: "LuaValue"):
        self._metatable = value

    def __str__(self):
        return self.recursive_detecting_str(set())

    def recursive_detecting_str(
        self,
        seen_objects: set[int],
    ) -> str:
        i = id(self)
        if i in seen_objects:
            return "{<...>}"
        seen_objects.add(i)
        pair_list = []
        for key, value in self.map.items():
            if not isinstance(key, LuaTable):
                key_str = str(key)
            else:
                key_str = key.recursive_detecting_str(seen_objects)
            if not isinstance(value, LuaTable):
                value_str = str(value)
            else:
                value_str = value.recursive_detecting_str(seen_objects)
            pair_list.append((key_str, value_str))
        return "{" + ", ".join(f"({k})=({v})" for k, v in pair_list) + "}"

    # TODO: Change raw's default value to False.
    def put(self, key: LuaValue, value: LuaValue, *, raw: bool = True):
        if not raw:
            raise NotImplementedError()  # todo. (__newindex metavalue)

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

    # TODO: Change raw's default value to False.
    def get(self, key: LuaValue, *, raw: bool = True) -> LuaValue:
        if not raw:
            raise NotImplementedError()  # todo. (__index metavalue)
        if key in self.map:
            return self.map[key]
        return LuaNil

    def get_with_fallback[T](self, key: LuaValue, fallback: T) -> LuaValue | T:
        return self.map.get(key, fallback)

    def has(self, key: LuaValue) -> bool:
        return key in self.map


@attrs.define(slots=True, eq=True)
class Variable:
    value: LuaValue
    constant: bool = False
    to_be_closed: bool = False

    def __repr__(self):
        if self.constant:
            return f"<const {self.value}>"
        if self.to_be_closed:
            return f"<close {self.value}>"
        return f"<var {self.value}>"


@attrs.define(slots=True, eq=False)
class LuaFunction(LuaObject):
    param_names: list[LuaString] | None
    variadic: bool
    parent_scope: Scope | None
    block: Block | Callable
    gets_scope: bool = False
    name: str | None = None
    min_req: int | None = None

    def _py_param_str(self, index):
        if (
            not self.param_names
            or index == len(self.param_names)
        ):
            if self.variadic:
                if self.param_names:
                    return "[, ...]"
                return "[...]"
            return ""
        my_name = self.param_names[index]
        next_name = self._py_param_str(index + 1)
        if index < self.min_req:
            if index == 0:
                return f"{my_name}{next_name}"
            return f", {my_name}{next_name}"
        if index >= self.min_req:
            if index == 0:
                return f"[{my_name}{next_name}]"
            return f"[, {my_name}{next_name}]"

    def _stringify_params(self):
        if self.min_req is not None:
            return f"({self._py_param_str(0)})"
        param_names = [str(name) for name in self.param_names]
        if self.variadic:
            param_names.append("...")
        param_list = ", ".join(param_names)
        return f"({param_list})"

    def __str__(self):
        if not self.name:
            return f"function{self._stringify_params()}: {hex(id(self))}"
        return (
            f"function {self.name}{self._stringify_params()}: {hex(id(self))}"
        )

    def call(
        self,
        args: list[LuaValue | list[LuaValue]],
        scope: Scope | None = None,
    ) -> list[LuaValue]:
        if not scope and not self.parent_scope:
            raise ValueError("No scope to call function in")
        from ay.control_structures import ReturnException
        try:
            self._call(args, scope or self.parent_scope)
        except ReturnException as e:
            return e.values if e.values is not None else []
        return []

    def _call(
        self,
        args: list[LuaValue | list[LuaValue]],
        scope: Scope,
    ):
        if not callable(self.block):
            new_scope = scope.push()
            # Function is implemented in Lua
            if self.variadic:
                from ay.operations import adjust_without_requirement
                args = adjust_without_requirement(args)
                new_scope.varargs = args[len(self.param_names):]
                args = args[:len(self.param_names)]
            from ay.operations import adjust
            args = adjust(args, len(self.param_names))
            for param_name, arg in zip(self.param_names, args):
                new_scope.put_local_ls(param_name, Variable(arg))
            retvals = self.block.evaluate_without_inner_scope(new_scope)
            if retvals is not None:
                from ay.control_structures import ReturnException
                raise ReturnException(retvals)
        else:
            # Function is implemented in Python
            from ay.operations import adjust_without_requirement
            args = adjust_without_requirement(args)
            if not self.gets_scope:
                self.block(*args)
            else:
                self.block(scope, *args)
