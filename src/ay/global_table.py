from __future__ import annotations

from ay.standard_library.os_library import OSLibrary
from ay.values import LuaTable
from ay.standard_library.basic_library import BasicLibrary


def create_global_table() -> LuaTable:
    global_table = LuaTable()

    BasicLibrary().provide(global_table)
    OSLibrary().provide(global_table)

    return global_table
