import pytest

from ay.vm import VirtualMachine

vm = VirtualMachine()


def test_exit_42():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit(42, true)")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 42


def test_exit_bool_true():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit(true, true)")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 0


def test_exit_bool_false():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit(false, true)")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 1


@pytest.mark.skip(reason="No way to test this")
def test_exit_false():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit(42, false)")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 42


@pytest.mark.skip(reason="No way to test this")
def test_exit_default_type():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit(42)")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 42


@pytest.mark.skip(reason="No way to test this")
def test_exit_all_defaults():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit()")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 0

