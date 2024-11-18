from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_concat_strings():
    vm = VirtualMachine()
    assert vm.exec(
        """
            a = "hello"
            b = "world"
            return a .. b
        """
    ) == [LuaString(b"helloworld")]


def test_concat_numbers():
    vm = VirtualMachine()
    assert vm.exec(
        """
            a = 1
            b = 2
            return a .. b
        """
    ) == [LuaString(b"12")]


def test_concat_string_and_number():
    vm = VirtualMachine()
    assert vm.exec(
        """
            a = "hello"
            b = 2
            return a .. b
        """
    ) == [LuaString(b"hello2")]


def test_concat_metamethod(capsys):
    vm = VirtualMachine()
    vm.exec(
        """
            table_1 = {v=1}
            table_2 = {v=2}

            function cc(a, b)
                return a.v .. b.v
            end

            setmetatable(table_1, {__concat = cc})

            print(table_1 .. table_2)
            print(table_2 .. table_1)

            setmetatable(table_1, nil)
            setmetatable(table_2, {__concat = cc})

            print(table_1 .. table_2)
            print(table_2 .. table_1)
        """
    )
    assert capsys.readouterr().out == "12\n21\n12\n21\n"
