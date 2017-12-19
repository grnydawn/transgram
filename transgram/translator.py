##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import itertools, re, functools, types, math, random
from collections import OrderedDict
from .grammar import Grammar
from .nodes import NodeVisitor
from .lego import parse as lego_parse, pattern
from .hint import Hint
from .parglare import ParglareConversion

DEBUG = False

grammar_notation = (r'''
    # notation for context-free and context-sensitive grammars

    # high-level rules
    rules           = _ rule*
    rule            = LABEL expression_attributes_angle? COLON expression expression_attributes_brace?
    expression      = firstmatched / ored / sequence / term
    firstmatched    = term firstmatch_term+
    firstmatch_term = (SLASH ored) / (SLASH term)
    ored            = term or_term+
    or_term         = VBAR term
    sequence        = LEFT? term term+ RIGHT? expression_attributes_brace?
    term            = quantified / atom

    # expression attributes
    expression_attributes_angle = LANGLE attribute_parts? RANGLE
    expression_attributes_brace = LBRACE attribute_parts? RBRACE
    semicolon_separated_part = SEMICOLON attribute_items
    attribute_parts = attribute_items semicolon_separated_part*
    attribute_name  = attr_label expression_itemnum? COLON
    expression_itemnum= AT DIGITS
    comma_separated_term = COMMA comma_term
    attribute_items = attribute_name? comma_term comma_separated_term*
    comma_term      = LABEL / literal / number / regex / paren_comma_term
    paren_comma_term = LPARAN comma_term RPARAN

    # terms
    quantified      = atom quantifier
    atom            = literal / reference / regex / parenthesized
    #regex           = TILDE SPACELESS_LITERAL ~"[ilmsux]*"i _
    regex           = TILDE SPACELESS_LITERAL _
    parenthesized   = LPARAN expression RPARAN
    quantifier      = QUANTIFIER_RE _
    reference       = LABEL !COLON
    literal         = (SPACELESS_LITERAL / BINARY_LITERAL / OCTAL_LITERAL / HEX_LITERAL) _
    attr_label      = LABEL
    _               = meaninglessness*
    meaninglessness = blanks / comment
    blanks          = HSPACES / VSPACES
    number          = FLOAT / INTEGER
    comment         = SHARP HINT? LINE 

    # regular expressions and basic terms
    DIGITS          = ~"[0-9]+" _
    SPACELESS_LITERAL= ~"u?r?\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\""is /
                        ~"u?r?'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"is
    BINARY_LITERAL  = ~"b\"[01]*\""is
    OCTAL_LITERAL   = ~"o\"[0-7]*\""is
    HEX_LITERAL     = ~"x\"[0-9a-fA-F]*\""is
    QUANTIFIER_RE   = ~"[*+?]"
    LABEL           = ~"[a-zA-Z_][a-zA-Z_0-9]*" _
    HSPACES         = ~r"[ \t]+"
    VSPACES         = ~r"[\r\n\f\v]+"
    SHARP           = "#"
    TILDE           = "~"
    LPARAN          = "(" _
    AT              = "@" _
    RPARAN          = ")" _
    SLASH           = "/" _
    VBAR            = "|" _
    HINT            = ~"hint\s*:"
    LINE            = ~r"[^\r\n]*"
    COLON           = ":" _
    COMMA           = "," _
    SEMICOLON       = ";" _
    LEFT            = "=>" _
    RIGHT           = "<=" _
    LANGLE          = "<" _
    RANGLE          = ">" _
    LBRACE          = "{" _
    RBRACE          = "}" _
    INTEGER         = ~r"[-+]?[0-9]+" _
    FLOAT           = ~r"[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?" _
''')

grammar_syntax = Grammar(grammar_notation)

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


