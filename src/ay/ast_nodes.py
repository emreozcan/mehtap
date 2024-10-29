from __future__ import annotations

import io
import string
from abc import ABC, abstractmethod
from collections.abc import Sequence, Iterable
from typing import Literal, TYPE_CHECKING

import attrs

import ay.values as ay_values
from ay.control_structures import BreakException, GotoException, ReturnException
from ay.values import (
    LuaNumber,
    LuaValue,
    LuaNumberType,
    LuaString,
    MAX_INT64,
    LuaTable,
    LuaFunction,
    StackFrame,
)
from ay.operations import (
    int_overflow_wrap_around,
    str_to_lua_string,
    adjust,
    coerce_to_bool,
)
import ay.operations as ay_operations

if TYPE_CHECKING:
    from vm import VirtualMachine


def flatten(v: Iterable[LuaValue | list[LuaValue]]) -> list[LuaValue]:
    result = []
    for elem in v:
        if isinstance(elem, list):
            result.extend(flatten(elem))
        else:
            result.append(elem)
    return result


@attrs.define(slots=True)
class Node(ABC):
    def as_dict(self):
        return attrs.asdict(self)


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
class Statement(NonTerminal, ABC):
    @abstractmethod
    def execute(self, vm: VirtualMachine) -> None:
        pass


@attrs.define(slots=True)
class Expression(NonTerminal, ABC):
    @abstractmethod
    def evaluate(self, vm: VirtualMachine) -> LuaValue | Sequence[LuaValue]:
        pass


@attrs.define(slots=True)
class Block(Statement, Expression):
    def evaluate(self, vm: VirtualMachine) -> Sequence[LuaValue]:
        for stmt in self.statements:
            stmt.execute(vm)
        return (
            flatten(expr.evaluate(vm) for expr in self.return_statement.values)
            if self.return_statement
            else []
        )

    def execute(self, vm: VirtualMachine) -> None:
        for stmt in self.statements:
            stmt.execute(vm)

    statements: Sequence[Statement]
    return_statement: ReturnStatement | None = None


@attrs.define(slots=True)
class Numeral(Expression, ABC):
    pass


@attrs.define(slots=True)
class NumeralHex(Numeral):
    digits: Terminal
    fract_digits: Terminal | None = None
    p_sign: Terminal | None = None
    p_digits: Terminal | None = None

    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        if self.fract_digits or self.p_digits:
            if not self.p_sign:
                self.p_sign = Terminal("+")
            if not self.p_digits:
                self.p_digits = Terminal("0")
            if not self.fract_digits:
                self.fract_digits = Terminal("")
            whole_val = int(self.digits.text + self.fract_digits.text, 16)
            frac_val = whole_val / 16 ** len(self.fract_digits.text)
            exp_val = 2 ** int(self.p_sign.text + self.p_digits.text)
            return LuaNumber(frac_val * exp_val, LuaNumberType.FLOAT)
        # if the value overflows, it wraps around to fit into a valid integer.
        return int_overflow_wrap_around(int(self.digits.text, 16))


@attrs.define(slots=True)
class NumeralDec(Numeral):
    digits: Terminal
    fract_digits: Terminal | None = None
    e_sign: Terminal | None = None
    e_digits: Terminal | None = None

    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        if self.fract_digits or self.e_digits:
            if not self.e_sign:
                self.e_sign = Terminal("+")
            if not self.e_digits:
                self.e_digits = Terminal("0")
            if not self.fract_digits:
                self.fract_digits = Terminal("0")
            return LuaNumber(
                float(
                    self.digits.text
                    + "."
                    + self.fract_digits.text
                    + "e"
                    + self.e_sign.text
                    + self.e_digits.text
                ),
                LuaNumberType.FLOAT,
            )
        whole_val = int(self.digits.text)
        if whole_val > MAX_INT64:
            return LuaNumber(float(self.digits.text), LuaNumberType.FLOAT)
        return LuaNumber(whole_val, LuaNumberType.INTEGER)


