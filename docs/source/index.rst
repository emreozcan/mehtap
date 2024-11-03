ay Documentation
================

Lua 5.4 programming language implementation in Pure Python

Status
------
ay is in an early alpha stage. Since there is active development,
API changes may happen without any special notice.
Please pin your dependencies using a specific commit hash.

What does ay have?
------------------

* Everything in the `Lua 5.4 grammar`_ is supported.
* There are utility functions to convert values
  :doc:`from Python to Lua <py2lua>` and
  :doc:`from Lua to Python <lua2py>`.
* Most of the standard library is supported. (100% support is planned.)
  See `this issue`_ for progress.

.. _Lua 5.4 grammar: https://lua.org/manual/5.4/manual.html#9
.. _this issue: https://github.com/emreozcan/ay/issues/11

What's the catch?
-----------------

There are some differences with the specification of the reference manual.
They are:

* garbage collection,
* frame scope.

For the most part,
behaviour differences with the reference implementation are only allowed if the
reference manual does not specify the behaviour.
For example, the exact formatting of error messages is not specified in the
reference manual, so it is allowed to be different.

There are some things that are not implemented yet.
They are, only listing language features, excluding the standard library:

* Taking metavalues and metamethods into consideration when doing operations.

Also, since this is a Python implementation, it is **SLOW**.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   values
   py2lua
   lua2py
