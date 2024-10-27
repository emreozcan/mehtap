from __future__ import annotations

from ay.values import LuaTable
from ay.standard_library.basic import BasicLibrary


def create_global_table() -> LuaTable:
    global_table = LuaTable()

    BasicLibrary().provide(global_table)

    return global_table