@attrs.define(slots=True)
class LiteralString(Expression):
    text: Terminal

    def _simple_string(self) -> LuaString:
        bytes_io = io.BytesIO()
        currently_skipping_whitespace = False
        currently_reading_decimal = False
        currently_read_decimal: str = ""
        str_iter = iter(self.text.text[1:-1])
        for character in str_iter:
            if currently_skipping_whitespace:
                if character in string.whitespace:
                    continue
                currently_skipping_whitespace = False
            if currently_reading_decimal:
                if (
                    character in string.digits
                    and len(currently_read_decimal) < 3
                ):
                    currently_read_decimal += character
                    continue
                bytes_io.write(bytes([int(currently_read_decimal)]))
                currently_reading_decimal = False
                currently_read_decimal = ""
            if character == "\\":
                try:
                    escape_char = next(str_iter)
                except StopIteration:
                    bytes_io.write(b"\\")
                    break
                if escape_char == "a":
                    bytes_io.write(b"\a")
                elif escape_char == "b":
                    bytes_io.write(b"\b")
                elif escape_char == "f":
                    bytes_io.write(b"\f")
                elif escape_char == "n":
                    bytes_io.write(b"\n")
                elif escape_char == "r":
                    bytes_io.write(b"\r")
                elif escape_char == "t":
                    bytes_io.write(b"\t")
                elif escape_char == "v":
                    bytes_io.write(b"\v")
                elif escape_char == "\\":
                    bytes_io.write(b"\\")
                elif escape_char == '"':
                    bytes_io.write(b'"')
                elif escape_char == "'":
                    bytes_io.write(b"'")
                elif escape_char == "\n":
                    bytes_io.write(b"\n")
                elif escape_char == "z":
                    currently_skipping_whitespace = True
                    continue
                elif escape_char == "x":
                    try:
                        hex_digit_1 = next(str_iter)
                        hex_digit_2 = next(str_iter)
                    except StopIteration:
                        raise NotImplementedError()
                    bytes_io.write(bytes.fromhex(hex_digit_1 + hex_digit_2))
                elif escape_char in string.digits:
                    currently_reading_decimal = True
                    currently_read_decimal = escape_char
                    continue
                elif escape_char == "u":
                    left_brace = next(str_iter)
                    if left_brace != "{":
                        raise NotImplementedError()
                    hex_digits = []
                    while True:
                        hex_digit = next(str_iter)
                        if hex_digit == "}":
                            break
                        hex_digits.append(hex_digit)
                    hex_str = "".join(hex_digit)
                    bytes_io.write(chr(int(hex_str, 16)).encode("utf-8"))
                else:
                    raise NotImplementedError()
                continue
            bytes_io.write(character.encode("utf-8"))
        bytes_io.seek(0)
        return LuaString(bytes_io.read())

    def _long_bracket(self) -> LuaString:
        # Literals in this bracketed form can run for several lines,
        # do not interpret any escape sequences,
        # and ignore long brackets of any other level.
        level = 1
        while self.text.text[level] == "=":
            level += 1
        level -= 1
        # [====[...
        #   0123456
        # ...]====]
        # (-)654321
        symbol_len = level + 2
        bytes_io = io.BytesIO()
        str_iter = iter(self.text.text[symbol_len:-symbol_len])
        converting_end_of_line = False
        first_character_seen = False
        for character in str_iter:
            # Any kind of end-of-line sequence (carriage return, newline,
            # carriage return followed by newline, or newline followed by
            # carriage return) is converted to a simple newline.
            if character in ("\r", "\n"):
                if not first_character_seen:
                    # When the opening long bracket is immediately followed by a
                    # newline, the newline is not included in the string.
                    converting_end_of_line = True
                    first_character_seen = True
                    continue
                if converting_end_of_line:
                    continue
                first_character_seen = True
                converting_end_of_line = True
                bytes_io.write(b"\n")
                continue
            else:
                first_character_seen = True
                converting_end_of_line = False
                bytes_io.write(character.encode("utf-8"))
        bytes_io.seek(0)
        return LuaString(bytes_io.read())

    def evaluate(self, vm: VirtualMachine) -> LuaString:
        if self.text.text[0] != "[":
            return self._simple_string()
        return self._long_bracket()


