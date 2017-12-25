##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from parsimonious import NodeVisitor
from parsimonious.expressions import Literal
import sys
sys.path.append("/home/ashley/repos/github/click")
sys.path.append("/home/ashley/repos/github/parglare")

from parglare import Grammar, GLRParser, Parser

# NOTE: may accept only double quote for literals

# TODO1: debugging with samples having parentheses
# TODO2: regex instance variable ~label. Two step parser generation to decide ~label
# TODO3: Context class having rule_stack and regex instance variable resolutions
# TODO2-1: General instance variable whose content is used to choose proper expression
# TODO4: tree reordering or user-directed restructuring
# TODO5: Need to come up with mixing code possibly related with TODO4(resolve: cluttred and confused)
# TODO6: Mixing grammar such as c code having assembly code(like Perl6?)
# TODO7: Keyword support that having word boundary
# TODO8: How to introduce assertions ( & and ! in PEG)?
# TODOX: DO magical things with easily understandable ways

class ParglareConverter(NodeVisitor):

    TAB = ' '*4

    def __init__(self):
        self.rules = OrderedDict()
    
    def grammar(self):
        l = []
        for name, rule in self.rules.items():
            l.append("%s :\n%s"%(name, self.TAB))
            for term in rule:
                if term == "|":
                    l.append(" \n%s%s"%(self.TAB, term))
                elif term == ";":
                    l.append(" %s\n"%term)
                else:
                    l.append(" %s"%term)
        return ''.join(l)

    def generic_visit(self, node, items):
        if isinstance(node.expr, Literal):
            return [node.text.strip()]
        else:
            l = []
            for item in items:
                l.extend(item)
            return l

    def visit_rule(self, node, items):
        terms = [";"]
        P = 10
        BAR = True
        for term in reversed(items[3]):
            if term == "/":
                P += 10
                term = "|"
                BAR = True
            elif "__priority__" in term:
                term = term.replace("__priority__", "%d"%P)
                BAR = False
            elif BAR:
                if len(term)<2 or term[0]!="/" and term[-1]!="/":
                    terms.append(" {%d}"%P)
                BAR = False
            terms.append(term)
        self.rules[items[0][0]] = [t for t in reversed(terms)]
        return []

    def visit_expression_attributes_angle(self, node, items):
        return []

    def visit_expression_attributes_brace(self, node, items):
        return []

    def visit_firstmatched(self, node, items):
        if items[0][0] == "(" and items[0][-1] == ")":
            del items[0][-1]
            del items[0][0]
        return items[0]+items[1]

    def visit_firstmatch_term(self, node, items):
        if items[0][1] == "(" and items[0][-1] == ")":
            del items[0][-1]
            del items[0][1]
        return items[0]

    def visit_ored(self, node, items):
        if items[0][0] == "(" and items[0][-1] == ")":
            del items[0][-1]
            del items[0][0]
        return items[0]+items[1]

    def visit_or_term(self, node, items):
        if items[1][0] == "(" and items[1][-1] == ")":
            del items[1][-1]
            del items[1][0]
        return items[0]+items[1]

    def visit_sequence(self, node, items):
        assert not (items[0] and items[3])
        direct = ""
        if items[0]:
            direct = "left, "
        if items[3]:
            direct = "right, "
        return items[1]+items[2]+[" {%s__priority__}"%direct]

    #def visit_term(self, node, items):
    #    l = []
    #    for item in items:
    #        l.extend(item)
    #    return l

    def visit_label(self, node, items):
        return [node.text.strip()]

    def visit_regex(self, node, items):
        return ["/%s/"%node.children[1].text[1:-1]]

    def visit_quantified(self, node, items):
        l = []
        for item in items:
            l.extend(item)
        return [''.join(l)]

    def visit_quantifier(self, node, items):
        return [node.text.strip()]

    def visit_SPACELESS_LITERAL(self, node, items):
        return [node.text.strip()]

    def visit_BINARY_LITERAL(self, node, items):
        raise NotImplementedError("Binary literal is not supported yet: '%s'."%node.text)

    def visit_OCTAL_LITERAL(self, node, items):
        raise NotImplementedError("Octal literal is not supported yet: '%s'."%node.text)

    def visit_HEX_LITERAL(self, node, items):
        raise NotImplementedError("Hex literal is not supported yet: '%s'."%node.text)

def generate_parglare_parser(grammar):
    g = Grammar.from_string(grammar)
    parser = GLRParser(g, ws=None)
    #parser = Parser(g)
    return parser
