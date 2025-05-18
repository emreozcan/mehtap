
def test_all_tokens_have_names():
    from mehtap.parser import repl_parser

    assert not [
        terminal for terminal in repl_parser.terminals
        if terminal.name.startswith("__ANON")
    ]
