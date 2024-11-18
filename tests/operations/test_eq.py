from mehtap.values import LuaBool
from mehtap.vm import VirtualMachine


def test_eq_different_types():
    vm = VirtualMachine()
    assert vm.exec("return 1 == '1'") == [LuaBool(False)]


def test_eq_string():
    vm = VirtualMachine()
    assert vm.exec("return '1' == '1'") == [LuaBool(True)]
    assert vm.exec("return '1' == '2'") == [LuaBool(False)]


def test_eq_number():
    vm = VirtualMachine()
    assert vm.exec("return 1 == 1") == [LuaBool(True)]
    assert vm.exec("return 1 == 2") == [LuaBool(False)]
    assert vm.exec("return 1 == 1.0") == [LuaBool(True)]
    assert vm.exec("return 1 == 1.1") == [LuaBool(False)]
    assert vm.exec("return 0.0 == 0") == [LuaBool(True)]
    assert vm.exec("return -0.0 == 0") == [LuaBool(True)]

    # nan isn't equal to itself
    assert vm.exec("return 0/0 == 0/0") == [LuaBool(False)]


def test_eq_boolean():
    vm = VirtualMachine()
    assert vm.exec("return true == true") == [LuaBool(True)]
    assert vm.exec("return false == false") == [LuaBool(True)]
    assert vm.exec("return true == false") == [LuaBool(False)]


def test_eq_table_identity():
    vm = VirtualMachine()
    assert vm.exec("return {} == {}") == [LuaBool(False)]
    assert vm.exec("return {1} == {1}") == [LuaBool(False)]
    assert vm.exec(
        """
            x = {}
            return x == x
        """
    ) == [LuaBool(True)]


def test_eq_metamethod():
    vm = VirtualMachine()
    vm.exec(
        """
            point_1 = {x = 15, y = 30}
            point_2 = {x = 15, y = 30}

            function compare_points(p1, p2)
                return p1.x == p2.x and p1.y == p2.y
            end

            mt = {__eq = compare_points}
        """
    )
    assert vm.eval("point_1 == point_2") == [LuaBool(False)]
    vm.exec("setmetatable(point_1, mt)")
    assert vm.eval("point_1 == point_2") == [LuaBool(True)]
    assert vm.eval("point_1 == {x = 15, y = 30}") == [LuaBool(True)]
    vm.exec("setmetatable(point_1, nil) setmetatable(point_2, mt)")
    assert vm.eval("point_1 == point_2") == [LuaBool(True)]
    assert vm.eval("point_1 == {x = 15, y = 30}") == [LuaBool(False)]
    assert vm.eval("point_2 == {x = 15, y = 30}") == [LuaBool(True)]
