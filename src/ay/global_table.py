from __future__ import annotations

from ay.library.stdlib.os_library import OSLibrary
from ay.library.stdlib.basic_library import BasicLibrary
from ay.values import LuaTable


def create_global_table() -> LuaTable:
    global_table = LuaTable()

    BasicLibrary().provide(global_table)
    OSLibrary().provide(global_table)

    return global_table
