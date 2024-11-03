from mehtap.py2lua import lua_function, py2lua
from mehtap.values import LuaString, Variable, LuaNumber, LuaNil
from mehtap.vm import VirtualMachine


def run_chunk(chunk, vm):
    return vm.exec(chunk)


# The following cases were taken from the Lua 5.4 Reference Manual from the
# section "3.4.12 – Lists of expressions, multiple results, and adjustment"
# https://lua.org/manual/5.4/manual.html#3.4.12
#
# Values assumed are as follows:
# f() = 100, 200, 300
# g() = 1000, 2000, 3000
# ... = -100, -200, -300
# x = "marks the spot"
# w = "double u"


@lua_function(wrap_values=True)
def f():
    return 100, 200, 300


@lua_function(wrap_values=True)
def g():
    return 1000, 2000, 3000


def new_vm() -> VirtualMachine:
    vm = VirtualMachine()
    vm.put_nonlocal_ls(LuaString(b"x"), Variable(LuaString(b"marks the spot")))
    vm.put_local_ls(LuaString(b"w"), Variable(LuaString(b"double u")))
    vm.put_nonlocal_ls(LuaString(b"f"), Variable(f))
    vm.put_nonlocal_ls(LuaString(b"g"), Variable(g))
    vm.root_scope.varargs = [py2lua(x) for x in [-100, -200, -300]]
    return vm


def test_extension(capsys):
    # print(x, f())      -- prints x and all results from f().
    run_chunk("print(x, f())", new_vm())
    assert capsys.readouterr().out == "marks the spot\t100\t200\t300\n"


def test_parenthesize_culling(capsys):
    # print(x, (f()))    -- prints x and the first result from f().
    run_chunk("print(x, (f()))", new_vm())
    assert capsys.readouterr().out == "marks the spot\t100\n"


def test_nonlast_culling(capsys):
    # print(f(), x)      -- prints the first result from f() and x.
    run_chunk("print(f(), x)", new_vm())
    assert capsys.readouterr().out == "100\tmarks the spot\n"


def test_addition_culling(capsys):
    # print(1 + f())     -- prints 1 added to the first result from f().
    run_chunk("print(1 + f())", new_vm())
    assert capsys.readouterr().out == "101\n"


def test_vararg_localassignment_adjustment():
    # local x = ...      -- x gets the first vararg argument.
    vm = new_vm()
    run_chunk("local x = ...", vm)
    assert vm.root_scope.get_ls(LuaString(b"x")) == LuaNumber(-100)


def test_vararg_assignment_adjustment_to_small():
    # x,y = ...          -- x gets the first vararg argument,
    #                    -- y gets the second vararg argument.
    vm = new_vm()
    run_chunk("x,y = ...", vm)
    assert vm.get_ls(LuaString(b"x")) == LuaNumber(-100)
    assert vm.get_ls(LuaString(b"y")) == LuaNumber(-200)


def test_vararg_assignment_adjustment_and_culling():
    # x,y,z = w, f()     -- x gets w, y gets the first result from f(),
    #                    -- z gets the second result from f().
    vm = new_vm()
    run_chunk("x,y,z = w, f()", vm)
    assert vm.get_ls(LuaString(b"x")) == LuaString(b"double u")
    assert vm.get_ls(LuaString(b"y")) == LuaNumber(100)
    assert vm.get_ls(LuaString(b"z")) == LuaNumber(200)


def test_vararg_assignment_with_no_adjustment():
    # x,y,z = f()        -- x gets the first result from f(),
    #                    -- y gets the second result from f(),
    #                    -- z gets the third result from f().
    vm = new_vm()
    run_chunk("x,y,z = f()", vm)
    assert vm.get_ls(LuaString(b"x")) == LuaNumber(100)
    assert vm.get_ls(LuaString(b"y")) == LuaNumber(200)
    assert vm.get_ls(LuaString(b"z")) == LuaNumber(300)


def test_vararg_assignment_with_no_adjustment_and_with_culling():
    # x,y,z = f(), g()   -- x gets the first result from f(),
    #                    -- y gets the first result from g(),
    #                    -- z gets the second result from g().
    vm = new_vm()
    run_chunk("x,y,z = f(), g()", vm)
    assert vm.get_ls(LuaString(b"x")) == LuaNumber(100)
    assert vm.get_ls(LuaString(b"y")) == LuaNumber(1000)
    assert vm.get_ls(LuaString(b"z")) == LuaNumber(2000)


def test_vararg_assignment_with_paren_culling_and_adjustment_to_more():
    # x,y,z = (f())      -- x gets the first result from f(), y and z get nil.
    vm = new_vm()
    run_chunk("x,y,z = (f())", vm)
    assert vm.get_ls(LuaString(b"x")) == LuaNumber(100)
    assert vm.get_ls(LuaString(b"y")) == LuaNil
    assert vm.get_ls(LuaString(b"z")) == LuaNil


def test_return_multires():
    # return f()         -- returns all results from f().
    r_val = run_chunk("return f()", new_vm())
    assert r_val == [LuaNumber(100), LuaNumber(200), LuaNumber(300)]


def test_return_vararg():
    # return x, ...      -- returns x and all received vararg arguments.
    r_val = run_chunk("return x, ...", new_vm())
    assert r_val == [
        LuaString(b"marks the spot"),
        LuaNumber(-100),
        LuaNumber(-200),
        LuaNumber(-300),
    ]


def test_return_vararg_extension():
    # return x,y,f()     -- returns x, y, and all results from f().
    vm = new_vm()
    vm.put_local_ls(LuaString(b"y"), Variable(LuaString(b"why oh why")))
    r_val = run_chunk("return x,y,f()", vm)
    assert r_val == [
        LuaString(b"marks the spot"),
        LuaString(b"why oh why"),
        LuaNumber(100),
        LuaNumber(200),
        LuaNumber(300),
    ]


def test_tableconstructor_extension():
    # {f()}              -- creates a list with all results from f().
    t, = run_chunk("return {f()}", new_vm())
    assert t.map.items() == py2lua([100, 200, 300]).map.items()


def test_tableconstructor_vararg():
    # {...}              -- creates a list with all vararg arguments.
    t, = run_chunk("return {...}", new_vm())
    assert t.map.items() == py2lua([-100, -200, -300]).map.items()


def test_tableconstructor_culling():
    # {f(), 5}           -- creates a list with the first result from f() and 5.
    t, = run_chunk("return {f(), 5}", new_vm())
    assert t.map.items() == py2lua([100, 5]).map.items()
