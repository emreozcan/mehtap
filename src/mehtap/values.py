from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

import attrs

from mehtap.control_structures import LuaError

if TYPE_CHECKING:
    from mehtap.ast_nodes import Block
    from mehtap.scope import Scope
    from mehtap.operations import Multires


@attrs.define(slots=True, eq=True, repr=False)
class Variable:
    """Tuple of a Lua value and its properties describing a local variable."""

    value: LuaValue
    """The value of the variable."""
    constant: bool = False
    """Whether the local is a constant."""
    to_be_closed: bool = False
    """Whether the local is a to-be-closed variable."""

    def __repr__(self):
        if self.constant:
            return f"<Variable const {self.value}>"
        if self.to_be_closed:
            return f"<Variable close {self.value}>"
        return f"<Variable var {self.value}>"


@attrs.define(slots=True, eq=False)
class LuaValue(ABC):
    """Base class that all Lua values inherit from."""

    def get_metatable(self) -> LuaNilType | LuaTable:
        """
        :return: The value's metatable if it exists, or :data:`LuaNil` if not.
        """
        if hasattr(self, "_metatable") and self._metatable:
            return self._metatable
        return LuaNil

    def has_metavalue(self, name: LuaString) -> bool:
        """
        :param name: The name of the metavalue to check for.
        :return: Whether the value has a metavalue with this key.
        """
        metatable = self.get_metatable()
        if metatable is LuaNil:
            return False
        return metatable.has(name)

    def get_metavalue(self, name: LuaString) -> LuaValue | None:
        """
        :param name: The name of the metavalue to get.
        :return: The metavalue, or :data:`None` if the value doesn't have a
                 metavalue with the given name.
        """
        metatable = self.get_metatable()
        if metatable is LuaNil:
            return None
        return metatable.get_with_fallback(name, fallback=None)

    def set_metatable(self, value: LuaTable):
        """Set the value's metatable if the value can have one.

        :raises NotImplementedError: if the value can't have a metatable
        """
        if hasattr(self, "_metatable"):
            self._metatable = value
        else:
            raise LuaError(f"cannot set metatable for {type_of_lv(self)} value")

    def remove_metatable(self):
        """Removes the value's metatable if the value can have one.

        Does nothing if the value can't have a metatable
        """
        if hasattr(self, "_metatable"):
            self._metatable = None

    def __eq__(self, other) -> bool:
        """Compare this value according to Lua's rules on equality."""
        from .operations import rel_eq

        return rel_eq(self, other).true

    def __ne__(self, other) -> bool:
        from .operations import rel_ne

        return rel_ne(self, other).true

    __ne__.__doc__ = __eq__.__doc__


@attrs.define(slots=True, eq=False, repr=False)
class LuaNilType(LuaValue):
    def __str__(self) -> str:
        return "nil"

    def __repr__(self) -> str:
        return "LuaNil"

    def __hash__(self):
        return hash(None)


LuaNil = LuaNilType()
"""Value that is different from all other LuaValues.

Represents the value of the *nil* basic type in Lua.
Sole object of the ``LuaNilType`` class.
"""
del LuaNilType


@attrs.define(slots=True, eq=False)
class LuaBool(LuaValue):
    """Class representing values of the *boolean* basic type in Lua."""

    true: bool
    """Whether this value is ``true`` or ``false``."""

    def __str__(self) -> str:
        return "true" if self.true else "false"

    def __hash__(self):
        return hash(self.true)


class LuaNumberType(Enum):
    """LuaNumberType(value)
    Enumeration of the types of numbers in Lua.
    """

    INTEGER = 1
    """Number type that represents 64-bit signed integers."""
    FLOAT = 2
    """Number type that represents double-precision floating point numbers."""


MAX_INT64 = 2**63 - 1
MIN_INT64 = -(2**63)
SIGN_BIT = 1 << 63
ALL_SET = 2**64 - 1


@attrs.define(slots=True, init=False, eq=False)
class LuaNumber(LuaValue):
    """Class representing values of the *number* basic type in Lua.

    :param value: The underlying value of this number value.
    :param type: The type of this number value.
                 If provided, must match the type of ``value``.
    """

    value: int | float
    """The underlying value of this number value."""
    type: LuaNumberType | None
    """The type of this number value."""

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
    """Class representing values of the *string* basic type in Lua."""

    content: bytes
    """Sequence of the bytes of the string."""

    def __str__(self) -> str:
        return self.content.decode("utf-8")

    def __hash__(self):
        return hash(self.content)


@attrs.define(slots=True, eq=False)
class LuaObject(LuaValue, ABC):
    """Base class that *Lua objects* inherit from.

    :class:`Tables <LuaTable>`,
    :class:`functions <LuaFunction>`,
    :class:`threads <LuaThread>` and
    :class:`(full) userdata values <LuaUserdata>`
    are objects.
    See `Lua 5.4 Reference Manual, Section 2.1
    <https://lua.org/manual/5.4/manual.html#2.1>`_.
    """

    def __str__(self):
        return repr(self)


