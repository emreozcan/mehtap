from __future__ import annotations

from locale import strcoll
from typing import TypeAlias, TYPE_CHECKING

from mehtap.control_structures import LuaError
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
    LuaUserdata, LuaIndexableABC, LuaCallableABC, type_of_lv,
)


if TYPE_CHECKING:
    from mehtap.scope import Scope


SYMBOL__EQ = LuaString(b"__eq")
SYMBOL__LEN = LuaString(b"__len")


def check_metamethod_binary(a: LuaValue, b: LuaValue, mm_name: LuaString) \
        -> LuaValue | None:
    mm = a.get_metavalue(mm_name)
    if mm is None:
        mm = b.get_metavalue(mm_name)
        if mm is None:
            return None
    # mm is not None
    return adjust_to_one(call(mm, args=[a, b], scope=None))


def check_metamethod_unary(a: LuaValue, mm_name: LuaString) \
        -> LuaValue | None:
    mm = a.get_metavalue(mm_name)
    if mm is None:
        return None
    return adjust_to_one(call(mm, args=[a], scope=None))


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
    # mehtap extension: All LuaBool(False) _and true_ objects are currently not
    #                   all the same object :(
    if isinstance(a, LuaBool):
        return LuaBool(a.true == b.true)
    # Tables, userdata, and threads are compared by reference:
    # two objects are considered equal only if they are the same object.
    # You can change the way that Lua compares tables and userdata by using the
    # __eq metamethod (see §2.4).
    mt_types = (LuaTable, LuaUserdata)
    if isinstance(a, mt_types) and isinstance(b, mt_types) and not raw:
        mm_res = check_metamethod_binary(a, b, SYMBOL__EQ)
        if mm_res is not None:
            return coerce_to_bool(mm_res)
    return LuaBool(a is b)


def rel_ne(a: LuaValue, b: LuaValue, *, raw: bool = False) -> LuaBool:
    """
    :param raw: Whether to bypass the ``__eq`` metamethod.
    :return: The result of ``a ~= b`` in Lua.
    """
    # The operator ~= is exactly the negation of equality (==).
    return LuaBool(not rel_eq(a, b, raw=raw).true)


SYMBOL__LT = LuaString(b"__lt")


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
    if isinstance(a, LuaString) and isinstance(b, LuaString):
        return LuaBool(strcoll(a.content, b.content) < 0)
    # Otherwise, Lua tries to call the __lt or the __le metamethod (see §2.4).
    mm_res = check_metamethod_binary(a, b, SYMBOL__LT)
    if mm_res is not None:
        return coerce_to_bool(mm_res)
    a_type = type_of_lv(a)
    b_type = type_of_lv(b)
    raise LuaError(f"attempt to compare {a_type} with {b_type}")


def rel_gt(a: LuaValue, b: LuaValue) -> LuaBool:
    """
    :return: The result of ``a > b`` in Lua.
    """
    # a > b is translated to b < a
    return rel_lt(b, a)


