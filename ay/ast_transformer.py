from collections.abc import Sequence

import ay.ast_nodes as nodes

import lark


def to_string_literal(
    i: nodes.Name,
    /,
) -> nodes.LiteralString:
    if isinstance(i, nodes.Name):
        return nodes.LiteralString(text=nodes.Terminal(text=i.name.text))
    raise TypeError(f"Can't turn {i=} to a string literal")


@lark.v_args(inline=True)
class LuaTransformer(lark.Transformer):
    def __default__(self, data, children, meta):
        raise NotImplementedError(
            f"Unimplemented transformer for {data=}, {children=}, {meta=}"
        )

    def __default_token__(self, token):
        return nodes.Terminal(text=token.value)

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
            return nodes.VarIndex(base=base, index=to_string_literal(index))
        return nodes.VarIndex(base=base, index=index)

    @staticmethod
    def varlist(*args: nodes.Variable) -> Sequence[nodes.Variable]:
        return args

    @staticmethod
    def tableconstructor(fieldlist: Sequence[nodes.FieldWithKey] | None) \
            -> nodes.TableConstructor:
        if fieldlist is None:
            return nodes.TableConstructor(fields=tuple())
        return nodes.TableConstructor(fields=fieldlist)

    @staticmethod
    def explist(*args: nodes.Expression) -> Sequence[nodes.Expression]:
        return args

    @staticmethod
    def stat_assignment(
            varlist: list[nodes.Variable],
            explist: list[nodes.Expression]) -> nodes.Assignment:
        return nodes.Assignment(names=varlist, exprs=explist)

    @staticmethod
    def numeral_dec(
            digits: nodes.Terminal,
            fract_digits: nodes.Terminal | None,
            e_sign: nodes.Terminal | None,
            e_digits: nodes.Terminal | None) -> nodes.NumeralDec:
        return nodes.NumeralDec(
            digits=digits,
            fract_digits=fract_digits,
            e_sign=e_sign,
            e_digits=e_digits,
        )

    @staticmethod
    def field_with_key(
            key: nodes.Expression | nodes.Name,
            value: nodes.Expression) -> nodes.FieldWithKey:
        return nodes.FieldWithKey(key=key, value=value)

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
    def attname(name: nodes.Name, attrib: nodes.Name | None) \
            -> nodes.AttributeName:
        return nodes.AttributeName(name=name, attrib=attrib)

    @staticmethod
    def attnamelist(*args: nodes.AttributeName) \
            -> Sequence[nodes.AttributeName]:
        return args

    @staticmethod
    def stat_localassignment(*children) -> nodes.LocalAssignment:
        LOCAL, attnames, values = children
        return nodes.LocalAssignment(names=attnames, exprs=values)

    @staticmethod
    def sumop(op: nodes.Terminal) -> nodes.Terminal:
        return op

    @staticmethod
    def exp_sum(l: nodes.Expression, o: nodes.Terminal, r: nodes.Expression):
        return nodes.SumOp(
            lhs=l,
            op=o.text,
            rhs=r,
        )

    @staticmethod
    def stat_empty():
        return nodes.EmptyStatement()

    @staticmethod
    def retstat(_, values: Sequence[nodes.Expression]) -> nodes.ReturnStatement:
        return nodes.ReturnStatement(values=values)

    @staticmethod
    def funcbody(parlist, block, END):
        if parlist is None:
            return nodes.FuncBody(params=tuple(), body=block)
        raise NotImplementedError()

    @staticmethod
    def exp_functiondef(funcbody: nodes.FuncBody) -> nodes.FuncDef:
        return nodes.FuncDef(body=funcbody)

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
    def namelist(*names: nodes.Name) -> Sequence[nodes.Name]:
        return names

    @staticmethod
    def args_list(explist: Sequence[nodes.Expression]) \
            -> Sequence[nodes.Expression]:
        if explist is None:
            return tuple()
        return explist

    @staticmethod
    def args_value(value: nodes.Expression) -> Sequence[nodes.Expression]:
        return (value,)

    @staticmethod
    def functioncall_regular(
            name: nodes.Expression,
            args: Sequence[nodes.Expression]) -> nodes.FuncCallRegular:
        return nodes.FuncCallRegular(name=name, args=args)