class LuaCallableABC(ABC):
    """Abstract base class for objects that can be called.

    If a type that is not a subclass of this class is attempted to be called in
    execution, a :class:`LuaError` will be raised.
    """
    @abstractmethod
    def rawcall(
        self,
        args: Multires,
        scope: Scope | None,
        *,
        modify_tb: bool = True,
    ) -> list[LuaValue]:
        """Call this value.

        :param args: Arguments to pass.
        :param scope: The scope of the caller.
        :param modify_tb: Whether to add an entry to the tracebacks of errors.
        :return: the list of :class:`LuaValue` objects that the callable returns
        """
        ...


@attrs.define(slots=True, eq=False)
class LuaFunction(LuaObject, LuaCallableABC):
    """Class representing values of the *function* basic type in Lua."""

    param_names: list[LuaString]
    """The names of the parameters of the function.

    Used when binding given arguments to the block scope when calling the
    function or when pretty-displaying the function.
    """
    variadic: bool
    """Whether the function is a *variadic function*.

    That is, a function that accepts a variable number of arguments, binding
    the excess arguments to the expression "``...``".
    """
    parent_scope: Scope | None
    """The scope the function was defined in.

    The function can access any of these values as *upvalues*.
    Not applicable for functions defined from Python.
    """
    block: Block | Callable
    """The code that the function executes.

    If of type :class:`Block`, the function is implemented in Lua.
    If of type :class:`Callable`, the function is implemented in Python.

    The :meth:`call` method should be used to call the function.
    """
    gets_scope: bool = False
    """Whether the function receives the scope as its first argument.

    Only applicable for functions implemented in Python.
    """
    name: str | None = None
    """The name of the function."""
    min_req: int | None = None
    """The minimum number of required arguments.

    Only applicable for functions implemented in Python.
    Only used for pretty-displaying the function.
    """

    def _py_param_str(self, index):
        if not self.param_names or index == len(self.param_names):
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
        native = "native " if callable(self.block) else ""
        if not self.name:
            return (
                f"{native}function{self._stringify_params()}: {hex(id(self))}"
            )
        return (
            f"{native}function {self.name}{self._stringify_params()}: "
            f"{hex(id(self))}"
        )

    def rawcall(
        self,
        args: Multires,
        scope: Scope | None,
        *,
        modify_tb: bool = True,
    ) -> list[LuaValue]:
        """Call the function.

        :param args: The arguments to pass to the function.
        :param scope: The scope of the caller.
        :param modify_tb: Whether to add self to the traceback of exceptions.
                          If the caller is handling traceback,
                          should be set to :data:`False`,
                          otherwise should be set to :data:`True`.
        :return: A multires list of the return values of the function.

        The number of arguments will be suitably adjusted to the
        number of the function's arguments according to
        `the rules on adjustment of Lua`_.
        Can contain multires expressions.

        .. _the rules on adjustment of Lua:
           https://lua.org/manual/5.4/manual.html#3.4.12
        """
        from mehtap.control_structures import ReturnException
        from mehtap.vm import VirtualMachine
        from mehtap.control_structures import LuaError
        try:
            self._call(
                args,
                scope or self.parent_scope or VirtualMachine().root_scope,
            )
        except LuaError as le:
            if modify_tb:
                le.push_tb(str(self))
            raise le
        except ReturnException as e:
            return e.values if e.values is not None else []
        except Exception as e:
            from mehtap.control_structures import LuaError
            s_e = str(e)
            assert s_e
            le = LuaError(
                LuaString(f"{self!s}: {e!s}".encode("utf-8")),
                caused_by=e,
            )
            if modify_tb:
                le.push_tb(str(self))
            raise le from e
        return []

    def _call(
        self,
        args: Multires,
        scope: Scope,
    ):
        if not callable(self.block):
            # Function is implemented in Lua
            new_scope = self.parent_scope.push()
            param_count = len(self.param_names)

            if self.variadic:
                from mehtap.operations import adjust_flatten

                args = adjust_flatten(args)
                new_scope.varargs = args[param_count:]
                args = args[:param_count]
            from mehtap.operations import adjust

            args = adjust(args, param_count)
            for param_name, arg in zip(self.param_names, args):
                new_scope.put_local_ls(param_name, Variable(arg))
            retvals = self.block.evaluate_without_inner_scope(new_scope)
            if retvals is not None:
                from mehtap.control_structures import ReturnException

                raise ReturnException(retvals)
        else:
            # Function is implemented in Python
            from mehtap.operations import adjust_flatten

            args = adjust_flatten(args)
            try:
                if not self.gets_scope:
                    self.block(*args)
                else:
                    self.block(scope, *args)
            # Always add Python functions to tracebacks.
            # (Ignore the modify_tb parameter of cls.call().)
            except LuaError as le:
                le.push_tb(str(self), file="<Python>", line=None)
                raise le
            except Exception as e:
                le = LuaError(
                    LuaString(str(e).encode("utf-8")),
                    caused_by=e,
                )
                le.push_tb(str(self), file="<Python>", line=None)
                raise le from e


