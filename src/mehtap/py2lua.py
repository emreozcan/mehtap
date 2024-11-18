from __future__ import annotations

from inspect import signature
from collections.abc import Mapping, Iterable, Callable
from typing import (
    overload,
    Union,
    Literal,
    TYPE_CHECKING,
    Protocol,
    TypeVar, ParamSpec, Concatenate,
)

from mehtap.operations import str_to_lua_string
from mehtap.scope import Scope
from mehtap.values import (
    LuaValue,
    LuaFunction,
    LuaTable,
    LuaString,
    LuaNil,
    LuaBool,
    LuaNumber,
)


if TYPE_CHECKING:
    from mehtap.values import LuaNilType


LV = TypeVar("LV", bound=LuaValue, covariant=True)


class SupportsLua(Protocol[LV]):
    """SupportsLua(Protocol[LV])
    Protocol for objects that can be converted to :class:`LuaValue`.

    :func:`py2lua` will call the ``__lua__`` method of the object if it exists.
    The result is considered the result of the conversion, so it is expected to
    be a :class:`LuaValue` instance.
    """

    def __lua__(self) -> LV:
        """
        The conversion method that :func:`py2lua` will call, and that supporters
        must implement.
        :return: A :class:`LuaValue` instance that represents the object.
        """
        pass


# This uses Union[A, B] instead of A | B because it is shorter in this case.
PyLuaNative = Union[None, bool, int, float, str, Mapping, Iterable, Callable]
"""Types that :func:`py2lua` knows how to convert natively."""
Py2LuaAccepts = PyLuaNative | SupportsLua[LV]
"""Types that :func:`py2lua` knows how to convert."""


@overload
def py2lua(value: None) -> LuaNilType: ...


@overload
def py2lua(value: bool) -> LuaBool: ...


@overload
def py2lua(value: int | float) -> LuaNumber: ...


@overload
def py2lua(value: str | bytes) -> LuaString: ...


@overload
def py2lua(value: Mapping) -> LuaTable: ...


@overload
def py2lua(value: Iterable) -> LuaTable: ...


@overload
def py2lua(value: Callable) -> LuaFunction: ...


@overload
def py2lua(value: SupportsLua[LV]) -> LV: ...


def py2lua(value):
    """Convert a plain Python value to a :class:`LuaValue`.

    If the value (or a member of the value) has a ``__lua__`` dunder method,
    (or, in other words implements the
    :class:`SupportsLua protocol <SupportsLua>`)
    the converter will call it and convert its return value instead.

    Iterables will be converted to sequence tables starting from the index
    :data:`1`.

    Functions are converted using ``@lua_function(wrap_values=True)``.
    See :func:`lua_function` for more information.

    This function is implemented using memoization,
    so it can convert recursive data structures.

    :raises TypeError: if the value can't be converted
    """
    return _py2lua(value, {})


def _py2lua(py_val, memos):
    if id(py_val) in memos:
        return memos[id(py_val)]
    if py_val is None:
        return LuaNil
    if hasattr(py_val, "__lua__"):
        return py_val.__lua__()
    if isinstance(py_val, bool):
        return LuaBool(py_val)
    if isinstance(py_val, (int, float)):
        return LuaNumber(py_val)
    if isinstance(py_val, str):
        return LuaString(py_val.encode("utf-8"))
    if isinstance(py_val, bytes):
        return LuaString(py_val)
    if isinstance(py_val, Mapping):
        m = LuaTable()
        memos[id(py_val)] = m
        for k, v in py_val.items():
            m.rawput(_py2lua(k, memos), _py2lua(v, memos))
        return m
    if isinstance(py_val, Iterable):
        m = LuaTable()
        memos[id(py_val)] = m
        for i, v in enumerate(py_val, start=1):
            m.rawput(LuaNumber(i), _py2lua(v, memos))
        return m
    if callable(py_val):
        return lua_function(wrap_values=True)(py_val)
    raise TypeError(f"can't convert {py_val!r} to LuaValue")


PyLuaRet = list[LuaValue] | None
PyLuaWrapRet = list[Py2LuaAccepts] | None
P = ParamSpec("P")
if TYPE_CHECKING:
    LuaCallback = TypeVar(
        "LuaCallback",
        bound=Callable[..., PyLuaRet],
    )
    LuaScopeCallback = TypeVar(
        "LuaScopeCallback",
        bound=Callable[Concatenate[Scope, ...], PyLuaRet],
    )
    PyCallback = TypeVar(
        "PyCallback",
        bound=Callable[..., PyLuaWrapRet],
    )
    PyScopeCallback = TypeVar(
        "PyScopeCallback",
        bound=Callable[Concatenate[Scope, ...], PyLuaWrapRet],
    )


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[False] = False,
    wrap_values: Literal[False] = False,
    rename_args: list[str] | None = None,
    preserve: Literal[False] = False,
) -> Callable[[LuaCallback], LuaFunction]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[False] = False,
    wrap_values: Literal[False] = False,
    rename_args: list[str] | None = None,
    preserve: Literal[True] = True,
) -> Callable[[LuaCallback], LuaCallback]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[False] = False,
    wrap_values: Literal[True] = True,
    rename_args: list[str] | None = None,
    preserve: Literal[False] = False,
) -> Callable[[PyCallback], LuaFunction]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[False] = False,
    wrap_values: Literal[True] = True,
    rename_args: list[str] | None = None,
    preserve: Literal[True] = True,
) -> Callable[[PyCallback], PyCallback]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[True] = True,
    wrap_values: Literal[False] = False,
    rename_args: list[str] | None = None,
    preserve: Literal[False] = False,
) -> Callable[[LuaScopeCallback], LuaFunction]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[True] = True,
    wrap_values: Literal[False] = False,
    rename_args: list[str] | None = None,
    preserve: Literal[True] = True,
) -> Callable[[LuaScopeCallback], LuaScopeCallback]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[True] = True,
    wrap_values: Literal[True] = True,
    rename_args: list[str] | None = None,
    preserve: Literal[False] = False,
) -> Callable[[PyScopeCallback], LuaFunction]: ...


