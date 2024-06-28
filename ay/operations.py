from .values import LuaBool, LuaValue, LuaString, LuaNumber, MAX_INT64, \
    LuaNumberType, MIN_INT64


def rel_eq(a: LuaValue, b: LuaValue) -> LuaBool:
    # Equality (==) first compares the type of its operands.
    # If the types are different, then the result is false.
    type_a = type(a)
    if type_a is not type(b):
        return LuaBool(False)
    # Otherwise, the values of the operands are compared.
    # Strings are equal if they have the same byte content.
    if type_a is LuaString:
        a: LuaString
        b: LuaString
        return LuaBool(a.content == b.content)
    # Numbers are equal if they denote the same mathematical value.
    if type_a is LuaNumber:
        a: LuaNumber
        b: LuaNumber
        return LuaBool(a.value == b.value)
    # Tables, userdata, and threads are compared by reference:
    # two objects are considered equal only if they are the same object.
    return LuaBool(a is b)


def rel_ne(a: LuaValue, b: LuaValue) -> LuaBool:
    # The operator ~= is exactly the negation of equality (==).
    return LuaBool(not rel_eq(a, b).true)


def rel_lt(a: LuaValue, b: LuaValue) -> LuaBool:
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
    # a > b is translated to b < a
    return rel_lt(b, a)


def rel_le(a: LuaValue, b: LuaValue) -> LuaBool:
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
    # a >= b is translated to b <= a
    return rel_le(b, a)


def int_overflow_wrap_around(value: int) -> LuaNumber:
    if value < MAX_INT64:
        return LuaNumber(value, LuaNumberType.INTEGER)
    whole_val, sign = divmod(value, MAX_INT64)
    if sign & 1:
        return LuaNumber(-whole_val, LuaNumberType.INTEGER)
    return LuaNumber(whole_val, LuaNumberType.INTEGER)


def coerce_float_to_int(value: LuaNumber) -> LuaNumber:
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
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # If both operands are integers,
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        # the operation is performed over integers and the result is an integer.
        return int_overflow_wrap_around(a.value + b.value)
    # Otherwise, if both operands are numbers,
    # then they are converted to floats,
    # the operation is performed following the machine's rules for
    # floating-point arithmetic (usually the IEEE 754 standard),
    # and the result is a float.
    return LuaNumber(
        coerce_int_to_float(a).value + coerce_int_to_float(b).value,
        LuaNumberType.FLOAT
    )


def arith_sub(a, b):
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_overflow_wrap_around(a.value - b.value)
    return LuaNumber(
        coerce_int_to_float(a).value - coerce_int_to_float(b).value,
        LuaNumberType.FLOAT
    )


def arith_mul(a, b):
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_overflow_wrap_around(a.value * b.value)
    return LuaNumber(
        coerce_int_to_float(a).value * coerce_int_to_float(b).value,
        LuaNumberType.FLOAT
    )


def arith_float_div(a, b):
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # Exponentiation and float division (/) always convert their operands to
    # floats and the result is always a float.
    return LuaNumber(
        coerce_int_to_float(a).value / coerce_int_to_float(b).value,
        LuaNumberType.FLOAT
    )


def arith_floor_div(a, b):
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # Floor division (//) is a division that rounds the quotient towards minus
    # infinity, resulting in the floor of the division of its operands.
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_overflow_wrap_around(a.value // b.value)
    return LuaNumber(
        coerce_int_to_float(a).value // coerce_int_to_float(b).value,
        LuaNumberType.INTEGER
    )


def arith_mod(a, b):
    if not isinstance(a, LuaNumber) or not isinstance(b, LuaNumber):
        raise NotImplementedError()  # TODO.
    # Modulo is defined as the remainder of a division that rounds the quotient
    # towards minus infinity (floor division).
    if a.type == LuaNumberType.INTEGER and b.type == LuaNumberType.INTEGER:
        return int_overflow_wrap_around(a.value % b.value)
    return LuaNumber(
        coerce_int_to_float(a).value % coerce_int_to_float(b).value,
        LuaNumberType.INTEGER
    )


def arith_exp(a, b):
    # Exponentiation and float division (/) always convert their operands to
    # floats and the result is always a float.
    # Exponentiation uses the ISO C function pow,
    # so that it works for non-integer exponents too.
    return LuaNumber(
        coerce_int_to_float(a).value ** coerce_int_to_float(b).value,
        LuaNumberType.FLOAT
    )


def arith_unary_minus(a):
    if not isinstance(a, LuaNumber):
        raise NotImplementedError()  # TODO.
    return LuaNumber(-a.value, a.type)
