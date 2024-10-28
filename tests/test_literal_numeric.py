from ay.__main__ import work_expr
from ay.vm import VirtualMachine
from ay.values import LuaNumber


vm = VirtualMachine()


def parse(expr):
    return work_expr(expr, vm)


def test_whole_number_decimal():
    assert parse("123") == LuaNumber(123)
    assert parse("0") == LuaNumber(0)
    assert parse("1") == LuaNumber(1)
    assert parse("123456789") == LuaNumber(123456789)


def test_whole_number_hexadecimal():
    assert parse("0x0") == LuaNumber(0x0)
    assert parse("0x1") == LuaNumber(0x1)
    assert parse("0x123456789") == LuaNumber(0x123456789)


def test_fractional_decimal():
    assert parse("0.0") == LuaNumber(0.0)
    assert parse("0.1") == LuaNumber(0.1)
    assert parse("1.0") == LuaNumber(1.0)
    assert parse("123.456") == LuaNumber(123.456)


def test_fractional_hexadecimal():
    assert parse("0x0.0") == LuaNumber(0x0)
    assert parse("0x0.1") == LuaNumber(1 / 16)
    assert parse("0x1.0") == LuaNumber(0x1)
    assert parse("0x123.456") == LuaNumber(0x123456 / 16**3)


def test_exponent_decimal():
    assert parse("1e0") == LuaNumber(1)
    assert parse("1e1") == LuaNumber(10)
    assert parse("1e2") == LuaNumber(100)
    assert parse("1e-1") == LuaNumber(0.1)
    assert parse("1e-2") == LuaNumber(0.01)
    assert parse("1e-3") == LuaNumber(0.001)
    assert parse("123e0") == LuaNumber(123)
    assert parse("123e1") == LuaNumber(1230)
    assert parse("123e2") == LuaNumber(12300)
    assert parse("123e-1") == LuaNumber(12.3)
    assert parse("123e-2") == LuaNumber(1.23)
    assert parse("123e-3") == LuaNumber(0.123)


def test_exponent_hexadecimal():
    assert parse("0x1p0") == LuaNumber(1)
    assert parse("0x1p1") == LuaNumber(2)
    assert parse("0x1p2") == LuaNumber(4)
    assert parse("0x1p-1") == LuaNumber(0.5)
    assert parse("0x1p-2") == LuaNumber(0.25)
    assert parse("0x1p-3") == LuaNumber(0.125)

    assert parse("0x1.fp10") == LuaNumber(1984)

    assert parse("0x123p0") == LuaNumber(0x123 * 2**0)
    assert parse("0x123p1") == LuaNumber(0x123 * 2**1)
    assert parse("0x123p2") == LuaNumber(0x123 * 2**2)
    assert parse("0x123p-1") == LuaNumber(0x123 * 2**-1)
    assert parse("0x123p-2") == LuaNumber(0x123 * 2**-2)
    assert parse("0x123p-3") == LuaNumber(0x123 * 2**-3)


def test_fractional_exponent_decimal():
    assert parse("1.5e0") == LuaNumber(1.5)
    assert parse("1.5e1") == LuaNumber(15)
    assert parse("1.5e2") == LuaNumber(150)
    assert parse("1.5e-1") == LuaNumber(0.15)
    assert parse("1.5e-2") == LuaNumber(0.015)
    assert parse("1.5e-3") == LuaNumber(0.0015)


def test_fractional_exponent_hexadecimal():
    assert parse("0x1.5p0") == LuaNumber(0x15 / 16 * 2**0)
    assert parse("0x1.5p1") == LuaNumber(0x15 / 16 * 2**1)
    assert parse("0x1.5p2") == LuaNumber(0x15 / 16 * 2**2)
    assert parse("0x1.5p-1") == LuaNumber(0x15 / 16 * 2**-1)
    assert parse("0x1.5p-2") == LuaNumber(0x15 / 16 * 2**-2)
    assert parse("0x1.5p-3") == LuaNumber(0x15 / 16 * 2**-3)
