from mehtap.vm import VirtualMachine


def test_write_function(tmp_path):
    vm = VirtualMachine()
    test_file_path = tmp_path / "test.txt"
    vm.default_output = open(test_file_path, "wb")
    vm.exec("io.write('abc', 1, 'def')")
    vm.exec("io.close()")
    assert test_file_path.read_bytes() == b"abc1def"
