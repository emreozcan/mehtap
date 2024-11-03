from ay.values import LuaBool, LuaString, LuaNil, LuaNumber
from ay.vm import VirtualMachine

vm = VirtualMachine()


def test_rename_file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("hello world")

    new_file = tmp_path / "new_file.txt"

    path_str = str(file)
    new_path_str = str(new_file)
    r = vm.exec(f'os.rename({path_str!r}, {new_path_str!r})')
    assert r == [LuaBool(True)]

    assert not file.exists()
    assert new_file.exists()

    assert new_file.read_text() == "hello world"


def test_rename_file_fail(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("hello world")

    path_str = str(file)
    r = vm.exec(f'os.rename({path_str!r}, "\n.txt")')
    assert len(r) == 3
    assert r[0] == LuaNil
    assert isinstance(r[1], LuaString)
    assert isinstance(r[2], LuaNumber)
