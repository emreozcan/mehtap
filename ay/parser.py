from pathlib import Path

import lark


with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

lua_parser = lark.Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
    debug=True,
)