@attrs.define(slots=True)
class LiteralFalse(Expression):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        return ay_values.LuaBool(False)


@attrs.define(slots=True)
class LiteralTrue(Expression):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        return ay_values.LuaBool(True)


@attrs.define(slots=True)
class LiteralNil(Expression):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        return ay_values.LuaNil


@attrs.define(slots=True)
class Name(NonTerminal):
    name: Terminal

    def as_lua_string(self):
        return str_to_lua_string(self.name.text)


@attrs.define(slots=True)
class Variable(Expression, ABC):
    pass


@attrs.define(slots=True)
class VarName(Variable):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        return vm.get(str_to_lua_string(self.name.name.text))

    name: Name


@attrs.define(slots=True)
class VarIndex(Variable):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        table = self.base.evaluate(vm)
        assert isinstance(table, LuaTable)
        return table.get(self.index.evaluate(vm))

    base: Expression
    index: Expression


@attrs.define(slots=True)
class TableConstructor(Expression):
    fields: Sequence[Field]

    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        table = LuaTable()
        if not self.fields:
            return table
        counter = 1
        # If the last field in the list has the form exp and the expression is a
        # multires expression,
        # then all values returned by this expression enter the list
        # consecutively (see §3.4.12).
        last_field = self.fields[-1]
        if last_field and isinstance(last_field, FieldCounterKey):
            field_iter = iter(self.fields[:-1])
        else:
            field_iter = iter(self.fields)
        for field in field_iter:
            if isinstance(field, FieldWithKey):
                if isinstance(field.key, Name):
                    key = str_to_lua_string(field.key.name.text)
                elif isinstance(field.key, Expression):
                    key = field.key.evaluate(vm)
                else:
                    raise NotImplementedError(f"{type(field.key)=}")
                table.put(key, field.value.evaluate(vm))
            elif isinstance(field, FieldCounterKey):
                key = LuaNumber(counter, LuaNumberType.INTEGER)
                counter += 1
                table.put(key, field.value.evaluate(vm))
            else:
                raise NotImplementedError(f"{type(field)=}")
        if last_field and isinstance(last_field, FieldCounterKey):
            last_field_value = last_field.value.evaluate(vm)
            if isinstance(last_field_value, list):
                for counter, val in enumerate(last_field_value, start=counter):
                    table.put(
                        LuaNumber(counter, LuaNumberType.INTEGER),
                        val,
                    )
            else:
                table.put(
                    LuaNumber(counter, LuaNumberType.INTEGER),
                    last_field_value,
                )
        return table


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
class FuncBody(Expression):
    params: Sequence[Name]
    body: Block
    vararg: bool = False

    def evaluate(self, vm: VirtualMachine) -> LuaFunction:
        return LuaFunction(
            param_names=[p.as_lua_string() for p in self.params],
            variadic=self.vararg,
            block=self.body,
            parent_stack_frame=vm.stack_frame,
            interacts_with_the_vm=False,
        )


@attrs.define(slots=True)
class FuncDef(Expression):
    body: FuncBody

    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        return self.body.evaluate(vm)


def _call_function(
    vm: VirtualMachine,
    function: LuaFunction,
    args: list[LuaValue],
):
    new_stack_frame = StackFrame(parent=function.parent_stack_frame)
    if not callable(function.block):
        if function.variadic:
            new_stack_frame.varargs = args[len(function.param_names):]
        args = adjust(args, len(function.param_names))
        new_vm = vm.push()
        for param_name, arg in zip(function.param_names, args):
            new_stack_frame.put_local(param_name, ay_values.Variable(arg))
        function.block.evaluate(new_vm)
    else:
        if not function.interacts_with_the_vm:
            function.block(*args)
        else:
            function.block(vm, *args)


def call_function(
    vm: VirtualMachine, function: LuaFunction, args: list[LuaValue]
) -> list[LuaValue]:
    try:
        _call_function(vm, function, args)
    except ReturnException as e:
        return e.values if e.values is not None else []
    return [ay_values.LuaNil]