##### sampler
class Sampler(NodeVisitor):

    def __init__(self):
        self.rules = OrderedDict()
        self.rule_prefix = "__rule__%d"
        self.hint_multiline = []

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

    def visit_COMMA(self, node, items):
        return items[0]

    def visit_SEMICOLON(self, node, items):
        return items[0]

    def visit_LABEL(self, node, items):
        return [Label(node.text.strip())]

    def visit_reference(self, node, items):
        return [Reference(node.text.strip())]

    def visit_regex(self, node, items):
        return [lego_parse(eval(node.children[1].text))]

    def visit_SPACELESS_LITERAL(self, node, items):
        return [LiteralString(eval(node.text))]

    def visit_BINARY_LITERAL(self, node, items):
        return [LiteralBin(node.text[2:-1])]

    def visit_OCTAL_LITERAL(self, node, items):
        return [LiteralOct(node.text[2:-1])]

    def visit_HEX_LITERAL(self, node, items):
        return [LiteralHex(node.text[2:-1])]

    def visit_literal(self, node, items):
        return items[0]

    def visit_parenthesized(self, node, items):
        return items[1]

    def visit_blanks(self, node, items):
        ch = ''
        if node.text:
            ch = r'\n' if node.text.find('\n')>=0 else r' '
        if ch:
            return [lego_parse(ch)]
        else:
            return []

    def visit_comment(self, node, items):
        # TODO: add start and stop data for line checking
        if items[1]:
            hint_string = node.children[2].text.strip()
            if hint_string and hint_string[-1] == "\\":
                self.hint_multiline.append(hint_string[:-1])
            else:
                self.hint_multiline.append(hint_string)
                hint = Hint(''.join(self.hint_multiline))
                self.rules[self.rule_prefix%len(self.rules)] = hint
                self.hint_multiline = []
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
        return ["@", int(node.children[1].text)]

    def visit_attribute_items(self, node, items):
        return [items[0], items[1]+[i for i in items[2] if i != ","]]

    def _attr_brace(self, node, items, default_name, attr_class):

        attrs = {}
        semicolon_items = []

        def _getitems(sitems):
            name = default_name,
            num = 0
            attr_name, opts = sitems
            if attr_name:
                name = attr_name[0].name.strip()
                if "@" in attr_name:
                    num = attr_name[2]
            if name not in attrs:
                attrs[name] = {}
            if num not in attrs[name]:
                attrs[name][num] = []
            attrs[name][num].extend(opts)
            del sitems[:]

        for flag in items[1]:
            if flag == ";":
                _getitems(semicolon_items)
            else:
                semicolon_items.append(flag)
        if semicolon_items:
            _getitems(semicolon_items)

        return [attr_class(attrs)]

    def visit_expression_attributes_brace(self, node, items):
        return self._attr_brace(node, items, "filter", BraceAttribute)

    def visit_expression_attributes_angle(self, node, items):
        return self._attr_brace(node, items, "action", AngleAttribute)

    def visit_QUANTIFIER_RE(self, node, items):
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

    def visit_term(self, node, items):
        return items[0]

    def visit_firstmatched(self, node, items):
        return [FirstmatchOf(node, [items[0]]+items[1])]

    def visit_firstmatch_term(self, node, items):
        return [items[0][2:]]

    def visit_ored(self, node, items):
        return [AnymatchOf(node, [items[0]]+items[1])]

    def visit_or_term(self, node, items):
        return [items[1]]

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
        sample_kwargs = {}
        rules = [r for r in self.rules.items()]
        pairs = zip(rules[:-1], rules[1:])
        for (pname, prule), (nname, nrule) in pairs:
            if isinstance(prule, Hint):
                hints = prule.collect(modes="sample")
                if 'maxrepeats' in hints:
                    sample_kwargs['maxrepeats'] = hints['maxrepeats']
                if 'maxloops' in hints:
                    sample_kwargs['maxloops'] = hints['maxloops']
                if 'randomize' in hints:
                    sample_kwargs['randomize'] = hints['randomize']
            elif isinstance(nrule, Hint): #and the same line, then inline hint
                import pdb; pdb.set_trace()
                pass

        start_rule = items[1][0][0]
        for x in Generator(self.rules, start_rule, **sample_kwargs).generate():
            for y in itertools.product(*x):
                yield ''.join(y)


class Generator(object):
    def __init__(self, rules, start_rule, maxloops=5, maxrepeats=2, randomize=1):
        self.rules = dict(rules)
        self.start_rule = start_rule
        self.maxloops = maxloops
        self.maxrepeats = maxrepeats
        self.randomize = randomize

    def generate(self):

        if self.randomize > 0:
            random.seed(None)
        else:
            random.seed(len(self.start_rule))

        start_rules = [[({self.start_rule:self.maxloops}, r) for r in self.rules[self.start_rule]]]
        while start_rules:
            if DEBUG: print("Rules", start_rules)

            if self.randomize > 3:
                start_rule_stack = start_rules.pop(random.randint(0,len(start_rules)-1))
            else:
                start_rule_stack = start_rules.pop(0)

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
                    if self.randomize > 2:
                        random.shuffle(items)
                    elif self.randomize > 1:
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
                    if self.randomize > 0:
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
    grammar_tree = grammar_syntax.parse(custom_grammar)
    for idx, s in enumerate(Sampler().visit(grammar_tree)):
        print(''.join(s))
    #parglare_grammar = ParglareConversion().visit(grammar_tree)
    #import pdb; pdb.set_trace()
    
    #parglare_parsers = generate_parglare_parsers(parglare_grammar)
    #if multiple parsers, then take one sample from generations
    #and parse using the parsers and see where they diverge
