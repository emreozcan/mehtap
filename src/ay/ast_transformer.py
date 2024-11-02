from collections.abc import Sequence

import lark

import ay.ast_nodes as nodes
from ay.ast_nodes import BinaryOperator


@lark.v_args(inline=True)
class LuaTransformer(lark.Transformer):
    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"Unimplemented transformer for {data=}, {children=}, {meta=}"
        )

    def __default_token__(self, token):
        return nodes.Terminal(text=token.value)

    def _call_userfunc(self, tree: lark.Tree, new_children=None):
        node: nodes.Node = super()._call_userfunc(tree, new_children)
        if not tree.meta.empty:
            if isinstance(node, Sequence):
                for child in node:
                    child.line = tree.meta.line
            else:
                node.line = tree.meta.line
        return node

    def _call_userfunc_token(self, token: lark.Token):
        node: nodes.Node = super()._call_userfunc_token(token)
        node.line = token.line
        return node

    @staticmethod
    def NAME(token: lark.Token):
        return nodes.Name(name=nodes.Terminal(text=token.value))

    @staticmethod
    def var_name(name: nodes.Name) -> nodes.VarName:
        return nodes.VarName(name=name)

    @staticmethod
    def var_index(
        base: nodes.Expression,
        index: nodes.Expression | nodes.Name,
    ) -> nodes.VarIndex:
        if isinstance(index, nodes.Name):
            return nodes.VarIndex(
                base=base,
                index=nodes.ParsedLiteralLuaStringExpr(index.as_lua_string()),
            )
        return nodes.VarIndex(base=base, index=index)

    @staticmethod
    def exp_vararg() -> nodes.VarArgExpr:
        return nodes.VarArgExpr()

    @staticmethod
    def varlist(*args: nodes.Variable) -> Sequence[nodes.Variable]:
        return args

    @staticmethod
    def tableconstructor(
        fieldlist: Sequence[nodes.FieldWithKey] | None,
    ) -> nodes.TableConstructor:
        if fieldlist is None:
            return nodes.TableConstructor(fields=tuple())
        return nodes.TableConstructor(fields=fieldlist)

    @staticmethod
    def explist(*args: nodes.Expression) -> Sequence[nodes.Expression]:
        return args

    @staticmethod
    def stat_assignment(
        varlist: list[nodes.Variable], explist: list[nodes.Expression]
    ) -> nodes.Assignment:
        return nodes.Assignment(names=varlist, exprs=explist)

    @staticmethod
    def sign(token: nodes.Terminal) -> nodes.Terminal:
        return token

    @staticmethod
    def numeral_dec(
        digits: nodes.Terminal,
        fract_digits: nodes.Terminal | None,
        e_sign: nodes.Terminal | None,
        e_digits: nodes.Terminal | None,
    ) -> nodes.NumeralDec:
        return nodes.NumeralDec(
            digits=digits,
            fract_digits=fract_digits,
            e_sign=e_sign,
            e_digits=e_digits,
        )

    @staticmethod
    def numeral_hex(
        digits: nodes.Terminal,
        fract_digits: nodes.Terminal | None,
        p_sign: nodes.Terminal | None,
        p_digits: nodes.Terminal | None,
    ) -> nodes.NumeralHex:
        return nodes.NumeralHex(
            digits=digits,
            fract_digits=fract_digits,
            p_sign=p_sign,
            p_digits=p_digits,
        )

    @staticmethod
    def field_with_key(
        key: nodes.Expression | nodes.Name,
        value: nodes.Expression,
    ) -> nodes.FieldWithKey:
        return nodes.FieldWithKey(key=key, value=value)

    @staticmethod
    def field_counter_key(value: nodes.Expression) -> nodes.FieldCounterKey:
        return nodes.FieldCounterKey(value=value)

    @staticmethod
    def fieldsep():
        return lark.Discard

    @staticmethod
    def fieldlist(*children) -> Sequence[nodes.Field]:
        *fields, fieldsep = children
        return fields

    @staticmethod
    def block(*children) -> nodes.Block:
        *statements, return_statement = children
        return nodes.Block(
            statements=statements,
            return_statement=return_statement,
        )

    @staticmethod
    def chunk(block: nodes.Block) -> nodes.Chunk:
        return nodes.Chunk(block=block)

    @staticmethod
    def attrib(name: nodes.Name) -> nodes.Name:
        return name

    @staticmethod
    def attname(
        name: nodes.Name, attrib: nodes.Name | None
    ) -> nodes.AttributeName:
        return nodes.AttributeName(name=name, attrib=attrib)

    @staticmethod
    def attnamelist(
        *args: nodes.AttributeName,
    ) -> Sequence[nodes.AttributeName]:
        return args

    @staticmethod
    def stat_localassignment(*children) -> nodes.LocalAssignment:
        LOCAL, attnames, values = children
        return nodes.LocalAssignment(names=attnames, exprs=values)

    @staticmethod
    def cmp_op(op: nodes.Terminal) -> nodes.Terminal:
        return op

    @staticmethod
    def shift_op(op: nodes.Terminal) -> nodes.Terminal:
        return op

    @staticmethod
    def productop(op: nodes.Terminal) -> nodes.Terminal:
        return op

    @staticmethod
    def sumop(op: nodes.Terminal) -> nodes.Terminal:
        return op

    @staticmethod
    def unop(op: nodes.Terminal) -> nodes.Terminal:
        return op

    @staticmethod
    def exp_logical_or(
        left: nodes.Expression, right: nodes.Expression
    ) -> nodes.BinaryOperation:
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.OR,
            rhs=right,
        )

    @staticmethod
    def exp_logical_and(
        left: nodes.Expression, right: nodes.Expression
    ) -> nodes.BinaryOperation:
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.AND,
            rhs=right,
        )

    @staticmethod
    def exp_cmp(
        left: nodes.Expression,
        operation: nodes.Terminal,
        right: nodes.Expression,
    ):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator(operation.text),
            rhs=right,
        )

    @staticmethod
    def exp_bit_or(left: nodes.Expression, right: nodes.Expression):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.BIT_OR,
            rhs=right,
        )

    @staticmethod
    def exp_bit_xor(left: nodes.Expression, right: nodes.Expression):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.BIT_XOR,
            rhs=right,
        )

    @staticmethod
    def exp_bit_and(left: nodes.Expression, right: nodes.Expression):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.BIT_AND,
            rhs=right,
        )

    @staticmethod
    def exp_bit_shift(
        left: nodes.Expression,
        operation: nodes.Terminal,
        right: nodes.Expression,
    ):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator(operation.text),
            rhs=right,
        )

    @staticmethod
    def exp_concat(left: nodes.Expression, right: nodes.Expression):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.CONCAT,
            rhs=right,
        )

    @staticmethod
    def exp_sum(
        left: nodes.Expression,
        operation: nodes.Terminal,
        right: nodes.Expression,
    ):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator(operation.text),
            rhs=right,
        )

    @staticmethod
    def exp_product(
        left: nodes.Expression,
        operation: nodes.Terminal,
        right: nodes.Expression,
    ):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator(operation.text),
            rhs=right,
        )

    @staticmethod
    def exp_unop(operation: nodes.Terminal, operand: nodes.Expression):
        return nodes.UnaryOperation(
            op=nodes.UnaryOperator(operation.text),
            exp=operand,
        )

    @staticmethod
    def exp_pow(left: nodes.Expression, right: nodes.Expression):
        return nodes.BinaryOperation(
            lhs=left,
            op=BinaryOperator.EXP,
            rhs=right,
        )

    @staticmethod
    def stat_empty():
        return nodes.EmptyStatement()

    @staticmethod
    def retstat(_, values: Sequence[nodes.Expression]) -> nodes.ReturnStatement:
        return nodes.ReturnStatement(values=values)

    def parlist(self, namelist) -> nodes.Parlist:
        return nodes.Parlist(
            names=namelist,
            vararg=False,
        )

    def parlist_vararg(self, namelist) -> nodes.Parlist:
        return nodes.Parlist(
            names=namelist,
            vararg=True,
        )

    @staticmethod
    def funcbody(parlist, block, END):
        if parlist is None:
            return nodes.FuncBody(params=tuple(), body=block)
        return nodes.FuncBody(
            params=parlist.names,
            body=block,
            vararg=parlist.vararg,
        )

    @staticmethod
    def exp_functiondef(funcbody: nodes.FuncBody) -> nodes.FuncDef:
        return nodes.FuncDef(body=funcbody)

    @staticmethod
    def funcname(*names) -> nodes.FuncName:
        method = names[-1]
        if method is not None:
            return nodes.FuncName(
                names=[*names[:-1], method],
                method=True,
            )
        return nodes.FuncName(names=names[:-1], method=False)

    @staticmethod
    def stat_function(
        FUNCTION,
        funcname: nodes.FuncName,
        funcbody: nodes.FuncBody,
    ):
        return nodes.FunctionStatement(name=funcname, body=funcbody)

    @staticmethod
    def stat_for(FOR, name, start, stop, step, DO, block, END):
        return nodes.For(
            name=name,
            start=start,
            stop=stop,
            step=step,
            block=block,
        )

    @staticmethod
    def stat_forin(FOR, namelist, IN, explist, DO, block, END):
        return nodes.ForIn(
            names=namelist,
            exprs=explist,
            block=block,
        )

    @staticmethod
    def stat_do(DO, block, END) -> nodes.Do:
        return nodes.Do(block=block)

    @staticmethod
    def namelist(*names: nodes.Name) -> Sequence[nodes.Name]:
        return names

    @staticmethod
    def args_list(
        explist: Sequence[nodes.Expression],
    ) -> Sequence[nodes.Expression]:
        if explist is None:
            return tuple()
        return explist

    @staticmethod
    def args_value(value: nodes.Expression) -> Sequence[nodes.Expression]:
        return (value,)

    @staticmethod
    def functioncall_regular(
        name: nodes.Expression, args: Sequence[nodes.Expression]
    ) -> nodes.FuncCallRegular:
        return nodes.FuncCallRegular(name=name, args=args)

    @staticmethod
    def functioncall_method(
        base: nodes.Expression,
        method: nodes.Name,
        args: Sequence[nodes.Expression],
    ) -> nodes.FuncCallMethod:
        return nodes.FuncCallMethod(
            object=base,
            method=method,
            args=args,
        )

    @staticmethod
    def literalstring(terminal: nodes.Terminal) -> nodes.LiteralString:
        return nodes.LiteralString(text=terminal)

    @staticmethod
    def exp_false(FALSE: nodes.Terminal) -> nodes.LiteralFalse:
        return nodes.LiteralFalse()

    @staticmethod
    def exp_true(TRUE: nodes.Terminal) -> nodes.LiteralTrue:
        return nodes.LiteralTrue()

    @staticmethod
    def exp_nil(NIL: nodes.Terminal) -> nodes.LiteralNil:
        return nodes.LiteralNil()

    @staticmethod
    def exp_parenthesized(exp: nodes.Expression) -> nodes.ParenExpression:
        return nodes.ParenExpression(exp)


transformer = LuaTransformer()
