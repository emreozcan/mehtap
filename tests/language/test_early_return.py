from mehtap.values import LuaString
from mehtap.vm import VirtualMachine


def test_early_return():
    vm = VirtualMachine()

    vm.exec(
        """
        function test(number)
            if number == 0 then
                return "zero"
            end

            return "other"
        end
        """
    )

    assert vm.eval("test(0)") == [LuaString(b"zero")]
    assert vm.eval("test(1)") == [LuaString(b"other")]
