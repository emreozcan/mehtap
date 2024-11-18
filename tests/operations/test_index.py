from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_index_value():
    vm = VirtualMachine()
    assert vm.exec(
        """
            local tab1 = {foo = 'bar'}
            local tab2 = setmetatable({}, {__index = tab1})

            return tab2.foo
        """
    ) == [LuaString(b"bar")]


def test_index_function(capsys):
    vm = VirtualMachine()
    vm.exec(
        """
            local tab = setmetatable({count = 0}, {
                __index = function(self, _k)
                    self.count = self.count + 1
                    return self.count
                end
            })

            print(tab.index) --> 1
            print(tab.indexagain) --> 2
            print(tab.asdfasdf) --> 3
            print(tab[1234]) --> 4
        """
    )
    assert capsys.readouterr().out == "1\n2\n3\n4\n"
