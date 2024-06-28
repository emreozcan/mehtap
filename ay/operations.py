from .values import LuaBool, LuaValue, LuaString, LuaNumber


def rel_eq(a: LuaValue, b: LuaValue) -> LuaBool:
    # Equality (==) first compares the type of its operands.
    # If the types are different, then the result is false.
    type_a = type(a)
    if type_a is type(b):
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
    raise RuntimeError()  # TODO.


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
    raise RuntimeError()  # TODO.


def rel_ge(a: LuaValue, b: LuaValue) -> LuaBool:
    # a >= b is translated to b <= a
    return rel_le(b, a)
