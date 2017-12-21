##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from .nodes import NodeVisitor

class ParglareConversion(NodeVisitor):

    def __init__(self):
        self.rules = OrderedDict()
        self.rule_prefix = "__rule__%s__%d"

    def generic_visit(self, node, items):
        print("BB", node.text, node.expr, items)
        clsname = node.expr.__class__.__name__.lower()
        return getattr(self, '_'+clsname)(node, items)

    def _literal(self, node, items):
        return ['"%s"'%node.text]

    def _regex(self, node, items):
        return ['/%s/'%node.expr.re.pattern]

    def _optional(self, node, items):
        if items and items[0]:
            name = self.rule_prefix%("opt", len(self.rules))
            self.rules[name] = "%s | EMPTY"%items[0][0]
            return [name]
        else:
            return []

    def _sequence(self, node, items):
        if hasattr(node.expr, 'name') and node.expr.name:
            raise Exception("Named expr should be handled: %s"%node.expr.name)
        l = []
        for item in items:
            l.extend(item)
        return l

    def _oneof(self, node, items):
        return items[0]

    def _zeroormore(self, node, items):
        if items and items[0]:
            return items[0]
        else:
            return []

    def _oneormore(self, node, items):
        if items:
            l = []
            for item in items:
                l.extend(item)
            return [' '.join(l)]
        else:
            return []

    def _not(self, node, items):
        assert not items
        return items

    def visit_rules(self, node, items):
        import pdb; pdb.set_trace()

    def visit_rule(self, node, items):
        import pdb;pdb.set_trace()
        self.rules[items[0][0]] = None
    def visit_expression(self, node, items):
        return items[0]

    def visit_firstmatched(self, node, items):
        l = []
        for item in items:
            l.extend(item)
        return [' '.join(l)]

    def visit_firstmatch_term(self, node, items):
        return ["__//__ %s"%items[0][1]]

    def visit_float(self, node, items):
        import pdb; pdb.set_trace()

    def visit_integer(self, node, items):
        import pdb; pdb.set_trace()

    def visit_right(self, node, items):
        return items[0]

    def visit_left(self, node, items):
        return items[0]

    def visit_semicolon(self, node, items):
        import pdb; pdb.set_trace()

    def visit_comma(self, node, items):
        import pdb; pdb.set_trace()

    def visit_colon(self, node, items):
        return []

    def visit_comment(self, node, items):
        if items[1][0] in self.rules:
            del self.rules[items[1][0]]
        return []

    def visit_vspaces(self, node, items):
        return []

    def visit_hspaces(self, node, items):
        return []

    def visit_label(self, node, items):
        return [node.text.strip()] 

    def visit_quantifier_re(self, node, items):
        import pdb; pdb.set_trace()

    def visit_hex_literal(self, node, items):
        import pdb; pdb.set_trace()

    def visit_octal_literal(self, node, items):
        import pdb; pdb.set_trace()

    def visit_binary_literal(self, node, items):
        import pdb; pdb.set_trace()

    def visit_spaceless_literal(self, node, items):
        return [node.text]

    def visit_digits(self, node, items):
        return [node.text]
        import pdb; pdb.set_trace()

    def visit_number(self, node, items):
        import pdb; pdb.set_trace()

    def visit_blanks(self, node, items):
        return []

    def visit_meaninglessness(self, node, items):
        return []

    def visit__(self, node, items):
        return []

    def visit_attr_label(self, node, items):
        import pdb; pdb.set_trace()

    def visit_literal(self, node, items):
        return items[0]

    def visit_reference(self, node, items):
        return items[0]

    def visit_quantifier(self, node, items):
        import pdb; pdb.set_trace()

    def visit_parenthesized(self, node, items):
        return items[2]

    def visit_regex(self, node, items):
        import pdb; pdb.set_trace()

    def visit_atom(self, node, items):
        return items[0]

    def visit_quantified(self, node, items):
        import pdb; pdb.set_trace()

    def visit_paren_comma_term(self, node, items):
        import pdb; pdb.set_trace()

    def visit_comma_term(self, node, items):
        return items[0]

    def visit_attribute_items(self, node, items):
        return []

    def visit_comma_separated_term(self, node, items):
        import pdb; pdb.set_trace()

    def visit_expression_itemnum(self, node, items):
        return []

    def visit_attribute_name(self, node, items):
        return []

    def visit_attribute_parts(self, node, items):
        return []

    def visit_semicolon_separated_part(self, node, items):
        import pdb; pdb.set_trace()

    def visit_expression_attributes_brace(self, node, items):
        return []

    def visit_expression_attributes_angle(self, node, items):
        import pdb; pdb.set_trace()

    def visit_term(self, node, items):
        return items[0]

    def visit_sequence(self, node, items):
        left = ''
        right = ''
        if items[0]:
            left = '=>'
        if items[3]:
            right = '<='
        assert not (left and right)
        return [left+' '.join(items[1]+items[2])+right]

    def visit_or_term(self, node, items):
        return ["__||__%s"%items[2][0]]

    def visit_ored(self, node, items):
        return [' '.join(items[0]+items[1])]


