from pathlib import Path

import pytest

from ay.vm import VirtualMachine


paths = [
    pytest.param(
        path,
        marks=[
            *(
                (pytest.mark.xfail(
                    reason=path.with_suffix(".xfail").read_text()),)
                if path.with_suffix(".xfail").exists() else ()
            ),
        ],
        id=path.name
    )
    for path in Path(__file__).parent.rglob("*.lua")
]


@pytest.mark.parametrize("path", paths)
def test_program(path: Path, capsys):
    vm = VirtualMachine()

    stdin_path = path.with_suffix(".stdin")
    if stdin_path.exists():
        vm.default_input = stdin_path.open("rb")

    exit_code_path = path.with_suffix(".exit")
    if exit_code_path.exists():
        expected_code = int(exit_code_path.read_text())
        with pytest.raises(SystemExit) as e:
            vm.exec_file(path)
        assert e.value.code == expected_code
    else:
        vm.exec_file(path)

    outerr = capsys.readouterr()
    stdout_path = path.with_suffix(".stdout")
    if stdout_path.exists():
        assert outerr.out == stdout_path.read_text()
    else:
        assert outerr.out == ""
    stderr_path = path.with_suffix(".stderr")
    if stderr_path.exists():
        assert outerr.err == stderr_path.read_text()
    else:
        assert outerr.err == ""
