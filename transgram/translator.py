##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import itertools, re, functools, types, math, random
from .grammar import Grammar
from .nodes import NodeVisitor
from .lego import parse as lego_parse, pattern

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
    quantifier      = quantifier_re _
    quantifier_re   = ~"[*+?]"
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

#schars = ["\\", ".", "^", "$", "*", "+", "?", "{", "}", "[", "]", "|", "(", ")"]
DEBUG = False

class Article(object):

    def __init__(self, structure):
        self.structure = structure
        #self.generator = self.product(*self.structure, otherchar="_otherchar_")

    def sentences(self):
        # generate structures
        # sort by some ways
        # get one by one
        for struct in self.structure:
            for s in self.product(*struct, otherchar="_otherchar_"):
                yield s

    # from https://bugs.python.org/issue10109
    def product(self, *iters, **kwargs):
        otherchar = kwargs.get('otherchar', None)
        inf_iters = tuple(itertools.cycle(enumerate(
            it.strings(otherchar=otherchar))) for it in iters)
        num_iters = len(inf_iters)
        cur_val = [None for _ in range(num_iters)]

        first_v = True
        while True:
            i, p = 0, num_iters
            while p and not i:
                p -= 1
                #i, cur_val[p] = inf_iters[p].next()
                i, cur_val[p] = next(inf_iters[p])

            if not p and not i:
                if first_v:
                    first_v = False
                else:
                    break

            yield tuple(cur_val)


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

class LiteralString(Internal):
    def __init__(self, string):
        self.string = string

    def __iter__(self):
        yield self.string

    def copy(self):
        return self.__class__(self.string)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '"%s"'%self.string

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

class Attribute(Internal):
    pass

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
        self.rules = {}

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

    def visit_literal(self, node, items):
        return [LiteralString(eval(node.children[0].text))]

    def visit_parenthesized(self, node, items):
        return items[2]

    def visit_blanks(self, node, items):
        ch = ''
        if node.text:
            #ch = r'\n' if node.text.find('\n')>=0 else r' '
            ch = r' '
        if ch:
            return [lego_parse(ch)]
        else:
            return []

    def visit_comment(self, node, items):
        return []

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
        rulename = items[0][0].name
        self.rules[rulename] = items[3]
        return [(rulename, node.start)]

    def visit_rules(self, node, items):
        start_rule = items[1][0][0]
        for x in Generator(self.rules, start_rule).generate():
            for y in itertools.product(*x):
                yield ''.join(y)

DEBUG = False

class Generator(object):
    def __init__(self, rules, start_rule, maxloops=6, maxrepeats=2):
        self.rules = dict(rules)
        self.start_rule = start_rule
        self.maxloops = maxloops
        self.maxrepeats = maxrepeats

    def generate(self):
        start_rules = [[({self.start_rule:self.maxloops}, r) for r in self.rules[self.start_rule]]]
        while start_rules:
            if DEBUG: print("Rules", start_rules)
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
                elif isinstance(item, LiteralString):
                    if DEBUG: print("Literal", item.string)
                    bucket.append((dict(path), item))
                elif isinstance(item, pattern):
                    if DEBUG: print("RE", str(item))
                    bucket.append((dict(path), item))
                elif isinstance(item, FirstmatchOf):
                    if DEBUG: print("FirstmatchOf", )
                    for _i in item.items[1:]:
                        if DEBUG: print("_Item", _i)
                        _pair = [(path, p) for p in _i]
                        bucket_copy = [(x,y.copy()) for x,y in reversed(bucket)]
                        start_rules.append(start_rule_stack[:]+_pair+bucket_copy)
                    start_rule_stack.extend([(path,i) for i in item.items[0]])
                elif isinstance(item, AnymatchOf):
                    if DEBUG: print("AnymatchOf", )
                    shuffled = item.items[:]
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
