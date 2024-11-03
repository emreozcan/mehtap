from mehtap.vm import VirtualMachine


def test_flush_function(tmp_path):
    vm = VirtualMachine()
    write_handle = open(tmp_path / "test.txt", "wb")
    read_handle = open(tmp_path / "test.txt", "rb")
    vm.default_output = write_handle
    write_handle.write(b"abcde")
    assert read_handle.read() == b""
    vm.exec("io.flush()")
    assert read_handle.read() == b"abcde"
