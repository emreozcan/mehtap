from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Literal

import attrs

from util.node import Node
from vm import VirtualMachine


@attrs.define(slots=True)
class Terminal(Node):
    text: str


@attrs.define(slots=True)
class NonTerminal(Node, ABC):
    pass


@attrs.define(slots=True)
class AbstractSyntaxTree:
    root: Chunk


@attrs.define(slots=True)
class Chunk(NonTerminal):
    block: Block


@attrs.define(slots=True)
class Block(NonTerminal):
    statements: Sequence[Statement]
    return_statement: ReturnStatement | None = None


@attrs.define(slots=True)
class Statement(NonTerminal, ABC):
    # todo: @abstractmethod
    def execute(self, vm: VirtualMachine) -> None:
        pass


@attrs.define(slots=True)
class Expression(NonTerminal, ABC):
    pass


@attrs.define(slots=True)
class Numeral(Expression, ABC):
    pass


@attrs.define(slots=True)
class NumeralHex(Numeral):
    digits: Terminal
    fract_digits: Terminal | None = None
    p_sign: Terminal | None = None
    p_digits: Terminal | None = None


@attrs.define(slots=True)
class NumeralDec(Numeral):
    digits: Terminal
    fract_digits: Terminal | None = None
    e_sign: Terminal | None = None
    e_digits: Terminal | None = None


@attrs.define(slots=True)
class LiteralString(Expression):
    text: Terminal


@attrs.define(slots=True)
class Name(NonTerminal):
    name: Terminal


@attrs.define(slots=True)
class Variable(Expression):
    pass


@attrs.define(slots=True)
class VarName(Variable):
    name: Name


@attrs.define(slots=True)
class VarIndex(Variable):
    base: Expression
    index: Expression


@attrs.define(slots=True)
class TableConstructor(Expression):
    fields: Sequence[Field]


@attrs.define(slots=True)
class Field(NonTerminal, ABC):
    value: Expression


@attrs.define(slots=True)
class FieldWithKey(Field):
    key: Expression | Name | None = None


@attrs.define(slots=True)
class FieldCounterKey(Field):
    pass


@attrs.define(slots=True)
class FuncBody(NonTerminal):
    params: Sequence[Name]
    body: Block
    vararg: bool = False


@attrs.define(slots=True)
class FuncDef(Expression):
    body: FuncBody


@attrs.define(slots=True)
class FuncCallRegular(Expression, Statement):
    name: Expression
    args: Sequence[Expression]


@attrs.define(slots=True)
class FuncCallMethod(Expression, Statement):
    object: Expression
    method: Name
    args: Sequence[Expression]


@attrs.define(slots=True)
class Unary(Expression):
    op: Terminal
    exp: Expression


@attrs.define(slots=True)
class BinOp(Expression, ABC):
    lhs: Expression
    rhs: Expression


@attrs.define(slots=True)
class SumOp(BinOp):
    op: Literal["+", "-"]


@attrs.define(slots=True)
class ReturnStatement(Statement):
    values: Sequence[Expression]


@attrs.define(slots=True)
class EmptyStatement(Statement):
    pass


@attrs.define(slots=True)
class Assignment(Statement):
    names: Sequence[Expression]
    exprs: Sequence[Expression]


@attrs.define(slots=True)
class Label(Statement):
    name: Name


@attrs.define(slots=True)
class Break(Statement):
    pass


@attrs.define(slots=True)
class Goto(Statement):
    name: Name


@attrs.define(slots=True)
class Do(Statement):
    block: Block


@attrs.define(slots=True)
class While(Statement):
    condition: Expression
    block: Block


@attrs.define(slots=True)
class Repeat(Statement):
    block: Block
    condition: Expression


@attrs.define(slots=True)
class If(Statement):
    blocks: Sequence[tuple[Expression, Block]]
    else_block: Block | None = None


@attrs.define(slots=True)
class For(Statement):
    name: Name
    start: Expression
    stop: Expression
    step: Expression | None
    block: Block


@attrs.define(slots=True)
class ForIn(Statement):
    names: Sequence[Name]
    exprs: Sequence[Expression]
    block: Block


@attrs.define(slots=True)
class Function(Statement):
    name: Name
    body: FuncBody


@attrs.define(slots=True)
class LocalFunction(Statement):
    name: Name
    body: FuncBody


@attrs.define(slots=True)
class AttributeName(NonTerminal):
    name: Name
    attrib: Name | None = None


@attrs.define(slots=True)
class LocalAssignment(Statement):
    names: Sequence[AttributeName]
    exprs: Sequence[Expression]

