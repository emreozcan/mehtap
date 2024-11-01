ay Documentation
================

Lua 5.4 programming language implementation in Pure Python

What is supported?
------------------

* All of the `Lua 5.4 grammar`_ is supported.
* Parts of the standard library are supported, 100% support is planned.
  See `this issue`_ for progress.

.. _Lua 5.4 grammar: https://lua.org/manual/5.4/manual.html#9
.. _this issue: https://github.com/emreozcan/ay/issues/11

Caveats
-------

The grammar, syntax and semantics are exactly the same.

For the most part,
behaviour differences with the reference implementation are only allowed if the
reference manual does not specify the behaviour.
For example, the exact formatting of error messages is not specified in the
reference manual, so it is allowed to be different.

Currently, the only difference with the specification of the reference manual
if in garbage collection and frame scope.

Where is the license?
---------------------

Currently, the project is not open source.
Please contact if you want to use this project for some reason.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   values
   py2lua
   lua2py
