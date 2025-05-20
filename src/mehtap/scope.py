from __future__ import annotations

from abc import ABC, abstractmethod
from io import SEEK_SET
from os import PathLike
from os.path import basename
from typing import TypeVar, TYPE_CHECKING

import attrs
from lark.exceptions import VisitError

from mehtap.ast_transformer import transformer
from mehtap.control_structures import LuaError
from mehtap.parser import expr_parser, chunk_parser
from mehtap.values import LuaString, Variable, LuaValue

if TYPE_CHECKING:
    from mehtap.vm import VirtualMachine
    from mehtap.py2lua import Py2LuaAccepts

AnyPath = TypeVar("AnyPath", int, str, bytes, PathLike[str], PathLike[bytes])


class ExecutionContext(ABC):
    @abstractmethod
    def eval(self, expr: str) -> list[LuaValue]:
        ...

    @abstractmethod
    def exec(
        self, chunk: str, *, filename: str | None = None
    ) -> list[LuaValue]:
        ...

    @abstractmethod
    def exec_file(self, file_path: AnyPath) -> list[LuaValue]:
        ...

    @abstractmethod
    def get_varargs(self) -> list[LuaValue] | None:
        ...

    @abstractmethod
    def has_ls(self, key: LuaString) -> bool:
        ...

    @abstractmethod
    def get_ls(self, key: LuaString) -> LuaValue:
        ...

    @abstractmethod
    def put_local_ls(self, key: LuaString, variable: Variable) -> None:
        ...

    @abstractmethod
    def put_nonlocal_ls(self, key: LuaString, value: LuaValue) -> None:
        ...

    def put_nonlocal(self, name: str, value: Py2LuaAccepts | Variable | LuaValue) -> None:
        """Put a value in the current scope."""
        if isinstance(value, Variable):
            self.put_nonlocal_ls(LuaString(name.encode("utf-8")), value.value)
        elif isinstance(value, LuaValue):
            self.put_nonlocal_ls(LuaString(name.encode("utf-8")), value)
        else:
            from mehtap.py2lua import py2lua
            self.put_nonlocal_ls(LuaString(name.encode("utf-8")), py2lua(value))

    def put_local(self, name: str, value: Py2LuaAccepts | Variable | LuaValue) -> None:
        """Put a value in the current scope."""
        if isinstance(value, Variable):
            self.put_local_ls(LuaString(name.encode("utf-8")), value)
        elif isinstance(value, LuaValue):
            self.put_local_ls(LuaString(name.encode("utf-8")), Variable(value))
        else:
            from mehtap.py2lua import py2lua
            self.put_local_ls(LuaString(name.encode("utf-8")), Variable(py2lua(value)))

@attrs.define(slots=True, repr=False)
class Scope(ExecutionContext):
    vm: VirtualMachine
    parent: Scope | None
    locals: dict[LuaString, Variable] = attrs.field(factory=dict)
    varargs: list[LuaValue] | None = None
    file: str | None = None
    line: int | None = None

    def push(
        self,
        *,
        file: str | None = None,
        line: int | None = None
    ) -> Scope:
        return Scope(self.vm, self, file=file, line=line)

    def eval(self, expr: str):
        parsed_lua = expr_parser.parse(expr)
        try:
            ast = transformer.transform(parsed_lua, filename="<eval>")
        except VisitError as e:
            le = LuaError(
                LuaString(str(e.orig_exc).encode("utf-8")),
                caused_by=e,
            )
            raise le from e
        try:
            r = ast.evaluate(self)
        except Exception as e:
            le = LuaError(
                LuaString(str(e).encode("utf-8")),
                caused_by=e,
            )
            raise le from e
        if isinstance(r, LuaValue):
            return [r]
        return r

    def exec(self, chunk: str, *, filename: str | None = None) \
            -> list[LuaValue]:
        parsed_lua = chunk_parser.parse(chunk)
        try:
            ast = transformer.transform(
                parsed_lua,
                filename=filename or "<exec>"
            )
        except VisitError as e:
            le = LuaError(
                LuaString(str(e.orig_exc).encode("utf-8")),
                caused_by=e,
            )
            raise le from e
        try:
            r = ast.block.evaluate_without_inner_scope(self)
        except Exception as e:
            le = LuaError(
                LuaString(str(e).encode("utf-8")),
                caused_by=e,
            )
            raise le from e
        return r

    def exec_file(self, file_path: AnyPath) -> list[LuaValue]:
        try:
            f = open(file_path, "r", encoding="utf-8")
        except FileNotFoundError as e:
            raise LuaError(str(e))
        with f:
            if f.read(1) == "#":
                f.readline()
            f.seek(0, SEEK_SET)
            filename_str = basename(file_path)
            try:
                return self.exec(f.read(), filename=filename_str)
            except LuaError as le:
                le.push_tb("main chunk", file=filename_str, line=0)
                raise le
            except Exception as e:
                raise LuaError(
                    LuaString(str(e).encode("utf-8")),
                    caused_by=e,
                )

    def __repr__(self):
        cls_name = self.__class__.__name__
        values = ",".join(f"({k})=({v})" for k, v in self.locals.items())
        if not self.varargs:
            return f"<{cls_name} locals=[{values}]>"
        else:
            varargs = ",".join(str(v) for v in self.varargs)
            return f"<{cls_name} locals=[{values}], varargs=[{varargs}]>"

    def get_varargs(self) -> list[LuaValue] | None:
        if self.varargs is None:
            raise LuaError("cannot use '...' outside a vararg function")
        return self.varargs

    def has_ls(self, key: LuaString) -> bool:
        if key in self.locals:
            return True
        if self.parent is None:
            return False
        return self.parent.has_ls(key)

    def get_ls(self, key: LuaString) -> LuaValue:
        if key in self.locals:
            return self.locals[key].value
        if self.parent is None:
            return self.vm.get_ls(key)
        return self.parent.get_ls(key)

    def put_local_ls(self, key: LuaString, variable: Variable):
        if not isinstance(variable, Variable):
            raise TypeError(f"Expected Variable, got {type(variable)}")

        if key in self.locals and self.locals[key].constant:
            raise LuaError("attempt to change constant variable")
        self.locals[key] = variable

    def put_nonlocal_ls(self, key: LuaString, value: LuaValue):
        if key in self.locals:
            if self.locals[key].constant:
                raise LuaError("attempt to change constant variable")
            self.locals[key] = Variable(value)
            return
        if self.parent is None:
            self.vm.globals.rawput(key, value)
            return
        return self.parent.put_nonlocal_ls(key, value)
