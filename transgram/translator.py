##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import itertools, re, functools, types, math, random
from collections import OrderedDict
from .grammar import Grammar
from .nodes import NodeVisitor
from .lego import parse as lego_parse, pattern

DEBUG = False

new_notation = (r'''
    # notation for context-free and context-sensitive grammars

    # high-level rules
    rules           = _ rule*
    rule            = label expression_attributes_angle? colon expression expression_attributes_brace?
    expression      = firstmatched / ored / sequence / term
    firstmatched    = term firstmatch_term+
    firstmatch_term = ("/" _ ored) / ("/" _ term)
    ored            = term or_term+
    or_term         = "|" _ term
    sequence        = left? term term+ right? expression_attributes_brace?
    term            = quantified / atom

    # expression attributes
    expression_attributes_angle = "<" _ attribute_parts? ">" _
    expression_attributes_brace = "{" _ attribute_parts? "}" _
    semicolon_separated_part = semicolon attribute_items
    attribute_parts = attribute_items semicolon_separated_part*
    attribute_name  = attr_label expression_itemnum? colon
    expression_itemnum= "@" _ digits
    comma_separated_term = comma comma_term
    attribute_items = attribute_name? comma_term comma_separated_term*
    comma_term      = label / literal / number / regex / paren_comma_term
    paren_comma_term = "(" _ comma_term ")" _

    # terms
    quantified      = atom quantifier
    atom            = literal / reference / regex / parenthesized
    #regex           = "~" spaceless_literal ~"[ilmsux]*"i _
    regex           = "~" spaceless_literal _
    parenthesized   = "(" _ expression ")" _
    quantifier      = quantifier_re _
    reference       = label !colon
    literal         = (spaceless_literal / binary_literal / octal_literal / hex_literal) _
    attr_label      = label
    _               = meaninglessness*
    meaninglessness = blanks / comment
    blanks          = hspaces / vspaces
    number          = float / integer

    # regular expressions and basic terms
    digits          = ~"[0-9]+" _
    spaceless_literal= ~"u?r?\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\""is /
                        ~"u?r?'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"is
    binary_literal  = ~"b\"[01]*\""is
    octal_literal   = ~"o\"[0-7]*\""is
    hex_literal     = ~"x\"[0-9a-fA-F]*\""is
    quantifier_re   = ~"[*+?]"
    label           = ~"[a-zA-Z_][a-zA-Z_0-9]*" _
    hspaces         = ~r"[ \t]+"
    vspaces         = ~r"[\r\n\f\v]+"
    comment         = "#" ~"hint\s*:"? ~r"[^\r\n]*"
    colon           = ":" _
    comma           = "," _
    semicolon       = ";" _
    left            = "=>" _
    right           = "<=" _
    integer         = ~r"[-+]?[0-9]+" _
    float           = ~r"[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?" _
''')

DEBUG = False

###### internal classes #####

class Internal(object):
    pass

class Reference(Internal):
    def __init__(self, ref):
        self.name = ref

    def __str__(self):
        return '"%s"'%self.name

class Label(Internal):
    def __init__(self, label):
        self.name = label

class Literal(Internal):
    def __init__(self, elements):
        self.elements = elements

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.elements == other.elements
        elif isinstance(other, str):
            return self.elements == other

    def __iter__(self):
        yield self.elements

    def copy(self):
        return self.__class__(self.elements)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '"%s"'%self.elements

class LiteralString(Literal):
    pass

class LiteralBin(Literal):
    pass

class LiteralOct(Literal):
    pass

class LiteralHex(Literal):
    pass

class Quantified(Internal):
    def __init__(self, item, start, end):
        self.item = item
        self.start = start
        self.end = end

class Optional(Quantified):
    def __init__(self, item):
        super(Optional, self).__init__(item, 0, math.inf)

class ZeroOrMore(Quantified):
    def __init__(self, item):
        super(ZeroOrMore, self).__init__(item, 0, math.inf)

class OneOrMore(Quantified):
    def __init__(self, item):
        super(OneOrMore, self).__init__(item, 1, math.inf)

class LeftAssociative(Internal):
    def __str__(self):
        return '"=>"'

class RightAssociative(Internal):
    def __str__(self):
        return '"<="'

class Attribute(Internal):
    def __init__(self, attrs):
        self.attrs = attrs

class AngleAttribute(Attribute):
    pass

class BraceAttribute(Attribute):
    pass

class Iterator(Internal):
    # as generator
    def __init__(self, node, items):
        self.node = node
        self.items = items

class FirstmatchOf(Iterator):
    pass

class AnymatchOf(Iterator):
    pass


class Hint(Internal):
    def __init__(self, sentence):
        self.sentence = sentence

