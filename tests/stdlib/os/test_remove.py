import sys

import pytest

from ay.values import LuaBool, LuaNil, LuaString
from ay.vm import VirtualMachine

vm = VirtualMachine()


def test_remove_file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("hello world")

    path_str = str(file)
    r = vm.exec(f'os.remove({path_str!r})')
    assert r == [LuaBool(True)]

    assert not file.exists()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX only")
def test_remove_empty_dir(tmp_path):
    dir = (tmp_path / "dir")
    dir.mkdir()

    path_str = str(dir)
    r = vm.exec(f'os.remove({path_str!r})')
    assert r == [LuaBool(True)]

    assert not dir.exists()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="POSIX only")
def test_remove_full_dir(tmp_path):
    dir = (tmp_path / "dir")
    dir.mkdir()

    (dir / "file.txt").write_text("hello world")

    path_str = str(dir)
    r = vm.exec(f'os.remove({path_str!r})')
    assert len(r) == 3
    assert r[0] == LuaNil
    assert isinstance(r[1], LuaString)
    assert isinstance(r[2], LuaNil)

    assert not dir.exists()
