# ay

Lua 5.4 programming language implementation in Pure Python

[![Codacy Grade Badge](https://app.codacy.com/project/badge/Grade/c8799d9203354667a97ba39aca2c75f2)](https://app.codacy.com/gh/EmreOzcan/ay/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Codacy Coverage Badge](https://app.codacy.com/project/badge/Coverage/c8799d9203354667a97ba39aca2c75f2)](https://app.codacy.com/gh/EmreOzcan/ay/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![checks/master](https://img.shields.io/github/check-runs/emreozcan/ay/master?logo=github&label=checks%2Fmaster)](https://github.com/emreozcan/ay/actions/workflows/test.yml)
[![docs](https://readthedocs.org/projects/ay/badge/?version=latest&style=flat)](https://ay.readthedocs.io/en/latest/)

## What does ay have?

* Everything in the [Lua 5.4 grammar](https://lua.org/manual/5.4/manual.html#9)
  except _label_ and _goto_ statements is supported.
* There are utility functions to convert Python values to Lua values and
  vice-versa.
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

## What does ay not have?

**The grammar, syntax and semantics are exactly the same.**

For the most part,
behaviour differences with the reference implementation are only allowed if the
reference manual does not specify the behaviour.
For example, the exact formatting of error messages is not specified in the
reference manual, so it is allowed to be different.

Currently, the only difference with the specification of the reference manual
if in garbage collection and frame scope.

## Where is the license?

Currently, the project is not open source.
Please contact if you want to use this project for some reason. 
