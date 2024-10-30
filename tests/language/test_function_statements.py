from ay.py2lua import py2lua
from ay.vm import VirtualMachine


def run_chunk(chunk, vm):
    return vm.exec(chunk)


def test_simple_function():
    vm = VirtualMachine()
    assert run_chunk("""
        function foo()
            return "foo"
        end

        return foo()
    """, vm) == [py2lua("foo")]


def test_nested_function():
    vm = VirtualMachine()
    assert run_chunk("""
        a = {b = {}}
        function a.b.c()
            return "foo"
        end

        return a.b.c()
    """, vm) == [py2lua("foo")]


def test_function_argument():
    vm = VirtualMachine()
    assert run_chunk("""
        function double(x)
            return x * 2
        end

        return double(5)
    """, vm) == [py2lua(10)]


def test_function_vararg_reference_manual(capsys):
    vm = VirtualMachine()
    run_chunk("""
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

    run_chunk("f(3)", vm)
    assert capsys.readouterr().out == "a\t3\nb\tnil\n"
    run_chunk("f(3, 4)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n"
    run_chunk("f(3, 4, 5)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n"
    run_chunk("f(r(), 10)", vm)
    assert capsys.readouterr().out == "a\t1\nb\t10\n"
    run_chunk("f(r())", vm)
    assert capsys.readouterr().out == "a\t1\nb\t2\n"

    run_chunk("g(3)", vm)
    assert capsys.readouterr().out == "a\t3\nb\tnil\n...\n"
    run_chunk("g(3, 4)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n...\n"
    run_chunk("g(3, 4, 5, 8)", vm)
    assert capsys.readouterr().out == "a\t3\nb\t4\n...\t5\t8\n"
    run_chunk("g(5, r())", vm)
    assert capsys.readouterr().out == "a\t5\nb\t1\n...\t2\t3\n"



def test_method():
    vm = VirtualMachine()
    assert run_chunk("""
        human = {}
        human.name = "Emre"
        function human:get_name()
            return self.name
        end

        return human.get_name(human)
    """, vm) == [py2lua("Emre")]
