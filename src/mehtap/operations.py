from __future__ import annotations

from collections.abc import Sequence, MutableSequence
from typing import TypeAlias

from mehtap.values import (
    LuaBool,
    LuaValue,
    LuaString,
    LuaNumber,
    MAX_INT64,
    LuaNumberType,
    MIN_INT64,
    SIGN_BIT,
    ALL_SET,
    LuaNil,
    LuaTable,
    LuaFunction,
    LuaThread,
    LuaUserdata, LuaIndexableABC,
)


def rel_eq(a: LuaValue, b: LuaValue, *, raw: bool = False) -> LuaBool:
    """
    :param raw: Whether to bypass the ``__eq`` metamethod.
    :return: The result of ``a == b`` in Lua.
    """
    # Equality (==) first compares the type of its operands.
    # If the types are different, then the result is false.
    if type(a) is not type(b):
        return LuaBool(False)
    # Otherwise, the values of the operands are compared.
    # Strings are equal if they have the same byte content.
    if isinstance(a, LuaString):
        return LuaBool(a.content == b.content)
    # Numbers are equal if they denote the same mathematical value.
    if isinstance(a, LuaNumber):
        return LuaBool(a.value == b.value)
    # mehtap extension: All LuaBool(False) _and true_ objects are currently not all
    #               the same object :(
    if isinstance(a, LuaBool):
        return LuaBool(a.true == b.true)
    # Tables, userdata, and threads are compared by reference:
    # two objects are considered equal only if they are the same object.
    if a is b or raw:
        return LuaBool(True)
    # You can change the way that Lua compares tables and userdata by using the
    # __eq metamethod (see §2.4).
    if not raw:
        raise NotImplementedError()
    return LuaBool(a is b)  # TODO.


def rel_ne(a: LuaValue, b: LuaValue, *, raw: bool = False) -> LuaBool:
    """
    :param raw: Whether to bypass the ``__eq`` metamethod.
    :return: The result of ``a ~= b`` in Lua.
    """
    # The operator ~= is exactly the negation of equality (==).
    return LuaBool(not rel_eq(a, b, raw=raw).true)


def rel_lt(a: LuaValue, b: LuaValue) -> LuaBool:
    """
    :return: The result of ``a < b`` in Lua.
    """
    # The order operators work as follows.
    # If both arguments are numbers,
    if isinstance(a, LuaNumber) and isinstance(b, LuaNumber):
        # then they are compared according to their mathematical values,
        # regardless of their subtypes.
        return LuaBool(a.value < b.value)
    # Otherwise, if both arguments are strings,
    # then their values are compared according to the current locale.
    # Otherwise, Lua tries to call the __lt or the __le metamethod (see §2.4).
    raise NotImplementedError()  # TODO.


def rel_gt(a: LuaValue, b: LuaValue) -> LuaBool:
    """
    :return: The result of ``a > b`` in Lua.
    """
    # a > b is translated to b < a
    return rel_lt(b, a)


def rel_le(a: LuaValue, b: LuaValue) -> LuaBool:
    """
    :return: The result of ``a <= b`` in Lua.
    """
    # The order operators work as follows.
    # If both arguments are numbers,
    if isinstance(a, LuaNumber) and isinstance(b, LuaNumber):
        # then they are compared according to their mathematical values,
        # regardless of their subtypes.
        return LuaBool(a.value <= b.value)
    # Otherwise, if both arguments are strings,
    # then their values are compared according to the current locale.
    # Otherwise, Lua tries to call the __lt or the __le metamethod (see §2.4).
    raise NotImplementedError()  # TODO.


def rel_ge(a: LuaValue, b: LuaValue) -> LuaBool:
    """
    :return: The result of ``a >= b`` in Lua.
    """
    # a >= b is translated to b <= a
    return rel_le(b, a)


def int_wrap_overflow(value: int) -> LuaNumber:
    """Wrap around an integer value to the range of a signed 64-bit integer.

    The value is used as-is if it can already fit in a signed 64-bit integer.
    """
    if MIN_INT64 < value < MAX_INT64:
        return LuaNumber(value, LuaNumberType.INTEGER)
    whole_val, sign = divmod(value, MAX_INT64)
    if sign & 1:
        return LuaNumber(-whole_val, LuaNumberType.INTEGER)
    return LuaNumber(whole_val, LuaNumberType.INTEGER)