@attrs.define(slots=True)
class FuncCallRegular(Expression, Statement):
    def evaluate(self, vm: VirtualMachine) -> Sequence[LuaValue]:
        function = self.name.evaluate(vm)
        assert isinstance(function, LuaFunction)
        args = [arg.evaluate(vm) for arg in self.args]
        return call_function(vm, function, args)

    def execute(self, vm: VirtualMachine) -> None:
        try:
            self.evaluate(vm)
        except ReturnException:
            pass

    name: Expression
    args: Sequence[Expression]


@attrs.define(slots=True)
class FuncCallMethod(Expression, Statement):
    def evaluate(self, vm: VirtualMachine) -> Sequence[LuaValue]:
        # A call v:name(args) is syntactic sugar for v.name(v,args),
        # except that v is evaluated only once.
        v = self.object.evaluate(vm)
        assert isinstance(v, LuaTable)
        function = v.get(str_to_lua_string(self.method.name.text))
        assert isinstance(function, LuaFunction)
        args = [arg.evaluate(vm) for arg in self.args]
        return call_function(vm, function, args)

    def execute(self, vm: VirtualMachine) -> None:
        try:
            self.evaluate(vm)
        except ReturnException:
            pass

    object: Expression
    method: Name
    args: Sequence[Expression]


@attrs.define(slots=True)
class Unary(Expression):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        v = self.exp.evaluate(vm)
        match self.op.text:
            case "-":
                return ay_operations.arith_unary_minus(v)
            case "#":
                return ay_operations.length(v)
            case "~":
                return ay_operations.bitwise_unary_not(v)
            case "not":
                return ay_operations.logical_unary_not(v)
            case _:
                raise NotImplementedError(f"{self.op=}")

    op: Terminal
    exp: Expression


@attrs.define(slots=True)
class BinOp(Expression, ABC):
    lhs: Expression
    rhs: Expression


@attrs.define(slots=True)
class SumOp(BinOp):
    def evaluate(self, vm: VirtualMachine) -> LuaValue:
        left = self.lhs.evaluate(vm)
        right = self.rhs.evaluate(vm)
        match self.op:
            case "+":
                return ay_operations.arith_add(left, right)
            case "-":
                return ay_operations.arith_sub(left, right)
            case _:
                raise NotImplementedError(f"{self.op=}")

    op: Literal["+", "-"]


@attrs.define(slots=True)
class ReturnStatement(NonTerminal):
    values: Sequence[Expression]


