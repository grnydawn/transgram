##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import itertools
from .grammar import Grammar
from .nodes import NodeVisitor
from .expressions import (Literal, Regex, Not, ZeroOrMore,
    OneOrMore, Optional, Sequence, OneOf)
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

schars = ["\\", ".", "^", "$", "*", "+", "?", "{", "}", "[", "]", "|", "(", ")"]
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
            it)) for it in iters)
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

class Label(Internal):
    def __init__(self, label):
        self.name = label

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

    def _escape(self, string):
        for schar in schars:
            string = string.replace(schar, '\\'+schar)
        return string

    def _literal(self, node, items):
        return [lego_parse(self._escape(node.text))]

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

    def generic_visit(self, node, items):
        clsname = node.expr.__class__.__name__.lower()
        return getattr(self, '_'+clsname)(node, items)

    def visit_label(self, node, items):
        return [Label(node.text.strip())]

    def visit_reference(self, node, items):
        return [Reference(node.text.strip())]

    def visit_regex(self, node, items):
        return [lego_parse(eval(node.children[1].text))]

    def visit_literal(self, node, items):
        return [lego_parse(eval(self._escape(node.children[0].text)))]

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
        return []

    def visit_firstmatched(self, node, items):
        return [FirstmatchOf(node, items)]

    def visit_firstmatch_term(self, node, items):
        return items[0][2:]

    def visit_ored(self, node, items):
        return [AnymatchOf(node, items)]

    def visit_or_term(self, node, items):
        return items[0][2:]

    def visit_rule(self, node, items):
        rulename = items[0][0].name
        self.rules[rulename] = items[3]
        return [(rulename, node.start)]

    def visit_rules(self, node, items):
        start_rule = items[1][0][0]
        generators = self.Generator(self.rules, start_rule)
        return Article(generators)

    class Generator(object):
        def __init__(self, rules, start_rule, maxloops=3):
            self.rules = dict(rules)
            self.start_rule = start_rule
            self.maxloops = maxloops

        def __iter__(self):
            for gen in self._get_generators(self.start_rule):
                yield gen

        def _get_generators(self, rulename, path={}):

            generators = [[]]

            def _productextend(*items):
                retval = []
                for gen in items[0]:
                    if len(items)>1:
                        for item in _productextend(*items[1:]):
                            retval.append(gen+item)
                    else:
                        retval.append(gen)
                return retval

            if rulename in path:
                path[rulename] -= 1
            else:
                path[rulename] = self.maxloops

            print("BB", rulename, path)
            #import pdb; pdb.set_trace()
#            # handling attributes
#            for item in self.rules[rulename]:
#                if isinstance(item, self.Attribute):
#                    # common attribute handling
#                    if isinstance(item, self.AngleAttribute):
#                        # angle attribute handling
#                        import pdb; pdb.set_trace()
#                    elif isinstance(item, self.BraceAttribute):
#                        # barce attribute handling
#                        import pdb; pdb.set_trace()

            # generate structure for this rule
            for item in self.rules[rulename]:
                if isinstance(item, pattern):
                    generators = _productextend(generators, [[item.strings(otherchar="_OTHER_")]])
                elif isinstance(item, Reference):
                    # depth handling
                    if path[rulename] == self.maxloops:
                        gens = []
                        for nloops in range(self.maxloops):
                            newpath = dict(path)
                            newpath[rulename] = nloops
                            gens.append(self._get_generators(item.name, path=newpath))
                        generators = _productextend(generators, *gens)
                    elif path[rulename] > 0:
                        generators = _productextend(self._get_generators(item.name, path=path))
                elif isinstance(item, FirstmatchOf):
                    if path[rulename] > 0:
                        gens = []
                        for _item in item.items:
                            itemid = str(sum([id(o) for o in _item]))
                            if itemid not in self.rules:
                                self.rules[itemid] = _item
                            newpath = dict(path)
                            gens.append(self._get_generators(itemid, path=newpath))
                        generators = _productextend(generators, *gens)
                else:
                    import pdb; pdb.set_trace()
            #print("CC", rulename, path, generators)
            #import pdb; pdb.set_trace()
            return generators

def translate(custom_grammar):
    new_syntax = Grammar(new_notation)
    grammar_tree = new_syntax.parse(custom_grammar)
    sampler = Sampler().visit(grammar_tree)
    for idx, s in enumerate(sampler.sentences()):
        if idx ==3: break
        print(''.join(s))
    import pdb; pdb.set_trace()
    #cgrammar = CanonicalGrammar().visit(parsetree)
    #parglare_grammar = translate_to_parglare(cgrammar)
    #parglare_parsers = generate_parglare_parsers(parglare_grammar)
