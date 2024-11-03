from pathlib import Path

import lark


with open(Path(__file__).parent / "lua.lark", "r", encoding="utf-8") as f:
    lua_grammar = f.read()

chunk_parser = lark.Lark(
    lua_grammar,
    start="chunk",
    parser="earley",
    propagate_positions=True,
    debug=True,
)

expr_parser = lark.Lark(
    lua_grammar,
    start="exp",
    parser="earley",
    propagate_positions=True,
    debug=True,
)

numeral_parser = lark.Lark(
    lua_grammar,
    start="numeral",
    parser="earley",
    propagate_positions=True,
    debug=True,
)
