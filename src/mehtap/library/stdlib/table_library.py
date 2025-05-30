from functools import cmp_to_key

from mehtap.control_structures import LuaError
from mehtap.library.provider_abc import LibraryProvider
from mehtap.operations import length, rel_gt, index, concat, new_index, \
    arith_add, call
from mehtap.py2lua import PyLuaRet, lua_function
from mehtap.values import LuaString, LuaFunction, LuaTable, LuaNumber, \
    type_of_lv, LuaValue, LuaNil, LuaBool, LuaIndexableABC


@lua_function(name="concat")
def lf_table_concat(
    list,
    sep=LuaString(b""),
    i=LuaNumber(1),
    j=None,
    /
) -> PyLuaRet:
    return table_concat(list, sep, i, j)


def table_concat(list, sep, i, j, /) -> PyLuaRet:
    # The default value for sep is the empty string,
    # the default for i is 1,
    # and the default for j is #list.
    if j is None:
        j = length(list)
    # If i is greater than j, returns the empty string.
    if rel_gt(i, j).true:
        return [LuaString(b"")]
    if not isinstance(i, LuaNumber):
        raise LuaError(f"bad argument #3 to 'concat' "
                       f"(number expected, got {type_of_lv(i)})")
    if not isinstance(j, LuaNumber):
        raise LuaError(f"bad argument #4 to 'concat' "
                       f"(number expected, got {type_of_lv(j)})")
    # Given a list where all elements are strings or numbers,
    # returns the string
    # list[i]..sep..list[i+1] ··· sep..list[j].
    cur_str: LuaValue | None = None
    first_trip = True
    for x in range(i.value, j.value + 1):
        value = index(list, LuaNumber(x))
        if not isinstance(value, (LuaString, LuaNumber)):
            t = type_of_lv(value)
            raise LuaError(
                f"invalid value ({t}) at index {x} in table for 'concat'"
            )
        if first_trip:
            first_trip = False
            cur_str = concat(LuaString(b""), value)
            continue
        cur_str = concat(concat(cur_str, sep), value)
    return [cur_str]


@lua_function(name="insert")
def lf_table_insert(list, /, *args):
    if len(args) < 1 or len(args) > 2:
        raise LuaError(f"wrong number of arguments to 'insert'")
    arg1 = args[0]
    arg2 = args[1] if len(args) == 2 else None
    return table_insert(list, arg1, arg2)

lf_table_insert.signature = "(list, [pos,] value)"

def table_insert(list, arg1, arg2) -> PyLuaRet:
    len_list = length(list)
    if arg2 is None:
        # The default value for pos is #list+1,
        # so that a call table.insert(t,x) # inserts x at the end of the list t.
        pos = arith_add(len_list, LuaNumber(1))
        value = arg1
    else:
        pos = arg1
        value = arg2
    if not isinstance(pos, LuaNumber):
        raise LuaError(f"bad argument #2 to 'insert' "
                       f"(number expected, got {type_of_lv(pos)})")
    if pos.value > len_list.value + 1:
        raise LuaError(f"bad argument #2 to 'insert' "
                       f"(position out of bounds, got {pos.value} to a list"
                       f" of length {len_list.value})")
    for idx in range(len_list.value + 1, pos.value, -1):
        # shifting up the elements
        #   list[pos], list[pos+1], ···, list[#list].
        new_index(list, LuaNumber(idx), index(list, LuaNumber(idx - 1)))
    # Inserts element value at position pos in list,
    new_index(list, pos, value)
    return []


@lua_function(name="move")
def lf_table_move(a1, f, e, t, a2=LuaNil, /) -> PyLuaRet:
    return table_move(a1, f, e, t, a2)


def table_move(a1, f, e, t, a2=LuaNil) -> PyLuaRet:
    # The default for a2 is a1.
    if a2 is LuaNil:
        a2 = a1
    # Moves elements from the table a1 to the table a2, performing the
    # equivalent to the following multiple assignment:
    # a2[t],··· = a1[f],···,a1[e].
    # The destination range can overlap with the source range.
    if not isinstance(f, LuaNumber):
        raise LuaError(f"bad argument #2 to 'move' "
                       f"(number expected, got {type_of_lv(f)})")
    if not isinstance(e, LuaNumber):
        raise LuaError(f"bad argument #3 to 'move' "
                       f"(number expected, got {type_of_lv(e)})")
    if not isinstance(t, LuaNumber):
        raise LuaError(f"bad argument #4 to 'move' "
                       f"(number expected, got {type_of_lv(t)})")
    for a2_idx, a1_idx in enumerate(range(f.value, e.value + 1), start=t.value):
        new_index(a2, LuaNumber(a2_idx), index(a1, LuaNumber(a1_idx)))
    # Returns the destination table a2.
    return [a2]