SYMBOL__LE = LuaString(b"__le")


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
    if isinstance(a, LuaString) and isinstance(b, LuaString):
        return LuaBool(strcoll(a.content, b.content) <= 0)
    # Otherwise, Lua tries to call the __lt or the __le metamethod (see §2.4).
    mm_res = check_metamethod_binary(a, b, SYMBOL__LE)
    if mm_res is not None:
        return coerce_to_bool(mm_res)
    a_type = type_of_lv(a)
    b_type = type_of_lv(b)
    raise LuaError(f"attempt to compare {a_type} with {b_type}")


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

    :raises LuaError: if the conversion fails.
    """
    if not isinstance(value, LuaNumber):
        value_type = type_of_lv(value)
        raise LuaError(f"can't coerce {value_type} value to an integer")
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
    raise LuaError("number has no integer representation")


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


SYMBOL__ADD = LuaString(b"__add")


def arith_add(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a + b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__ADD)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to add {a_type} and {b_type} values")
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


def overflow_arith_add(a: LuaValue, b: LuaValue) -> tuple[bool, LuaNumber]:
    """
    :return: a tuple *(o, r)* where *o* is a boolean indicating whether the
             addition overflows and *r* is the result of ``a + b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        type_a = type_of_lv(a)
        type_b = type_of_lv(b)
        raise LuaError(f"attempt to add {type_a} and {type_b} values")
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        summed = a.value + b.value
        wrapped = int_wrap_overflow(summed)
        return wrapped.value != summed, wrapped
    return False, LuaNumber(
        coerce_int_to_float(a).value + coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


SYMBOL__SUB = LuaString(b"__sub")


def arith_sub(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a - b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__SUB)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to subtract {a_type} and {b_type} values")
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value - b.value)
    return LuaNumber(
        coerce_int_to_float(a).value - coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


SYMBOL__MUL = LuaString(b"__mul")


def arith_mul(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a * b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__MUL)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to multiply {a_type} and {b_type} values")
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value * b.value)
    return LuaNumber(
        coerce_int_to_float(a).value * coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


SYMBOL__DIV = LuaString(b"__div")


def arith_float_div(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a / b`` in Lua, which is always a float.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__DIV)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to divide {a_type} and {b_type} values")
    # Exponentiation and float division (/) always convert their operands to
    # floats and the result is always a float.
    a_float = coerce_int_to_float(a).value
    b_float = coerce_int_to_float(b).value
    if b_float == 0:
        if a_float == 0:
            return LuaNumber(float("nan"), LuaNumberType.FLOAT)
        if a_float < 0:
            return LuaNumber(float("-inf"), LuaNumberType.FLOAT)
        return LuaNumber(float("inf"), LuaNumberType.FLOAT)
    return LuaNumber(a_float / b_float, LuaNumberType.FLOAT)


SYMBOL__IDIV = LuaString(b"__idiv")


def arith_floor_div(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a // b`` in Lua.

             The result of floor division of *a* by *b* is defined as the result
             of the division of *a* by *b*
             rounded towards minus infinity.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__IDIV)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to floor divide {a_type} and {b_type} values")
    # Floor division (//) is a division that rounds the quotient towards minus
    # infinity, resulting in the floor of the division of its operands.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value // b.value)
    return LuaNumber(
        coerce_int_to_float(a).value // coerce_int_to_float(b).value,
        LuaNumberType.INTEGER,
    )


SYMBOL__MOD = LuaString(b"__mod")


def arith_mod(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a % b`` in Lua.

             The result of modulo is defined as the remainder of a division that
             rounds the quotient towards minus infinity (floor division).
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__MOD)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to modulo {a_type} and {b_type} values")
    # Modulo is defined as the remainder of a division that rounds the quotient
    # towards minus infinity (floor division).
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_wrap_overflow(a.value % b.value)
    return LuaNumber(
        coerce_int_to_float(a).value % coerce_int_to_float(b).value,
        LuaNumberType.INTEGER,
    )


SYMBOL__POW = LuaString(b"__pow")


def arith_exp(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a ^ b`` in Lua, which is always a float.
    """
    # Exponentiation and float division (/) always convert their operands to
    # floats and the result is always a float.
    # Exponentiation uses the ISO C function pow,
    # so that it works for non-integer exponents too.
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__POW)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to exponentiate {a_type} and {b_type} values")
    return LuaNumber(
        coerce_int_to_float(a).value ** coerce_int_to_float(b).value,
        LuaNumberType.FLOAT,
    )


SYMBOL__UNM = LuaString(b"__unm")


def arith_unary_minus(a: LuaValue) -> LuaValue:
    """
    :return: The result of ``-a`` in Lua.
    """
    if not isinstance(a, LuaNumber):
        mm_res = check_metamethod_unary(a, SYMBOL__UNM)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        raise LuaError(f"attempt to negate a {a_type} value")
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


SYMBOL__BOR = LuaString(b"__bor")


def bitwise_or(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a | b`` in Lua.
    """
    #  All bitwise operations convert its operands to integers (see §3.4.3),
    #  operate on all bits of those integers,
    #  and result in an integer.
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__BOR)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to bitwise or {a_type} and {b_type} values")
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    return _python_int_to_int64_luanumber(a.value | b.value)


SYMBOL__BXOR = LuaString(b"__bxor")


def bitwise_xor(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a ~ b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__BXOR)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to bitwise xor {a_type} and {b_type} values")
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    return _python_int_to_int64_luanumber(a.value ^ b.value)


SYMBOL__BAND = LuaString(b"__band")


def bitwise_and(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a & b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__BAND)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to bitwise and {a_type} and {b_type} values")
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    return _python_int_to_int64_luanumber(a.value & b.value)


SYMBOL__SHL = LuaString(b"__shl")


def bitwise_shift_left(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a << b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__SHL)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to shift left {a_type} and {b_type} values")
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


SYMBOL__SHR = LuaString(b"__shr")


def bitwise_shift_right(a: LuaValue, b: LuaValue) -> LuaValue:
    """
    :return: The result of ``a >> b`` in Lua.
    """
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        mm_res = check_metamethod_binary(a, b, SYMBOL__SHR)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to shift right {a_type} and {b_type} values")
    a = coerce_float_to_int(a)
    b = coerce_float_to_int(b)
    if b.value < 0:
        return bitwise_shift_left(a, arith_unary_minus(b))
    if b.value >= 64:
        return LuaNumber(0, LuaNumberType.INTEGER)
    return _python_int_to_int64_luanumber(a.value >> b.value)


SYMBOL__BNOT = LuaString(b"__bnot")


def bitwise_unary_not(a: LuaValue) -> LuaValue:
    """
    :return: The result of ``~a`` in Lua.
    """
    if not isinstance(a, LuaNumber):
        mm_res = check_metamethod_unary(a, SYMBOL__BNOT)
        if mm_res is not None:
            return mm_res
        a_type = type_of_lv(a)
        raise LuaError(f"attempt to bitwise not a {a_type} value")
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


SYMBOL__CONCAT = LuaString(b"__concat")


def concat(a: LuaValue, b: LuaValue) -> LuaValue:
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
    mm_res = check_metamethod_binary(a, b, SYMBOL__CONCAT)
    if mm_res is None:
        a_type = type_of_lv(a)
        b_type = type_of_lv(b)
        raise LuaError(f"attempt to concatenate {a_type} and {b_type} values")
    return mm_res


def length(a: LuaValue, *, raw: bool = False) -> LuaValue:
    """
    :return: The result of ``#a`` in Lua.
    """
    # The length of a string is its number of bytes.
    if isinstance(a, LuaString):
        return LuaNumber(len(a.content), LuaNumberType.INTEGER)

    if a.has_metavalue(SYMBOL__LEN) and not raw:
        mm_result = check_metamethod_unary(a, SYMBOL__LEN)
        if mm_result is not None:
            return mm_result

    if isinstance(a, LuaIndexableABC):
        border = 0
        while a.has(LuaNumber(border + 1, LuaNumberType.INTEGER)):
            border += 1
            if border == MAX_INT64:
                break
        return LuaNumber(border, LuaNumberType.INTEGER)

    type_string = type_of_lv(a)
    raise LuaError(f"attempt to get length of a {type_string} value")


SYMBOL__INDEX = LuaString(b"__index")


def index(a: LuaValue, b: LuaValue) -> LuaValue:
    mv = a.get_metavalue(SYMBOL__INDEX)
    if mv is None:
        if isinstance(a, LuaIndexableABC):
            return a.rawget(b)
        raise LuaError(f"attempt to index a {type_of_lv(a)} value")
    if isinstance(a, LuaIndexableABC) and a.has(b):
        return a.rawget(b)
    allowed_mv = (LuaFunction, LuaIndexableABC)
    if not (isinstance(mv, allowed_mv) or mv.has_metavalue(SYMBOL__INDEX)):
        raise LuaError(
            f"metavalue for '__index' must be a function, table, or a value "
            f"with an '__index' metavalue"
        )
    if isinstance(mv, LuaFunction):
        return adjust_to_one(call(mv, args=[a, b], scope=None))
    return index(mv, b)


SYMBOL__NEWINDEX = LuaString(b"__newindex")


def new_index(a: LuaValue, b: LuaValue, c: LuaValue):
    mv = a.get_metavalue(SYMBOL__NEWINDEX)
    if mv is None:
        if isinstance(a, LuaIndexableABC):
            a.rawput(b, c)
            return
        raise LuaError(f"attempt to index a {type_of_lv(a)} value")
    if isinstance(a, LuaIndexableABC) and a.has(b):
        a.rawput(b, c)
        return
    allowed_mv = (LuaFunction, LuaIndexableABC)
    if not (isinstance(mv, allowed_mv) or mv.has_metavalue(SYMBOL__NEWINDEX)):
        raise LuaError(
            f"metavalue for '__newindex' must be a function, table, or a value "
            f"with a '__newindex' metavalue"
        )
    if isinstance(mv, LuaFunction):
        call(mv, args=[a, b, c], scope=None)
        return
    new_index(mv, b, c)


SYMBOL__CALL = LuaString(b"__call")


def call(
    function: LuaValue,
    args: Multires,
    scope: Scope | None,
    *,
    modify_tb: bool = True,
) -> list[LuaValue]:
    if isinstance(function, LuaCallableABC):
        return function.rawcall(args, scope=scope, modify_tb=modify_tb)
    mv = function.get_metavalue(SYMBOL__CALL)
    if mv is None:
        raise LuaError(f"attempt to call {type_of_lv(function)} value")
    if not isinstance(mv, LuaCallableABC):
        raise LuaError(f"attempt to call {type_of_lv(mv)} value")
    return mv.rawcall([function, *args], scope=scope, modify_tb=modify_tb)


Multires: TypeAlias = "list[LuaValue | Multires]"
"""
A list where each element is either a :class:`LuaValue` or
:data:`Multires`.
"""


def adjust(multires: Multires, needed: int) -> list[LuaValue]:
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
    multires = [x for x in multires]  # Create a shallow copy of multires.
    if multires and isinstance(multires[-1], list):
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
        if isinstance(value, list):
            multires[i] = adjust(value, 1)[0]

    return multires


def adjust_flatten(multires: Multires) -> list[LuaValue]:
    """
    :return: The input multires where each element is adjusted to one value
             except for the last, which is extended to the list of previous
             values.
    """
    multires = [x for x in multires]
    if multires and isinstance(multires[-1], list):
        multires.extend(multires.pop())
    for i, value in enumerate(multires):
        if isinstance(value, list):
            multires[i] = adjust(value, 1)[0]
    return multires


def adjust_to_one(multires_or_value: Multires | LuaValue) -> LuaValue:
    """Adjusts a multires or a single Lua value to one value.

    If the input is a multires, it adjusts the multires to one value.
    If the input is a single Lua value, it returns the value as is.

    :param multires_or_value: The multires or single Lua value to adjust.
    :return: A single Lua value.
    """
    if isinstance(multires_or_value, list):
        return adjust(multires_or_value, 1)[0]
    return multires_or_value