@attrs.define(slots=True)
class EmptyStatement(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        pass


@attrs.define(slots=True)
class Assignment(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        values = adjust(
            [expr.evaluate(vm) for expr in self.exprs], len(self.names)
        )
        for variable, value in zip(self.names, values):
            if isinstance(variable, VarName):
                var_name = str_to_lua_string(variable.name.name.text)
                vm.put_nonlocal(var_name, ay_values.Variable(value))
            elif isinstance(variable, VarIndex):
                table = variable.base.evaluate(vm)
                assert isinstance(table, LuaTable)
                table.put(variable.index.evaluate(vm), value)
            else:
                raise NotImplementedError(f"{type(variable)=}")

    names: Sequence[Variable]
    exprs: Sequence[Expression]


@attrs.define(slots=True)
class Label(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        raise NotImplementedError()

    name: Name


@attrs.define(slots=True)
class Break(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        raise BreakException()


@attrs.define(slots=True)
class Goto(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        raise GotoException(self.name)

    name: Name


@attrs.define(slots=True)
class Do(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        self.block.execute(vm)

    block: Block


@attrs.define(slots=True)
class While(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        new_vm = vm.push()
        try:
            while coerce_to_bool(self.condition.evaluate(vm)).true:
                self.block.execute(new_vm)
        except BreakException:
            pass

    condition: Expression
    block: Block


@attrs.define(slots=True)
class Repeat(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        new_vm = vm.push()
        try:
            while True:
                self.block.execute(new_vm)
                if coerce_to_bool(self.condition.evaluate(new_vm)).true:
                    break
        except BreakException:
            pass

    block: Block
    condition: Expression


@attrs.define(slots=True)
class If(Statement):
    def execute(self, vm: VirtualMachine) -> None:
        for cnd, blk in self.blocks:
            if coerce_to_bool(cnd.evaluate(vm)).true:
                blk.execute(vm.push())
                return
        if self.else_block:
            self.else_block.execute(vm.push())

    blocks: Sequence[tuple[Expression, Block]]
    else_block: Block | None = None


@attrs.define(slots=True)
class For(Statement):
    name: Name
    start: Expression
    stop: Expression
    step: Expression | None
    block: Block

    def execute(self, vm: VirtualMachine) -> None:
        try:
            self._execute(vm)
        except BreakException:
            pass

    def _execute(self, vm: VirtualMachine) -> None:
        # This for loop is the "numerical" for loop explained in 3.3.5.
        # The given identifier (Name) defines the control variable,
        # which is a new variable local to the loop body (block).
        control_varname = self.name.as_lua_string()
        # The loop starts by evaluating once the three control expressions.
        # Their values are called respectively
        # the initial value,
        initial_value: LuaNumber = self.start.evaluate(vm)
        assert isinstance(initial_value, LuaNumber)
        # the limit,
        limit: LuaNumber = self.stop.evaluate(vm)
        assert isinstance(initial_value, LuaNumber)
        # and the step. If the step is absent, it defaults to 1.
        if self.step:
            step: LuaNumber = self.step.evaluate(vm)
            assert isinstance(initial_value, LuaNumber)
        else:
            step: LuaNumber = LuaNumber(1, LuaNumberType.INTEGER)
        # If both the initial value and the step are integers,
        # the loop is done with integers;
        # note that the limit may not be an integer.
        integer_loop = (
            initial_value.type == LuaNumberType.INTEGER
            and step.type == LuaNumberType.INTEGER
        )
        if not integer_loop:
            # Otherwise, the three values are converted to floats
            # and the loop is done with floats.
            initial_value = ay_operations.coerce_int_to_float(initial_value)
            limit = ay_operations.coerce_int_to_float(limit)
            step = ay_operations.coerce_int_to_float(step)
        # After that initialization, the loop body is repeated with the value of
        # the control variable going through an arithmetic progression,
        # starting at the initial value,
        # with a common difference given by the step.
        # A negative step makes a decreasing sequence;
        # a step equal to zero raises an error.
        if step.value == 0:
            raise NotImplementedError()
        # The loop continues while the value is less than or equal to the limit
        # (greater than or equal to for a negative step).
        # If the initial value is already greater than the limit
        # (or less than, if the step is negative),
        # the body is not executed.
        step_negative = step.value < 0
        condition_func = (
            ay_operations.rel_ge if step_negative else ay_operations.rel_le
        )
        # For integer loops, the control variable never wraps around; instead,
        # the loop ends in case of an overflow.
        # You should not change the value of the control variable during the
        # loop.
        # If you need its value after the loop, assign it to another variable
        # before exiting the loop.
        control_val = initial_value
        new_vm = vm.push()
        while condition_func(control_val, limit).true:
            new_vm.put_local(control_varname, ay_values.Variable(control_val))
            self.block.execute(new_vm)
            overflow, control_val = ay_operations.overflow_arith_add(
                control_val, step
            )
            if overflow and integer_loop:
                break


@attrs.define(slots=True)
class ForIn(Statement):
    names: Sequence[Name]
    exprs: Sequence[Expression]
    block: Block

    def execute(self, vm: VirtualMachine) -> None:
        try:
            self._execute(vm)
        except BreakException:
            pass

    def _execute(self, vm: VirtualMachine) -> None:
        # The generic for statement works over functions, called iterators.
        # On each iteration, the iterator function is called to produce a new
        # value, stopping when this new value is nil.

        #  A for statement like
        #      for var_1, ···, var_n in explist do body end
        # works as follows.
        # The names var_i declare loop variables local to the loop body.
        new_vm = vm.push()
        body_stack_frame = new_vm.stack_frame
        name_count = len(self.names)
        names = [name.as_lua_string() for name in self.names]
        for name in names:
            body_stack_frame.put_local(
                name, ay_values.Variable(ay_values.LuaNil)
            )
        # The first of these variables is the control variable.
        control_variable_name = names[0]
        # The loop starts by evaluating explist to produce four values:
        exp_vals = adjust([exp.evaluate(vm) for exp in self.exprs], 4)
        # an iterator function,
        iterator_function = exp_vals[0]
        if not isinstance(iterator_function, LuaFunction):
            raise NotImplementedError()
        # a state,
        state = exp_vals[1]
        # an initial value for the control variable,
        initial_value = exp_vals[2]
        body_stack_frame.put_local(
            control_variable_name, ay_values.Variable(initial_value)
        )
        # and a closing value.
        closing_value = exp_vals[3]

        nil = ay_values.LuaNil
        while True:
            # Then, at each iteration, Lua calls the iterator function with two
            # arguments: the state and the control variable.
            results = adjust(
                call_function(
                    vm,
                    iterator_function,
                    [state, body_stack_frame.get(control_variable_name)],
                ),
                name_count,
            )
            # The results from this call are then assigned to the loop
            # variables, following the rules of multiple assignments.
            for name, value in zip(names, results):
                body_stack_frame.put_local(name, ay_values.Variable(value))
            # If the control variable becomes nil, the loop terminates.
            if results[0] is nil:
                break
            # Otherwise, the body is executed and the loop goes to the next
            # iteration.
            self.block.execute(new_vm)
            continue
        if closing_value is not nil:
            # The closing value behaves like a to-be-closed variable,
            # which can be used to release resources when the loop ends.
            # Otherwise, it does not interfere with the loop.
            raise NotImplementedError()


@attrs.define(slots=True)
class FuncName(NonTerminal):
    names: Sequence[Name]
    method: bool


@attrs.define(slots=True)
class Function(Statement):
    name: FuncName
    body: FuncBody

    def execute(self, vm: VirtualMachine) -> None:
        function = self.body.evaluate(vm)
        if self.name.method:
            function.param_names.insert(0, LuaString(b"self"))
        if len(self.name.names) == 1:
            name = self.name.names[0].as_lua_string()
            vm.put_nonlocal(name, ay_values.Variable(function))
        else:
            table = vm.get(self.name.names[0].as_lua_string())
            for name in self.name.names[1:-1]:
                table = table.get(name.as_lua_string())
                assert isinstance(table, LuaTable)
            table.put(self.name.names[-1], function)


@attrs.define(slots=True)
class LocalFunction(Statement):
    name: Name
    body: FuncBody

    def execute(self, vm: VirtualMachine) -> None:
        # The statement
        #      local function f () body end
        # translates to
        #      local f; f = function () body end
        # not to
        #      local f = function () body end
        # (This only makes a difference
        # when the body of the function contains references to f.)
        name = self.name.as_lua_string()
        vm.put_local(name, ay_values.Variable(ay_values.LuaNil))
        function = self.body.evaluate(vm)
        vm.put_local(name, ay_values.Variable(function))


@attrs.define(slots=True)
class AttributeName(NonTerminal):
    name: Name
    attrib: Name | None = None


@attrs.define(slots=True)
class LocalAssignment(Statement):
    names: Sequence[AttributeName]
    exprs: Sequence[Expression]

    def execute(self, vm: VirtualMachine) -> None:
        if self.exprs:
            exp_vals = [exp.evaluate(vm) for exp in self.exprs]
            exp_vals = adjust(exp_vals, len(self.names))
        else:
            exp_vals = [ay_values.LuaNil] * len(self.names)
        used_closed = False
        for attname, exp_val in zip(self.names, exp_vals):
            var_name = attname.name.as_lua_string()
            if attname.attrib is None:
                vm.put_local(var_name, ay_values.Variable(exp_val))
            else:
                attrib = attname.attrib.as_lua_string()
                if attrib.content == b"close":
                    if used_closed:
                        raise NotImplementedError()
                    used_closed = True
                    vm.put_local(
                        var_name, ay_values.Variable(exp_val, to_be_closed=True)
                    )
                elif attrib.content == b"const":
                    vm.put_local(
                        var_name, ay_values.Variable(exp_val, constant=True)
                    )
                else:
                    # TODO: Create an error
                    raise NotImplementedError()