@lua_function(name="pack")
def lf_table_pack(*args) -> PyLuaRet:
    return table_pack(*args)


def table_pack(*args) -> PyLuaRet:
    # Returns a new table with all arguments stored into keys 1, 2, etc.
    new_table = LuaTable()
    for idx, value in enumerate(args, start=1):
        new_table.rawput(LuaNumber(idx), value)
    # and with a field "n" with the total number of arguments.
    new_table.rawput(LuaString(b"n"), LuaNumber(len(args)))
    return [new_table]


@lua_function(name="remove")
def lf_table_remove(list, pos=LuaNil, /) -> PyLuaRet:
    return table_remove(list, pos)


def table_remove(list, pos=LuaNil) -> PyLuaRet:
    # The default value for pos is #list.
    list_length = length(list)
    if pos is LuaNil:
        pos = list_length
    # Removes from list the element at position pos,
    old_value = index(list, pos)
    new_index(list, pos, LuaNil)
    # returning the value of the removed element.
    # When pos is an integer between 1 and #list,
    if (
        isinstance(pos, LuaNumber)
        and isinstance(list_length, LuaNumber)
        and 1 <= pos.value <= list_length.value
    ):
        # it shifts down the elements
        #   list[pos+1], list[pos+2], ···, list[#list]
        # and erases element list[#list];
        for idx in range(pos.value, list_length.value + 1):
            new_index(list, LuaNumber(idx), index(list, LuaNumber(idx + 1)))
        new_index(list, list_length, LuaNil)
    # The index pos can also be 0 when #list is 0, or #list + 1.
    return [old_value]


@lua_function(name="sort")
def lf_table_sort(list, comp=LuaNil, /) -> PyLuaRet:
    return table_sort(list, comp)


def table_sort(list: LuaIndexableABC, comp=LuaNil) -> PyLuaRet:
    # Sorts the list elements in a given order, in-place,
    # from list[1] to list[#list].
    # If comp is given, then it must be a function that receives two list
    # elements and returns true when the first element must come before the
    # second in the final order, so that, after the sort,
    # i <= j implies not comp(list[j],list[i]).
    # If comp is not given, then the standard Lua operator < is used instead.
    #
    # The sort algorithm is not stable: Different elements considered equal by
    # the given order may have their relative positions changed by the sort.

    if comp is LuaNil:
        def comparator(a, b) -> bool:
            return rel_gt(a, b).true
    else:
        def comparator(a, b) -> bool:
            return call(comp, [a, b], None) == [LuaBool(True)]
    list_length = length(list).value
    # Extract elements from list[1] to list[#list]
    elements = [index(list, LuaNumber(idx)) for idx in range(1, list_length + 1)]
    # Use a stable sort (Python's sorted is stable)
    def cmp(a, b):
        # comparator(a, b) should return True if a > b (i.e., a should come after b)
        # so for sorting in ascending order, we reverse the logic
        if comparator(a, b):
            return 1
        elif comparator(b, a):
            return -1
        else:
            return 0
    sorted_elements = sorted(elements, key=cmp_to_key(cmp))
    # Write back sorted elements to list[1] to list[#list]
    for idx, value in enumerate(sorted_elements, start=1):
        new_index(list, LuaNumber(idx), value)
    return []


@lua_function(name="unpack")
def lf_table_unpack(list, i=LuaNil, j=LuaNil, /) -> PyLuaRet:
    return table_unpack(list, i, j)


def table_unpack(list, i=LuaNil, j=LuaNil) -> PyLuaRet:
    # By default, i is 1 and j is #list.
    if i is LuaNil:
        i = LuaNumber(1)
    if not isinstance(i, LuaNumber):
        raise LuaError(f"bad argument #2 to 'unpack' "
                       f"(number expected, got {type_of_lv(i)})")
    if j is LuaNil:
        j = length(list)
    if not isinstance(j, LuaNumber):
        raise LuaError(f"bad argument #3 to 'unpack' "
                       f"(number expected, got {type_of_lv(j)})")
    # Returns the elements from the given list. This function is equivalent to
    #     return list[i], list[i+1], ···, list[j]
    return [
        index(list, LuaNumber(x))
        for x in range(i.value, j.value + 1)
    ]


class TableLibrary(LibraryProvider):
    def provide(self, global_table: LuaTable) -> None:
        table_table = LuaTable()
        global_table.rawput(LuaString(b"table"), table_table)

        for name_of_global, value_of_global in globals().items():
            if name_of_global.startswith("lf_table_"):
                assert isinstance(value_of_global, LuaFunction)
                assert value_of_global.name
                table_table.rawput(
                    LuaString(value_of_global.name.encode("ascii")),
                    value_of_global,
                )
