from mehtap.values import LuaNumber
from mehtap.vm import VirtualMachine


def test_upvalue_read():
    vm = VirtualMachine()
    assert vm.exec(
        """
        function main()
            local x = 42
            function inner()
                return x
            end
            return inner()
        end

        return main()
    """
    ) == [LuaNumber(42)]
