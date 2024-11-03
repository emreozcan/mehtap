import pytest

from ay.vm import VirtualMachine

vm = VirtualMachine()


def test_exit_true():
    with pytest.raises(SystemExit) as system_exit:
        vm.exec("os.exit(42, true)")
    assert system_exit.type == SystemExit
    assert system_exit.value.code == 42


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

