##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import functools
from .grammar import Grammar
from .nodes import NodeVisitor
from .expressions import (Literal, Regex, Not, ZeroOrMore,
    OneOrMore, Optional, Sequence, OneOf)
from .lego import parse as lego_parse, lego, mult, qm, plus, star, reduce_after, call_fsm
import random

new_notation = (r'''
    # New notation to express context-free and context-sensitive grammars

    # high-level rules
    rules           = _ rule*
    rule            = label expression_attributes_angle? colon expression
    expression      = firstmatched / ored / sequence / term
    firstmatched    = term firstmatch_term+
    ored            = term or_term+
    sequence        = left? term term+ right? expression_attributes_brace?
    term            = quantified / atom

    # choice terms
    firstmatch_term = ("/" _ ored) / ("/" _ term)
    or_term         = "|" _ term

    # expression attributes
    expression_attributes_angle = "<" _ attribute_parts? ">" _
    expression_attributes_brace = "{" _ attribute_parts? "}" _
    semicolon_separated_part = semicolon attribute_items
    attribute_parts = attribute_items semicolon_separated_part*
    attribute_name = attr_label colon
    comma_separated_term = comma attr_label
    attribute_items = attribute_name? attr_label comma_separated_term*

    # primitive terms
    quantified      = atom quantifier
    atom            = reference / literal / regex / parenthesized
    #regex           = "~" spaceless_literal ~"[ilmsux]*"i _
    regex           = "~" spaceless_literal _
    parenthesized   = "(" _ expression ")" _
    quantifier      = ~"[*+?]" _
    reference       = label !colon
    literal         = spaceless_literal _
    spaceless_literal = ~"u?r?\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\""is /
                        ~"u?r?'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"is

    # primitive items
    _               = meaninglessness*
    attr_label      = label
    label           = ~"[a-zA-Z_][a-zA-Z_0-9]*" _
    meaninglessness = blanks / comment
    blanks          = hspaces / vspaces
    hspaces         = ~r"[ \t]+"
    vspaces         = ~r"[\r\n\f\v]+"
    comment         = "#" ~r"[^\r\n]*"
    colon           = ":" _
    comma           = "," _
    semicolon       = ";" _
    left            = "=>" _
    right           = "<=" _
''')

schars = [".", "^", "$", "*", "+", "?", "{", "}", "[", "]", "|", "(", ")", "\\"]
DEBUG = False


class Sampler(NodeVisitor):


    def __init__(self):
        ''' string: string, listgenerator: generator,
            set: one of, tuple: firstmatch of, list: sequence
        '''

        # contains all the rules
        # rule_name: rule_handler
        # rule_handler type matches with ...
        # usage: user picks a rule and execute sample function
        # a rule maintains state for generation of string
        # a rule handler may use multiple another rule handlers
        # generators for each rules
        # each generator may return a list??
        self.rules = {}

    def _oneof(self, *rules):
        # return generator

    def _firstmatchof(self, *rules):
        # return generator

    def _sequence(self, *rules):
        # return generator

    def _optional(self, *rules):
        # return generator

    def generic_visit(self, node, items):
        print("GV", node.expr)

    def visit_attribute_name(self, node, items):
        import pdb; pdb.set_trace()
        return items[0]

    def visit_attribute_items(self, node, items):
        import pdb; pdb.set_trace()
        return [items[0], [items[1]]+items[2]]

    def visit_comma_separated_term(self, node, items):
        import pdb; pdb.set_trace()
        return items[1]

    def visit_semicolon_separated_part(self, node, items):
        import pdb; pdb.set_trace()
        return items[1]

    def visit_attribute_parts(self, node, items):
        import pdb; pdb.set_trace()
        return [items[0]]+items[1]

    def visit_expression_attributes_angle(self, node, items):
        import pdb; pdb.set_trace()
        return items[2]

    def visit_firstmatch_term(self, node, items):
        import pdb; pdb.set_trace()

    def visit_firstmatched(self, node, items):
        import pdb; pdb.set_trace()

    def visit_or_term(self, node, items):
        import pdb; pdb.set_trace()
        return items[2]

    def visit_ored(self, node, items):
        import pdb; pdb.set_trace()
        return [items[0]]+items[1]

    def visit_left(self, node, items):
        import pdb; pdb.set_trace()
        return True if items[0] else None

    def visit_right(self, node, items):
        import pdb; pdb.set_trace()
        return True if items[0] else None

    def visit_expression_attributes_brace(self, node, items):
        import pdb; pdb.set_trace()
        return items[2]

    def visit_sequence(self, node, items):
        import pdb; pdb.set_trace()

    def visit_quantified(self, node, items):
        import pdb; pdb.set_trace()

    def visit_spaceless_literal(self, node, items):
        import pdb; pdb.set_trace()
        return items[0]

    def visit_blanks(self, node, items):
        ch = ''
        if node.text:
            ch = '\n' if node.text.find('\n')>=0 else ' '
        self.rules['blanks'] = iter([ch for n in range(1000)])

    def visit_comment(self, node, items):
        self.rules['comment'] = iter(['#CMT%d'%n for n in range(100)])

    def visit_meaninglessness(self, node, items):
        self.rules['meaninglessness'] = ('blanks', 'comment')

    def visit__(self, node, items):
        self.rules['_'] = ['meaninglessness', '*']

    def visit_literal(self, node, items):
        import pdb; pdb.set_trace()
        return items[0]

    def visit_quantifier(self, node, items):
        import pdb; pdb.set_trace()

    def visit_regex(self, node, items):
        import pdb; pdb.set_trace()

    def visit_parenthesized(self, node, items):
        import pdb; pdb.set_trace()
        return items[2]

    def visit_atom(self, node, items):
        import pdb ;pdb.set_trace()
        return self.reduce(items, "+")

    def visit_term(self, node, items):
        import pdb ;pdb.set_trace()
        return self.reduce(items, "+")

    def visit_expression(self, node, items):
        import pdb ;pdb.set_trace()
        return self.reduce(items, "+")

    def visit_rule(self, node, items):
        import pdb; pdb.set_trace()

    def visit_rules(self, node, items):
        import pdb; pdb.set_trace()
        #print(node)
        pass

