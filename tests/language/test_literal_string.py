from mehtap.operations import str_to_lua_string
from mehtap.vm import VirtualMachine

vm = VirtualMachine()


def parse(expr):
    r = vm.eval(expr)
    assert len(r) == 1
    return r[0]


def test_alo():
    t1 = parse(r"""'alo\n123"'""")
    t2 = parse(r'''"alo\n123\""''')
    t3 = parse(r"""'\97lo\10\04923"'""")
    t4 = parse(
        r"""[[alo
123"]]"""
    )
    t5 = parse(
        r"""[==[
alo
123"]==]"""
    )

    ref = str_to_lua_string('alo\n123"')

    assert t1 == ref
    assert t2 == ref
    assert t3 == ref
    assert t4 == ref
    assert t5 == ref
