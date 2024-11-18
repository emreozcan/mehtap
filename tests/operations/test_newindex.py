from mehtap.vm import VirtualMachine


def test_newindex(capsys):
    vm = VirtualMachine()
    vm.exec(
        """
            t = setmetatable({}, {
                __newindex = function(t, key, value)
                    if type(value) == 'number' then
                        rawset(t, key, value * value)
                    else
                        rawset(t, key, value)
                    end
                end
            })

            t.foo = 'foo'
            t.bar = 4
            t.la = 10
            print(t.foo) --> 'foo'
            print(t.bar) --> 16
            print(t.la) --> 100
        """
    )

    assert capsys.readouterr().out == "foo\n16\n100\n"
