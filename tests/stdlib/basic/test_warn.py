from mehtap.vm import VirtualMachine


def test_warn(capsys):
    VirtualMachine().exec(
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
    """)
    captured = capsys.readouterr()
    assert captured.out == "p1\np2\np3\n"
    assert captured.err.endswith("w2\n")
