from ay.__main__ import work_chunk
from ay.vm import VirtualMachine


def test_block_scope_from_reference_manual(capsys):
    # From the Lua 5.4 reference manual 3.5 – Visibility Rules
    # https://lua.org/manual/5.4/manual.html#3.5
    vm = VirtualMachine()
    work_chunk("""
        x = 10                -- global variable
        do                    -- new block
            local x = x       -- new 'x', with value 10
            print(x)          --> 10
            x = x+1
            do                -- another block
                local x = x+1 -- another 'x'
                print(x)      --> 12
            end
            print(x)          --> 11
        end
        print(x)              --> 10  (the global one)
    """, vm)
    assert capsys.readouterr().out == "10\n12\n11\n10\n"
