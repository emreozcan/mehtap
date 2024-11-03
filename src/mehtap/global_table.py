from __future__ import annotations

from mehtap.library.stdlib.io_library import IOLibrary
from mehtap.library.stdlib.os_library import OSLibrary
from mehtap.library.stdlib.basic_library import BasicLibrary
from mehtap.values import LuaTable


def create_global_table() -> LuaTable:
    global_table = LuaTable()

    BasicLibrary().provide(global_table)
    OSLibrary().provide(global_table)
    IOLibrary().provide(global_table)

    return global_table