#class Translate2Parglare(NodeVisitor):
#
#    def generic_visit(self, node, items):
#        if not node.expr.name:
#            if isinstance(node.expr, (Literal, Regex)):
#                return node.text
#            elif isinstance(node.expr, Optional):
#                return items[0] if items else None
#            elif isinstance(node.expr, (ZeroOrMore, OneOrMore,
#                Sequence)):
#                return items
#
#    def visit_comma(self, node, items):
#        return items[0]
#
#    def visit_colon(self, node, items):
#        return items[0]
#
#    def visit_label(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[0]
#
#    def visit_attribute_name(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[0]
#
#    def visit_attribute_items(self, node, items):
#        return [items[0], [items[1]]+items[2]]
#
#    def visit_comma_separated_term(self, node, items):
#        return items[1]
#
#    def visit_semicolon_separated_part(self, node, items):
#        return items[1]
#
#    def visit_attribute_parts(self, node, items):
#        return [items[0]]+items[1]
#
#    def visit_expression_attributes_angle(self, node, items):
#        return items[2]
#
#    def visit_firstmatch_term(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_firstmatched(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_or_term(self, node, items):
#        return items[2]
#
#    def visit_ored(self, node, items):
#        return [items[0]]+items[1]
#
#    def visit_left(self, node, items):
#        return True if items[0] else None
#
#    def visit_right(self, node, items):
#        return True if items[0] else None
#
#    def visit_expression_attributes_brace(self, node, items):
#        return items[2]
#
#    def visit_sequence(self, node, items):
#        return [items[0], [items[1]]+items[2], items[3], items[4]]
#
#    def visit_quantified(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_reference(self, node, items):
#        return items[0]
#
#    def visit_spaceless_literal(self, node, items):
#        return items[0]
#
#    def visit_blanks(self, node, items):
#        return items[0] if items else None
#
#    def visit_comment(self, node, items):
#        return items[1]
#
#    def visit_meaninglessness(self, node, items):
#        return items[0]
#
#    def visit__(self, node, items):
#        return [item for item in items if item]
#
#    def visit_literal(self, node, items):
#        return items[0]
#
#    def visit_quantifier(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_regex(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_parenthesized(self, node, items):
#        return items[2]
#
#    def visit_atom(self, node, items):
#        return items[0]
#
#    def visit_term(self, node, items):
#        return items[0]
#
#    def visit_expression(self, node, items):
#        return items[0]
#
#    def visit_rule(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_rules(self, node, items):
#        import pdb; pdb.set_trace()
#        #print(node)
#        pass

def translate(custom_grammar):
    new_syntax = Grammar(new_notation)
    grammar_tree = new_syntax.parse(custom_grammar)
    sampler = Sampler().visit(grammar_tree)
    import pdb; pdb.set_trace()
    #cgrammar = CanonicalGrammar().visit(parsetree)
    #parglare_grammar = translate_to_parglare(cgrammar)
    #parglare_parsers = generate_parglare_parsers(parglare_grammar)
