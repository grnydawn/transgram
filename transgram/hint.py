##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals

from parsimonious import Grammar, NodeVisitor

#NOTE: all value should be evaluated first including function

hint_notation = (r'''
    # directives
    directive = sample_directive

    # sample directive
    sample_directive = "sample" _1 sample_clauses
    sample_clauses  = sample_clause comma_sample_clause*
    comma_sample_clause = comma sample_clause
    sample_clause  = maxloops_clause / maxrepeats_clause / randomize_clause
    maxloops_clause  = "maxloops" _ paren_int_expr
    maxrepeats_clause= "maxrepeats" _ paren_int_expr
    randomize_clause = "randomize" _ paren_int_expr

    # common expressions
    paren_int_expr   = "(" _ int_expr ")" _
    paren_literal_expr   = "(" _ literal_expr ")" _
    literal_expr     = spaceless_literal _
    spaceless_literal= ~"u?r?\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\""is /
                        ~"u?r?'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"is
    int_expr         = product_expr int_expr_opt?
    int_expr_opt     = ('+' / '-') _ product_expr
    product_expr     = power_expr product_expr_opt?
    product_expr_opt = ('*' / '/') _ power_expr
    power_expr       = value power_expr_opt?
    power_expr_opt   = '^' _ value
    value            = unary_op? (digit / paren_int_expr)
    unary_op         = ('+' / '-') _
    function_reference= function_name "(" _ arguments ")" _
    arguments        = argument comma_argument*
    comma_argument   = comma argument
    argument         = int_expr / variable_name
    function_name    = label
    variable_name    = label
    label           = ~"[a-zA-Z_][a-zA-Z_0-9]*" _
    digit            = ~"[0-9]+" _
    integer          = ~"[-+]?[0-9]+" _
    comma            = "," _
    _                = ~r"[ \t]*"
    _1               = ~r"[ \t]+"
''')

hint_syntax = Grammar(hint_notation)


class Hint(NodeVisitor):

    directive = {}

    def __init__(self, sentence):
        self.sentence = sentence
        self.tree = hint_syntax.parse(sentence)
        self.hints = {
            "sample" : {}
        }

    def _regex(self, node, items):
        return [node.text]

    def _literal(self, node, items):
        return [node.text]

    def _optional(self, node, items):
        if items:
            assert len(items) == 1
            return items[0]
        else:
            return items

    def _sequence(self, node, items):
        retval = []
        for item in items:
            retval.extend(item)
        return retval

    def _zeroormore(self, node, items):
        if items:
            retval = []
            for item in items:
                retval.extend(item)
            return retval
        else:
            return items

    def _oneof(self, node, items):
        assert len(items) == 1
        return items[0]

    def generic_visit(self, node, items):
        clsname = node.expr.__class__.__name__.lower()
        return getattr(self, '_'+clsname)(node, items)

    def visit_comma(self, node, items):
        return []

    def visit_digit(self, node, items):
        return [int(items[0][0])]

    def visit_label(self, node, items):
        return items[0]

    def visit_value(self, node, items):
        if items[0] and items[0][0] == "-":
            return [items[1][0]*-1]
        else:
            return items[1]

    def visit_power_expr(self, node, items):
        if items[1]:
            import pdb; pdb.set_trace()
        else:
            return items[0]

    def visit_product_expr(self, node, items):
        if items[1]:
            import pdb; pdb.set_trace()
        else:
            return items[0]

    def visit_int_expr_opt(self, node, items):
        if items[0] == "-":
            return [-1*items[2][0]]
        else:
            return items[2]

    def visit_int_expr(self, node, items):
        if items[1]:
            return [items[0][0] + items[1][0]]
        else:
            return items[0]

    def visit_paren_int_expr(self, node, items):
        return items[2]

    def visit_maxloops_clause(self, node, items):
        self.hints["sample"][items[0][0]] = items[2][0]
        return []

    def visit_maxrepeats_clause(self, node, items):
        self.hints["sample"][items[0][0]] = items[2][0]
        return []

    def visit_randomize_clause(self, node, items):
        self.hints["sample"][items[0][0]] = items[2][0]
        return []

    def visit_comma_sample_clause(self, node, items):
        return []

    def collect(self, modes=None):
        self.visit(self.tree)
        if isinstance(modes, str):
            return self.hints[modes]
        elif modes is None:
            return self.hints
        else:
            partial_hints = {}
            for name, hint in self.hints.items():
                if name in modes:
                    partial_hints[name] = hint
            return partial_hints