@overload
def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: Literal[True] = True,
    wrap_values: Literal[True] = True,
    rename_args: list[str] | None = None,
    preserve: Literal[True] = True,
) -> Callable[[PyScopeCallback], PyScopeCallback]: ...


def lua_function(
    table: LuaTable | None = None,
    *,
    name: str | None = None,
    gets_scope: bool = False,
    wrap_values: bool = False,
    rename_args: list[str] | None = None,
    preserve: bool | None = False,
):
    """Convert a Python callable to a :class:`LuaFunction` instance.

    :param table: If provided, the newly created :class:`LuaFunction` will be
                  put into the table with the proper name.
    :param name: Allows to rename the function.
    :param gets_scope: Whether the function requires a :class:`Scope` as its
                       first argument.
    :param wrap_values: Whether the values should be converted to/from
                        Lua/Python
                        when passing them to/from the function.
    :param rename_args: Allows to rename the arguments of the function.
    :param preserve: If set to True, the original function will be returned
                     instead of the :class:`LuaFunction` instance.
                     The table will still get the LuaFunction instance.
    :return: A decorator that turns Python functions to :class:`LuaFunction`
             instances.

    The arguments of the decorated function must be positional-only.
    The function may have a variadic parameter as the last one.
    For example, ``def f(a, b, c, /): ...`` or
    ``def f(a, b, /, *args): ...``.

    If the function throws an exception, it will be caught and a similar error
    will be re-raised in Lua.

    If *gets_scope* is set to True, the function will receive a scope as its
    first argument.

    When *wrap_values* is set to True, the function will receive and return
    Python values.
    If the function returns a list or tuple, it will be
    returned in Lua as a multires.
    If it returns a single value, it will be
    returned as a single value.

    When *wrap_values* is set to False, the function's arguments will be
    instances of :class:`LuaValue` and the function will return a list of
    :class:`LuaValue` instances.
    Note that since function calls in Lua are multires expressions, functions
    always return a list of values. Returning :data:`None` is equivalent to
    returning an empty list.

    If *rename_args* is provided, it should be a list of strings with the same
    length as the number of arguments of the function.
    This change is only cosmetic since only parameter order is used to bind
    arguments to the function.

    If *preserve* is set to True, *table* must not be left empty.
    """
    return _lua_function(
        table=table,
        name=name,
        rename_args=rename_args,
        gets_scope=gets_scope,
        wrap_values=wrap_values,
        preserve=preserve if preserve is not None else False,
    )


def _lua_function(
    *,
    table: LuaTable | None,
    name: str | None,
    rename_args: list[str] | None,
    gets_scope: bool,
    wrap_values: bool,
    preserve: bool,
):
    from mehtap.control_structures import ReturnException

    if preserve and not table:
        raise ValueError(
            "So, the decorator will preserve the object and will not put the"
            " LuaFunction instance in the table... What's your point?"
        )

    def decorator(func: Callable):
        f_signature = signature(func)
        callable_argnames = []
        minimum_required = 0
        f_variadic = False
        scope_skipped = False
        for param in f_signature.parameters.values():
            if gets_scope and not scope_skipped:
                scope_skipped = True
                continue
            if f_variadic:
                raise ValueError(
                    f"Function {func.__qualname__} has a parameter after a "
                    f"variadic parameter ({param.name})"
                )
            if param.kind == param.POSITIONAL_ONLY:
                if param.default is param.empty:
                    minimum_required += 1
            elif param.kind == param.VAR_POSITIONAL:
                f_variadic = True
                continue
            else:
                raise ValueError(
                    f"Function {func.__qualname__} has a parameter {param.name}"
                    f"that is not positional or variadic"
                )
            callable_argnames.append(param.name)

        if wrap_values:

            def new_function(*args: LuaValue) -> None:
                from mehtap.lua2py import lua2py

                return_values = func(*(lua2py(v) for v in args))
                if isinstance(return_values, (list, tuple)):
                    raise ReturnException([py2lua(v) for v in return_values])
                raise ReturnException([py2lua(return_values)])

        else:

            def new_function(*args: LuaValue) -> None:
                raise ReturnException(func(*args))

        if rename_args is None:
            lua_param_names = [str_to_lua_string(x) for x in callable_argnames]
        else:
            callable_arg_count = len(callable_argnames)
            rename_arg_count = len(rename_args)
            if callable_arg_count != rename_arg_count:
                scope_warning = (
                    "(not counting the scope parameter,) " if gets_scope else ""
                )
                raise ValueError(
                    f"Callable has {callable_arg_count} parameters "
                    f"{scope_warning}but "
                    f"{len(rename_args)} names were supplied"
                )
            lua_param_names = [str_to_lua_string(x) for x in rename_args]

        used_name = name if name is not None else func.__name__
        if not used_name:
            used_name = "<native function>"

        lf = LuaFunction(
            param_names=lua_param_names,
            variadic=f_variadic,
            parent_scope=None,
            block=new_function,
            gets_scope=gets_scope,
            name=used_name,
            min_req=minimum_required,
        )
        if table is not None:
            table.rawput(py2lua(used_name), lf)

        if preserve:
            return func
        return lf

    return decorator