##### sampler
class Sampler(NodeVisitor):

    def __init__(self):
        self.rules = OrderedDict()
        self.rule_prefix = "__rule__%d"

    def generic_visit(self, node, items):
        clsname = node.expr.__class__.__name__.lower()
        return getattr(self, '_'+clsname)(node, items)

    def _literal(self, node, items):
        return [LiteralString(node.text)]

    def _regex(self, node, items):
        return [lego_parse(node.expr.re.pattern)]

    def _sequence(self, node, items):
        l = []
        for item in items:
            l.extend(item)
        return l

    def _optional(self, node, items):
        return items[0] if items else items

    def _oneof(self, node, items):
        assert len(items) == 1
        return items[0]

    def _zeroormore(self, node, items):
        return self._sequence(node, items)

    def _oneormore(self, node, items):
        return self._sequence(node, items)

    def _not(self, node, items):
        return []

    def visit_label(self, node, items):
        return [Label(node.text.strip())]

    def visit_reference(self, node, items):
        return [Reference(node.text.strip())]

    def visit_regex(self, node, items):
        return [lego_parse(eval(node.children[1].text))]

    def visit_spaceless_literal(self, node, items):
        return [LiteralString(eval(node.text))]

    def visit_binary_literal(self, node, items):
        return [LiteralBin(node.text[2:-1])]

    def visit_octal_literal(self, node, items):
        return [LiteralOct(node.text[2:-1])]

    def visit_hex_literal(self, node, items):
        return [LiteralHex(node.text[2:-1])]

    def visit_literal(self, node, items):
        return items[0]

    def visit_parenthesized(self, node, items):
        return items[2]

    def visit_blanks(self, node, items):
        ch = ''
        if node.text:
            ch = r'\n' if node.text.find('\n')>=0 else r' '
        if ch:
            return [lego_parse(ch)]
        else:
            return []

    def visit_comment(self, node, items):
        if items[1]:
            hint = Hint(node.children[2].text)
            self.rules[self.rule_prefix%len(self.rules)] = hint
        return []

    def visit_sequence(self, node, items):

        left = False
        right = False
        if len(items[0]) > 0 and items[0][0] == "=>":
            left = True
        if len(items[-2]) > 0 and items[-2][0] == "<=":
            right = True
        if left and right:
            raise Exception("Can not be both of left and right associative.")
        elif not left and not right:
            left = True

        terms = items[1]+items[2]
        if items[4]:
            attrs = items[4][0].attrs
            if "string" in attrs:
                if 0 in attrs["string"]:
                    for i in range(len(terms)):
                        terms[i] = attrs["string"][0][0]
                for i in range(len(terms)):
                    if i+1 in attrs["string"]:
                        terms[i] = attrs["string"][i+1][0]

        # removed attribute on completing all required actions
        return terms

    def visit_expression_itemnum(self, node, items):
        return ["@", int(node.children[2].text)]

    def visit_attribute_items(self, node, items):
        return [items[0], items[1]+[i for i in items[2] if i != ","]]

    def _attr_brace(self, node, items, default_name, attr_class):

        attrs = {}
        semicolon_items = []

        def _getitems():
            name = default_name,
            num = 0
            attr_name, opts = semicolon_items
            if attr_name:
                name = attr_name[0].name.strip()
                if "@" in attr_name:
                    num = attr_name[2]
            if name not in attrs:
                attrs[name] = {}
            if num not in attrs[name]:
                attrs[name][num] = []
            attrs[name][num].extend(opts)

        for flag in items[2]:
            if flag == ";":
                _getitems()
            else:
                semicolon_items.append(flag)
        if semicolon_items:
            _getitems()

        return [attr_class(attrs)]

    def visit_expression_attributes_brace(self, node, items):
        return self._attr_brace(node, items, "filter", BraceAttribute)

    def visit_expression_attributes_angle(self, node, items):
        return self._attr_brace(node, items, "action", AngleAttribute)

    def visit_quantifier_re(self, node, items):
        return [node.text]

    def visit_quantifier(self, node, items):
        return items[0]

    def visit_quantified(self, node, items):
        if items[1][0] == "?":
            return [Optional(items[0])]
        elif items[1][0] == "+":
            return [OneOrMore(items[0])]
        elif items[1][0] == "*":
            return [ZeroOrMore(items[0])]

    def visit_firstmatched(self, node, items):
        return [FirstmatchOf(node, [items[0]]+items[1])]

    def visit_firstmatch_term(self, node, items):
        return [items[0][2:]]

    def visit_ored(self, node, items):
        return [AnymatchOf(node, [items[0]]+items[1])]

    def visit_or_term(self, node, items):
        return [items[2]]

    def visit_rule(self, node, items):
        if items[4]:
            attrs = items[4][0].attrs
            terms = items[3][:]
            if "string" in attrs:
                if 0 in attrs["string"]:
                    for i in range(len(terms)):
                        terms[i] = attrs["string"][0][0]
                for i in range(len(terms)):
                    if i+1 in attrs["string"]:
                        terms[i] = attrs["string"][i+1][0]
            items[3] = terms

        rulename = items[0][0].name
        self.rules[rulename] = items[3]
        return [(rulename, node.start)]

    def visit_rules(self, node, items):

        # hint processing
        rules = [r for r in self.rules.items()]
        pairs = zip(rules[:-1], rules[1:])
        for (pname, prule), (nname, nrule) in pairs:
            if isinstance(prule, Hint):
                #import pdb; pdb.set_trace()
                pass
        start_rule = items[1][0][0]
        for x in Generator(self.rules, start_rule, randomize=False).generate():
            for y in itertools.product(*x):
                yield ''.join(y)


