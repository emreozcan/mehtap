from ay.__main__ import work_chunk
from ay.util.py_lua_function import py_to_lua
from ay.vm import VirtualMachine


def test_simple_function():
    vm = VirtualMachine()
    assert work_chunk("""
        function foo()
            return "foo"
        end

        return foo()
    """, vm) == [py_to_lua("foo")]


def test_nested_function():
    vm = VirtualMachine()
    assert work_chunk("""
        a = {b = {}}
        function a.b.c()
            return "foo"
        end

        return a.b.c()
    """, vm) == [py_to_lua("foo")]


def test_function_argument():
    vm = VirtualMachine()
    assert work_chunk("""
        function double(x)
            return x * 2
        end

        return double(5)
    """, vm) == [py_to_lua(10)]


def test_function_vararg_reference_manual(capsys):
    vm = VirtualMachine()
    work_chunk("""
        function f(a, b)
            print("a", a)
            print("b", b)
        end
        function g(a, b, ...)
            print("a", a)
            print("b", b)
            print("...", ...)
        end
        function r() return 1,2,3 end
    """, vm)
    # Taken from the Lua 5.4 Reference Manual 3.4.11 - Function Definitions.
    # https://lua.org/manual/5.4/manual.html#3.4.11
    #
    # CALL             PARAMETERS
    #
    # f(3)             a=3, b=nil
    # f(3, 4)          a=3, b=4
    # f(3, 4, 5)       a=3, b=4
    # f(r(), 10)       a=1, b=10
    # f(r())           a=1, b=2
    #
    # g(3)             a=3, b=nil, ... -->  (nothing)
    # g(3, 4)          a=3, b=4,   ... -->  (nothing)
    # g(3, 4, 5, 8)    a=3, b=4,   ... -->  5  8
    # g(5, r())        a=5, b=1,   ... -->  2  3

    work_chunk("f(3)", vm)
    assert capsys.readouterr().out == "a\t3\nb\tnil\n"
    work_chunk("f(3, 4)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n"
    work_chunk("f(3, 4, 5)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n"
    work_chunk("f(r(), 10)", vm)
    assert capsys.readouterr().out == "a\t1\nb\t10\n"
    work_chunk("f(r())", vm)
    assert capsys.readouterr().out == "a\t1\nb\t2\n"

    work_chunk("g(3)", vm)
    assert capsys.readouterr().out == "a\t3\nb\tnil\n...\n"
    work_chunk("g(3, 4)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n...\n"
    work_chunk("g(3, 4, 5, 8)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n...\t5\t8\n"
    work_chunk("g(5, r())", vm)
    assert capsys.readouterr().out == "a\t5\nb\t1\n...\t2\t3\n"



def test_method():
    vm = VirtualMachine()
    assert work_chunk("""
        human = {}
        human.name = "Emre"
        function human:get_name()
            return self.name
        end

        return human.get_name(human)
    """, vm) == [py_to_lua("Emre")]