@attrs.define(slots=True, eq=False)
class LuaUserdata(LuaObject):
    """Class representing values of the *userdata* basic type in Lua.

    Users can define their own userdata types by subclassing this class.
    An example of a subclass of this class is :class:`LuaFile`.
    """
    pass


@attrs.define(slots=True, eq=False)
class LuaThread(LuaObject):
    """Class representing values of the *thread* basic type in Lua."""
    pass


class LuaIndexableABC(LuaValue, ABC):
    """Abstract base class for objects that can be indexed.

    If a type that is not a subclass of this class is attempted to be indexed in
    execution, a :class:`LuaError` will be raised.
    """
    @abstractmethod
    def rawput(self, key: LuaValue, value: LuaValue) -> None:
        """Put a key-value pair into the object."""
        ...

    @abstractmethod
    def rawget(self, key: LuaValue) -> LuaValue:
        """Get the associated value of a key from the object."""
        ...

    T = TypeVar("T")

    @abstractmethod
    def get_with_fallback(self, key: LuaValue, fallback: T) -> LuaValue | T:
        """
        Get the associated value of a key from the object, or
        :data:`fallback` if the key isn't associated with any value.
        """
        ...

    @abstractmethod
    def has(self, key: LuaValue) -> bool:
        """
        :return: :data:`True` if the object has a value associated with
                 :data:`key`, :data:`False` otherwise.
        """
        ...


@attrs.define(slots=True, eq=False, repr=False)
class LuaTable(LuaObject, LuaIndexableABC):
    """Class representing values of the *table* basic type in Lua."""

    map: dict[LuaValue, LuaValue] = attrs.field(factory=dict)
    """The key-value pairs of the table."""
    _metatable: LuaTable | None = None
    """The metatable of the table."""

    def __repr__(self):
        if not self._metatable:
            return f"<LuaTable {self!s}>"
        return f"<LuaTable {self!s} metatable={self._metatable}>"

    def __str__(self):
        return self._recursive_detecting_str(set())

    def _recursive_detecting_str(
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
                key_str = key._recursive_detecting_str(seen_objects)
            if not isinstance(value, LuaTable):
                value_str = str(value)
            else:
                value_str = value._recursive_detecting_str(seen_objects)
            pair_list.append((key_str, value_str))
        return "{" + ", ".join(f"({k})=({v})" for k, v in pair_list) + "}"

    def rawput(self, key: LuaValue, value: LuaValue):
        # Warning: Do not optimize by deleting keys that are assigned LuaNil,
        # as Lua allows you to set existing fields in a table to nil while
        # traversing it by using next().

        if isinstance(key, LuaNumber):
            if key.type == LuaNumberType.FLOAT:
                if key.value == float("nan"):
                    raise LuaError("table index is NaN")
                if key.value.is_integer():
                    key = LuaNumber(int(key.value), LuaNumberType.INTEGER)

        self.map[key] = value

    def rawget(self, key: LuaValue):
        if key in self.map:
            return self.map[key]
        return LuaNil

    T = TypeVar("T")

    def get_with_fallback(self, key: LuaValue, fallback: T) -> LuaValue | T:
        f = self.map.get(key, None)
        if f is LuaNil or f is None:
            return fallback
        return f

    def has(self, key: LuaValue) -> bool:
        return key in self.map and self.map[key] is not LuaNil


def type_of_lv(a: LuaValue) -> str:
    """
    :return: The result of ``type(a)`` in Lua as a Python :class:`str`.

    This is not an operation but it is included here for ease of access.
    """
    #  Returns the type of its only argument, coded as a string.
    #  The possible results of this function are "nil"
    #  (a string, not the value nil),
    #  "number", "string", "boolean", "table", "function", "thread", and
    #  "userdata".
    if a is LuaNil:
        return "nil"
    if isinstance(a, LuaNumber):
        return "number"
    if isinstance(a, LuaString):
        return "string"
    if isinstance(a, LuaBool):
        return "boolean"
    if isinstance(a, LuaTable):
        return "table"
    if isinstance(a, LuaFunction):
        return "function"
    if isinstance(a, LuaThread):
        return "thread"
    if isinstance(a, LuaUserdata):
        return "userdata"
    raise TypeError(f"Unexpected type: {type(a)}")