class Generator(object):
    def __init__(self, rules, start_rule, maxloops=5, maxrepeats=2, randomize=None):
        self.rules = dict(rules)
        self.start_rule = start_rule
        self.maxloops = maxloops
        self.maxrepeats = maxrepeats
        self.randomize = randomize

    def generate(self):

        if self.randomize is True:
            random.seed(None)
        else:
            random.seed(len(self.start_rule))

        start_rules = [[({self.start_rule:self.maxloops}, r) for r in self.rules[self.start_rule]]]
        while start_rules:
            if DEBUG: print("Rules", start_rules)

            if self.randomize is True:
                start_rule_stack = start_rules.pop(random.randint(0,len(start_rules)-1))
            else:
                start_rule_stack = start_rules.pop()

            bucket = []
            while start_rule_stack:
                if DEBUG: print("Stack", start_rule_stack)
                path, item = start_rule_stack.pop()
                if DEBUG: print("Item", item)
                if isinstance(item, Reference):
                    if DEBUG: print("Ref", item.name)
                    if item.name in path:
                        path[item.name] -= 1
                    else:
                        path[item.name] = self.maxloops
                    if path[item.name] > 0:
                        start_rule_stack.extend([(dict(path),i) for i in self.rules[item.name]])
                    else:
                        bucket = []
                        start_rule_stack = []
                elif isinstance(item, Literal):
                    if DEBUG: print("Literal", item.elements)
                    bucket.append((dict(path), item))
                elif isinstance(item, pattern):
                    if DEBUG: print("RE", str(item))
                    bucket.append((dict(path), item))
                elif isinstance(item, FirstmatchOf):
                    if DEBUG: print("FirstmatchOf", )
                    items = item.items[:]
                    if self.randomize is True:
                        random.shuffle(items)
                    elif self.randomize is None:
                        for _ in range(random.randint(0,len(items))):
                            items.append(items.pop(0))
                    for _i in items[1:]:
                        if DEBUG: print("_Item", _i)
                        _pair = [(path, p) for p in _i]
                        bucket_copy = [(x,y.copy()) for x,y in reversed(bucket)]
                        start_rules.append(start_rule_stack[:]+_pair+bucket_copy)
                    start_rule_stack.extend([(path,i) for i in items[0]])
                elif isinstance(item, AnymatchOf):
                    if DEBUG: print("AnymatchOf", )
                    shuffled = item.items[:]
                    if not self.randomize is False:
                        random.shuffle(shuffled)
                    for _i in shuffled[1:]:
                        if DEBUG: print("_Item", _i)
                        _pair = [(path, p) for p in _i]
                        bucket_copy = [(x,y.copy()) for x,y in reversed(bucket)]
                        start_rules.append(start_rule_stack[:]+_pair+bucket_copy)
                    start_rule_stack.extend([(path,i) for i in shuffled[0]])

                elif isinstance(item, Optional):
                    if DEBUG: print("Optional", item)
                    bucket_copy = [(x,y.copy()) for x,y in reversed(bucket)]
                    start_rules.append(start_rule_stack[:]+item.item[:]+bucket_copy)
                elif isinstance(item, ZeroOrMore):
                    if DEBUG: print("ZeroOrMore", item)
                    buf = []
                    for _ in range(self.maxrepeats):
                        buf.extend([(path, i) for i in item.item])
                        bucket_copy = [(x,y.copy()) for x,y in reversed(bucket)]
                        start_rules.append(start_rule_stack[:]+buf[:]+bucket_copy)
                elif isinstance(item, OneOrMore):
                    if DEBUG: print("OneOrMore", item)
                    buf = [(path, i) for i in item.item]
                    for _ in range(self.maxrepeats-1):
                        buf += [(path, i) for i in item.item]
                        bucket_copy = [(x,y.copy()) for x,y in reversed(bucket)]
                        start_rules.append(start_rule_stack[:]+buf[:]+bucket_copy)
                    start_rule_stack.extend([(path,i) for i in item.item])
                else:
                    import pdb; pdb.set_trace()
                    pass
            if bucket:
                yield [z for z in reversed([y.copy() for x,y in bucket])]

def translate(custom_grammar):
    new_syntax = Grammar(new_notation)
    grammar_tree = new_syntax.parse(custom_grammar)
    for idx, s in enumerate(Sampler().visit(grammar_tree)):
        #if idx ==10: break
        print(''.join(s))
        #import pdb; pdb.set_trace()
    #import pdb; pdb.set_trace()
    #cgrammar = CanonicalGrammar().visit(parsetree)
    #parglare_grammar = translate_to_parglare(cgrammar)
    #parglare_parsers = generate_parglare_parsers(parglare_grammar)
    #if multiple parsers, then take one sample from generations
    #and parse using the parsers and see where they diverge