def coerce_float_to_int(value: LuaNumber) -> LuaNumber:
    """Coerce a number to an integer :class:`LuaNumber` if possible.

    :raises NotImplementedError: if the conversion fails.
    """
    if value.type is LuaNumberType.INTEGER:
        return value
    # The conversion from float to integer checks whether the float has an exact
    # representation as an integer
    # (that is, the float has an integral value
    # and it is in the range of integer representation).
    v = value.value
    if v.is_integer() and MIN_INT64 <= v <= MAX_INT64:
        # If it does, that representation is the result.
        return LuaNumber(int(v), LuaNumberType.INTEGER)
    # Otherwise, the conversion fails.
    raise NotImplementedError()  # TODO.


def coerce_int_to_float(value: LuaNumber) -> LuaNumber:
    """Coerce a number to a float :class:`LuaNumber`.

    This kind of conversion never fails.
    """
    if value.type is LuaNumberType.FLOAT:
        return value
    #  In a conversion from integer to float,
    #  if the integer value has an exact representation as a float,
    #  that is the result.
    #  Otherwise, the conversion gets the nearest higher or the nearest lower
    #  representable value.
    #  This kind of conversion never fails.
    return LuaNumber(float(value.value), LuaNumberType.FLOAT)


def arith_add(a, b):
    """
    :return: The result of ``a + b`` in Lua.
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # If both operands are integers,
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        # the operation is performed over integers and the result is an integer.
        return int_wrap_overflow(a.value + b.value)
    # Otherwise, if both operands are numbers,
    # then they are converted to floats,
    # the operation is performed following the machine's rules for
    # floating-point arithmetic (usually the IEEE 754 standard),
    # and the result is a float.
    return LuaNumber(
        coerce_int_to_float(a).value + coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


def overflow_arith_add(a, b) -> tuple[bool, LuaNumber]:
    """
    :return: a tuple *(o, r)* where *o* is a boolean indicating whether the
             addition overflows and *r* is the result of ``a + b`` in Lua.
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        summed = a.value + b.value
        wrapped = int_wrap_overflow(summed)
        return wrapped.value != summed, wrapped
    return False, LuaNumber(
        coerce_int_to_float(a).value + coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


def arith_sub(a, b):
    """
    :return: The result of ``a - b`` in Lua.
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value - b.value)
    return LuaNumber(
        coerce_int_to_float(a).value - coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


def arith_mul(a, b):
    """
    :return: The result of ``a * b`` in Lua.
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value * b.value)
    return LuaNumber(
        coerce_int_to_float(a).value * coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


def arith_float_div(a, b):
    """
    :return: The result of ``a / b`` in Lua, which is always a float.
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # Exponentiation and float division (/) always convert their operands to
    # floats and the result is always a float.
    return LuaNumber(
        coerce_int_to_float(a).value / coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


def arith_floor_div(a, b):
    """
    :return: The result of ``a // b`` in Lua.

             The result of floor division of *a* by *b* is defined as the result
             of the division of *a* by *b*
             rounded towards minus infinity.
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # Floor division (//) is a division that rounds the quotient towards minus
    # infinity, resulting in the floor of the division of its operands.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value // b.value)
    return LuaNumber(
        coerce_int_to_float(a).value // coerce_int_to_float(b).value,
        LuaNumberType.INTEGER,
    )


def arith_mod(a, b):
    """
    :return: The result of ``a % b`` in Lua.

             The result of modulo is defined as the remainder of a division that
             rounds the quotient towards minus infinity (floor division).
    :raises NotImplementedError: if ``a`` or ``b`` isn't a :class:`LuaNumber`.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # Modulo is defined as the remainder of a division that rounds the quotient
    # towards minus infinity (floor division).
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value % b.value)
    return LuaNumber(
        coerce_int_to_float(a).value % coerce_int_to_float(b).value,
        LuaNumberType.INTEGER,
    )


def arith_exp(a, b):
    """
    :return: The result of ``a ^ b`` in Lua, which is always a float.
    """
    # Exponentiation and float division (/) always convert their operands to
    # floats and the result is always a float.
    # Exponentiation uses the ISO C function pow,
    # so that it works for non-integer exponents too.
    return LuaNumber(
        coerce_int_to_float(a).value ** coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


def arith_unary_minus(a):
    """
    :return: The result of ``-a`` in Lua.
    """
    if not isinstance(a, LuaNumber):
        raise NotImplementedError()  # TODO.
    return LuaNumber(-a.value, a.type)


def _python_int_to_int64_luanumber(x: int) -> LuaNumber:
    """Convert a Python :class:`int` to a :class:`LuaNumber`.

    The input value, ``x``, is treated as an int64.
    If the value is greater than :data:`MAX_INT64`,
        * Bit value 1<<63 is interpreted as the sign bit.
        * Bit values greater than 1<<64 are ignored.
    """
    x = x & ALL_SET
    if x & SIGN_BIT:
        return LuaNumber(-x + MAX_INT64, LuaNumberType.INTEGER)
    return LuaNumber(x, LuaNumberType.INTEGER)


def bitwise_or(a, b) -> LuaNumber:
    """
    :return: The result of ``a | b`` in Lua.
    """
    #  All bitwise operations convert its operands to integers (see §3.4.3),
    #  operate on all bits of those integers,
    #  and result in an integer.
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    return _python_int_to_int64_luanumber(a.value | b.value)


def bitwise_xor(a, b) -> LuaNumber:
    """
    :return: The result of ``a ~ b`` in Lua.
    """
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    return _python_int_to_int64_luanumber(a.value ^ b.value)


def bitwise_and(a, b) -> LuaNumber:
    """
    :return: The result of ``a & b`` in Lua.
    """
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    return _python_int_to_int64_luanumber(a.value & b.value)


def bitwise_shift_left(a, b) -> LuaNumber:
    """
    :return: The result of ``a << b`` in Lua.
    """
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    # Both right and left shifts fill the vacant bits with zeros.
    # Negative displacements shift to the other direction;
    if b.value < 0:
        return bitwise_shift_right(a, arith_unary_minus(b))
    # displacements with absolute values equal to or higher than the number of
    # bits in an integer result in zero (as all bits are shifted out).
    if b.value >= 64:
        return LuaNumber(0, LuaNumberType.INTEGER)
    return _python_int_to_int64_luanumber(a.value << b.value)


def bitwise_shift_right(a, b) -> LuaNumber:
    """
    :return: The result of ``a >> b`` in Lua.
    """
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    if b.value < 0:
        return bitwise_shift_left(a, arith_unary_minus(b))
    if b.value >= 64:
        return LuaNumber(0, LuaNumberType.INTEGER)
    return _python_int_to_int64_luanumber(a.value >> b.value)


def bitwise_unary_not(a) -> LuaNumber:
    """
    :return: The result of ``~a`` in Lua.
    """
    a = coerce_float_to_int(a)
    return _python_int_to_int64_luanumber(~a.value)


def coerce_to_bool(a: LuaValue) -> LuaBool:
    """Coerce a value to a boolean.

    ``false`` and ``nil`` are ``false``; everything else is ``true``.
    """
    # Like the control structures (see §3.3.4),
    # all logical operators consider both false and nil as false
    # and anything else as true.
    if a is LuaNil:
        return LuaBool(False)
    if isinstance(a, LuaBool):
        return a
    return LuaBool(True)


def logical_unary_not(a: LuaValue) -> LuaBool:
    """
    :return: The result of ``not a`` in Lua.
    """
    # The negation operator not always returns false or true.
    return LuaBool(not coerce_to_bool(a).true)


def is_false_or_nil(a: LuaValue) -> bool:
    """
    :return: :data:`True` if ``a`` is ``false`` or ``nil``, :data:`False`
             otherwise.
    """
    if a is LuaNil:
        return True
    if isinstance(a, LuaBool):
        return not a.true
    return False


def str_to_lua_string(s: str) -> LuaString:
    """Convert a Python string to a Lua string.

    The Python string is encoded in ASCII.
    """
    return LuaString(s.encode("ascii"))


def concat(a: LuaValue, b: LuaValue) -> LuaString:
    """
    :return: The result of ``a .. b`` in Lua.
    """
    # If both operands are strings or numbers,
    types = (LuaString, LuaNumber)
    if isinstance(a, types) and isinstance(b, types):
        # then the numbers are converted to strings in a non-specified format
        # (see §3.4.3).
        if isinstance(a, LuaNumber):
            a = str_to_lua_string(str(a))
        if isinstance(b, LuaNumber):
            b = str_to_lua_string(str(b))
        return LuaString(a.content + b.content)
    # Otherwise, the __concat metamethod is called (see §2.4).
    raise NotImplementedError()  # TODO.


# TODO: Change the default value of raw to False.
def length(a: LuaValue, *, raw: bool = True) -> LuaNumber:
    """
    :return: The result of ``#a`` in Lua.
    """
    # The length of a string is its number of bytes.
    if isinstance(a, LuaString):
        return LuaNumber(len(a.content), LuaNumberType.INTEGER)

    # A program can modify the behavior of the length operator for any value but
    # strings through the __len metamethod (see §2.4).
    # TODO.

    if a.has_metamethod(LuaString(b"__len")) and not raw:
        raise NotImplementedError()  # TODO.

    if isinstance(a, LuaIndexableABC):
        if not a.map:
            return LuaNumber(0, LuaNumberType.INTEGER)
        border = 0
        while a.has(LuaNumber(border + 1, LuaNumberType.INTEGER)):
            border += 1
            if border == MAX_INT64:
                break
        return LuaNumber(border, LuaNumberType.INTEGER)

    raise NotImplementedError()  # TODO.


Multires: TypeAlias = "Sequence[LuaValue | Multires]"
"""
A list where each element is either a :class:`LuaValue` or
:data:`Multires`.
"""


def adjust(multires: Multires, needed: int) -> Sequence[LuaValue]:
    """
    :param multires: The multires of input values.
    :param needed: The amount of values needed.
    :return: Values adjusted to the amount of values needed according to
             `the rules on adjustment of Lua`_.

    .. _the rules on adjustment of Lua:
       https://lua.org/manual/5.4/manual.html#3.4.12
    """
    # When the list of expressions ends with a multires expression,
    # all results from that expression
    # enter the list of values before the adjustment.
    multires = [x for x in multires]
    if multires and isinstance(multires[-1], Sequence):
        multires.extend(multires.pop())

    # The adjustment follows these rules:
    # If there are more values than needed,
    if len(multires) > needed:
        # the extra values are thrown away;
        multires = multires[:needed]
    # if there are fewer values than needed,
    if len(multires) < needed:
        # the list is extended with nil's.
        multires.extend([LuaNil] * (needed - len(multires)))

    # When a multires expression is used in a list of expressions without being
    # the last element, ..., Lua adjusts the result list of that expression
    # to one element.
    for i, value in enumerate(multires):
        if isinstance(value, Sequence):
            multires[i] = adjust(value, 1)[0]

    return multires


def adjust_flatten(multires: Multires) -> Sequence[LuaValue]:
    """
    :return: The input multires where each element is adjusted to one value
             except for the last, which is extended to the list of previous
             values.
    """
    multires = [x for x in multires]
    if multires and isinstance(multires[-1], Sequence):
        multires.extend(multires.pop())
    for i, value in enumerate(multires):
        if isinstance(value, Sequence):
            multires[i] = adjust(value, 1)[0]
    return multires


def adjust_to_one(multires_or_value: Multires | LuaValue) -> LuaValue:
    """Adjusts a multires or a single Lua value to one value.

    If the input is a multires, it adjusts the multires to one value.
    If the input is a single Lua value, it returns the value as is.

    :param multires_or_value: The multires or single Lua value to adjust.
    :return: A single Lua value.
    """
    if isinstance(multires_or_value, Sequence):
        return adjust(multires_or_value, 1)[0]
    return multires_or_value
