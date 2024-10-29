from ay.__main__ import work_chunk
from ay.vm import VirtualMachine


def test_warn(capsys):
    work_chunk(
        """
        warn("@off")
        print("p1")
        warn("w1")
        warn("@on")
        print("p2")
        warn("w2")
        warn("@off")
        print("p3")
        warn("w3")
    """,
        VirtualMachine(),
    )
    captured = capsys.readouterr()
    assert captured.out == "p1\np2\np3\n"
    assert captured.err.endswith("w2\n")
