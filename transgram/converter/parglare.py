##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from ..nodes import NodeVisitor
from ..expressions import Literal

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
                    l.append(" %s\n%s"%(term,self.TAB))
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
                terms.append(" {%d, left}"%P)
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
        direct = "left"
        if items[3]:
            direct = "right"
        return items[1]+items[2]+[" {__priority__, %s}"%direct]

    def visit_label(self, node, items):
        return [node.text.strip()]

    def visit_regex(self, node, items):
        return ["/%s/"%node.text.strip()[2:-1]]

    def visit_literal(self, node, items):
        return [node.text.strip()]
