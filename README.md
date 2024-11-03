# mehtap

Lua 5.4 programming language implementation in Pure Python


[![Latest version on PyPI](https://img.shields.io/pypi/v/mehtap)](https://pypi.org/project/mehtap/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/mehtap)](https://pypi.org/project/mehtap/)

[![Codacy Grade Badge](https://app.codacy.com/project/badge/Grade/c8799d9203354667a97ba39aca2c75f2)](https://app.codacy.com/gh/EmreOzcan/mehtap/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Codacy Coverage Badge](https://app.codacy.com/project/badge/Coverage/c8799d9203354667a97ba39aca2c75f2)](https://app.codacy.com/gh/EmreOzcan/mehtap/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![checks/master](https://img.shields.io/github/check-runs/emreozcan/mehtap/master?logo=github&label=checks%2Fmaster)](https://github.com/emreozcan/mehtap/actions/workflows/test.yml)
[![docs](https://readthedocs.org/projects/mehtap/badge/?version=latest&style=flat)](https://mehtap.readthedocs.io/en/latest/)

## Status

mehtap is in an early alpha stage. Since there is active development,
API changes may happen without any special notice.
Please pin your dependencies using a specific commit hash.

## What does mehtap have?

* Everything in the [Lua 5.4 grammar](https://lua.org/manual/5.4/manual.html#9)
  is supported.
* There are utility functions to convert values
  [from Python to Lua](https://mehtap.readthedocs.io/en/latest/py2lua.html)
  and
  [from Lua to Python](https://mehtap.readthedocs.io/en/latest/lua2py.html).
* Most of the standard library is supported. (100% support is planned.)

    <details>
    <summary>Basic Functions (22/25)</summary>

    - [x] `assert()`
    - [x] `collectgarbage()` &mdash; Does nothing.
    - [x] `dofile()`
    - [x] `error()`
    - [x] `_G`
    - [x] `getmetatable()`
    - [x] `ipairs()`
    - [ ] `load()`
    - [ ] `loadfile()`
    - [ ] `next()`
    - [x] `pairs()`
    - [x] `pcall()`
    - [x] `print()`
    - [x] `rawequal()`
    - [x] `rawget()`
    - [x] `rawlen()`
    - [x] `rawset()`
    - [x] `select()`
    - [x] `setmetatable()`
    - [x] `tonumber()`
    - [x] `tostring()`
    - [x] `type()`
    - [x] `_VERSION`
    - [x] `warn()`
    - [x] `xpcall()`
    </details>

    <details>
    <summary>Input and Output Facilities (17/18)</summary>

    - [x] io.close()
    - [x] io.flush()
    - [x] io.input()
    - [x] io.lines()
    - [x] io.open()
    - [x] io.output()
    - [ ] io.popen()
    - [x] io.read()
    - [x] io.tmpfile()
    - [x] io.type()
    - [x] io.write()
    - [x] file:close()
    - [x] file:flush()
    - [x] file:lines()
    - [x] file:read()
    - [x] file:seek()
    - [x] file:setvbuf() &mdash; Does nothing.
    - [x] file:write()
    </details>

    <details>
    <summary>Operating System Facilities (8/11)</summary>

    - [x] os.clock()
    - [ ] os.date()
    - [ ] os.difftime()
    - [x] os.execute()
    - [x] os.exit()
    - [x] os.getenv()
    - [x] os.remove()
    - [x] os.rename()
    - [x] os.setlocale()
    - [ ] os.time()
    - [x] os.tmpname()
    </details>

## What's the catch?

There are some differences with the specification of the reference manual.
They are:

- garbage collection,
- frame scope.

For the most part,
behaviour differences with the reference implementation are only allowed if the
reference manual does not specify the behaviour.
For example, the exact formatting of error messages is not specified in the
reference manual, so it is allowed to be different.

There are some things that are not implemented yet.
They are, only listing language features, excluding the standard library:

- Taking metavalues and metamethods into consideration when doing operations.

Also, since this is a Python implementation, it is ***SLOW***.

---

Copyright (c) 2024 Emre Özcan
