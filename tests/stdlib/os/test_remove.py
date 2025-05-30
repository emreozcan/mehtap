import os

import pytest

from mehtap.values import LuaBool, LuaNil, LuaString, LuaNumber
from mehtap.vm import VirtualMachine

vm = VirtualMachine()


def test_remove_file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("hello world")

    path_str = str(file)
    r = vm.eval(f'os.remove({path_str!r})')
    assert r == [LuaBool(True)]

    assert not file.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX only")
def test_remove_empty_dir(tmp_path):
    dir = (tmp_path / "dir")
    dir.mkdir()

    path_str = str(dir)
    r = vm.eval(f'os.remove({path_str!r})')
    assert r == [LuaBool(True)]

    assert not dir.exists()


def test_remove_full_dir(tmp_path):
    dir = (tmp_path / "dir")
    dir.mkdir()

    (dir / "file.txt").write_text("hello world")

    path_str = str(dir)
    r = vm.eval(f'os.remove({path_str!r})')
    assert len(r) == 3
    assert r[0] == LuaNil
    assert isinstance(r[1], LuaString)
    assert isinstance(r[2], LuaNumber)

    assert dir.exists()
