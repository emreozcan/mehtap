# ay

Lua 5.4 programming language implementation in Pure Python

[![Codacy Grade Badge](https://app.codacy.com/project/badge/Grade/c8799d9203354667a97ba39aca2c75f2)](https://app.codacy.com/gh/EmreOzcan/ay/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Codacy Coverage Badge](https://app.codacy.com/project/badge/Coverage/c8799d9203354667a97ba39aca2c75f2)](https://app.codacy.com/gh/EmreOzcan/ay/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)
[![checks/master](https://img.shields.io/github/check-runs/emreozcan/ay/master?logo=github&label=checks%2Fmaster)](https://github.com/emreozcan/ay/actions/workflows/test.yml)
[![docs](https://readthedocs.org/projects/ay/badge/?version=latest&style=flat)](https://ay.readthedocs.io/en/latest/)

## What is supported?

* All of the [Lua 5.4 grammar](https://lua.org/manual/5.4/manual.html#9) is
  supported.
* Parts of the standard library are supported, 100% support is planned.
  See [this issue](https://github.com/emreozcan/ay/issues/11) for progress.

## Caveats

The grammar, syntax and semantics are exactly the same.

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
