##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import functools
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.expressions import (Literal, Regex, Not, ZeroOrMore,
    OneOrMore, Optional, Sequence, OneOf)
from .lego import parse as lego_parse, lego, mult, qm, plus, star, reduce_after, call_fsm

myrules = (r'''
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

    class REWrap(object):
        ''' Wrapper class for regular expression '''
        def __init__(self, left, op=None, right=None):
            self.left = left
            self.op = op
            self.right = right

        def reduce(self):
            return self

        def __add__(self, other):
            return self.__class__(self, "+", other)

    def reduce(self, items, op):
        if len(items)>0:
            names = [ "items[%d]"%idx for idx in range(len(items))]
            return eval(op.join(names)).reduce()
        else:
            return lego_parse('')

    def generic_visit(self, node, items):
        if isinstance(node.expr, Literal):
            return lego_parse('')
        #    #string = ["\\"+c if c in schars else c for c in node.text]
        #    #return lego_parse(''.join(string))
        #    if DEBUG: import pdb; pdb.set_trace()
        #    return lego_parse(node.text)
        elif isinstance(node.expr, Regex):
            return lego_parse('')
        elif isinstance(node.expr, Sequence):
            if DEBUG: import pdb; pdb.set_trace()
            return self.reduce(items, "+")
        elif isinstance(node.expr, OneOf):
            if DEBUG: import pdb; pdb.set_trace()
            return self.reduce(items, "|")
        elif isinstance(node.expr, Not):
            if DEBUG: import pdb; pdb.set_trace()
            return lego_parse('')
        elif isinstance(node.expr, Optional):
            if DEBUG: import pdb; pdb.set_trace()
            return self.reduce(items, "+")
        elif isinstance(node.expr, ZeroOrMore):
            if DEBUG: import pdb; pdb.set_trace()
            return self.reduce(items, "+")
        elif isinstance(node.expr, OneOrMore):
            if DEBUG: import pdb; pdb.set_trace()
            return self.reduce(items, "+")
        else:
            import pdb; pdb.set_trace()

    def visit__(self, node, items):
        #import pdb; pdb.set_trace()
        return lego_parse('')

    def visit_comment(self, node, items):
        #import pdb; pdb.set_trace()
        return lego_parse('')

    def visit_spaceless_literal(self, node, items):
        return lego_parse(eval('%s'%node.text))

    def visit_reference(self, node, items):
        return self.REWrap(node.text.strip())

    def visit_attr_label(self, node, items):
        import pdb; pdb.set_trace()

    def visit_label(self, node, items):
        return lego_parse(node.text.strip())

    def visit_rule(self, node, items):
        import pdb; pdb.set_trace()
        return lego_parse('')

#class Sampler(NodeVisitor):
#
#    class re_wrapper(object):
#        def __init__(self, item):
#            self.item = item
#
#        #def __add__(self,...)
#        #    pass
#
#    def __init__(self):
#        self.re_rules = {}
#
#    def reduce(self, items, op):
#        elems = [i for i in items if isinstance(i, lego)]
#        if len(elems)>1:
#            names = [ "elems[%d]"%idx for idx in range(len(elems))]
#            return eval(op.join(names)).reduce()
#        elif len(elems)==1:
#            return elems[0]
#        else:
#            return []
#
#    def generic_visit(self, node, items):
#        if isinstance(node.expr, Literal):
#            text = node.text
#            print("BB1", text)
#            for schar in schars:
#                text = text.replace(schar, "\\"+schar)
#            print("BB2", text)
#            return re_parse(text)
#        elif isinstance(node.expr, Regex):
#            return re_parse(node.expr.re.pattern)
#        elif isinstance(node.expr, Optional):
#            if len(items)>0:
#                return mult(items[0], qm)
#            else:
#                return []
#        elif isinstance(node.expr, ZeroOrMore):
#            if len(items)>0:
#                return mult(items[0], star)
#            else:
#                return []
#        elif isinstance(node.expr, OneOrMore):
#            if len(items)>0:
#                return mult(items[0], plus)
#            else:
#                return []
#        elif isinstance(node.expr, Sequence):
#            return self.reduce(items, "+")
#        elif isinstance(node.expr, OneOf):
#            return self.reduce(items, "|")
#        elif isinstance(node.expr, Not):
#            return []
#        else:
#            import pdb; pdb.set_trace()
#
#    def visit_label(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_attribute_name(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[0]
#
#    def visit_attribute_items(self, node, items):
#        import pdb; pdb.set_trace()
#        return [items[0], [items[1]]+items[2]]
#
#    def visit_comma_separated_term(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[1]
#
#    def visit_semicolon_separated_part(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[1]
#
#    def visit_attribute_parts(self, node, items):
#        import pdb; pdb.set_trace()
#        return [items[0]]+items[1]
#
#    def visit_expression_attributes_angle(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[2]
#
#    def visit_firstmatch_term(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_firstmatched(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_or_term(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[2]
#
#    def visit_ored(self, node, items):
#        import pdb; pdb.set_trace()
#        return [items[0]]+items[1]
#
#    def visit_left(self, node, items):
#        import pdb; pdb.set_trace()
#        return True if items[0] else None
#
#    def visit_right(self, node, items):
#        import pdb; pdb.set_trace()
#        return True if items[0] else None
#
#    def visit_expression_attributes_brace(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[2]
#
#    def visit_sequence(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_quantified(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_reference(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_spaceless_literal(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[0]
#
#    def visit_blanks(self, node, items):
#        if '\n' in node.text:
#            return re_parse('\n')
#        else:
#            return []
#
#    def visit_comment(self, node, items):
#        return []
#
#    def visit_meaninglessness(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit__(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_literal(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[0]
#
#    def visit_quantifier(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_regex(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_parenthesized(self, node, items):
#        import pdb; pdb.set_trace()
#        return items[2]
#
#    def visit_atom(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_term(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_expression(self, node, items):
#        return self.reduce(items, "+")
#
#    def visit_rule(self, node, items):
#        import pdb; pdb.set_trace()
#
#    def visit_rules(self, node, items):
#        import pdb; pdb.set_trace()
#        #print(node)
#        pass

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

def translate(text):
    grammar = Grammar(myrules)
    parsetree = grammar.parse(text)
    sampler = Sampler().visit(parsetree)
    import pdb; pdb.set_trace()
    #cgrammar = CanonicalGrammar().visit(parsetree)
    #parglare_grammar = translate_to_parglare(cgrammar)
    #parglare_parsers = generate_parglare_parsers(parglare_grammar)



