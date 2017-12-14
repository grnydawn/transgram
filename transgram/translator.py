##-*- coding: utf-8 -*-
#from __future__ import absolute_import, division, print_function, unicode_literals
import itertools, re, functools, types
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

    def strings(self, **kwargs):
        yield self.string

    def copy(self):
        return self.__class__(self.string)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '"%s"'%self.string

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

    def visit_firstmatched(self, node, items):
        return [FirstmatchOf(node, [items[0]]+items[1])]

    def visit_firstmatch_term(self, node, items):
        return [items[0][2:]]

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
        return self.Generator(self.rules, start_rule)
        #generators = self.Generator(self.rules, start_rule)
        #return Article(generators)

    class Generator(object):
        def __init__(self, rules, start_rule, maxloops=3):
            self.rules = dict(rules)
            self.start_rule = start_rule
            self.maxloops = maxloops
            self.barrel = self._generate()

        def _generate(self):
            barrel = []
            stack = [self.rules[self.start_rule][:]]
            while stack:
                node = stack.pop()
                bucket = []
                while node:
                    print("Node", node)
                    item = node.pop()
                    print("Item", item)
                    if isinstance(item, Reference):
                        node.extend(self.rules[item.name][:])
                    elif isinstance(item, LiteralString):
                        bucket.append(item)
                    elif isinstance(item, pattern):
                        bucket.append(item)
                    elif isinstance(item, FirstmatchOf):
                        node.extend(item.items[0][:])
                        for _i in item.items[1:]:
                            new_bucket = [x.copy() for x in reversed(bucket)]
                            stack.append(node[:]+_i[:]+new_bucket)
                    elif isinstance(item, types.GeneratorType):
                        bucket.append(item)
                    else:
                        import pdb; pdb.set_trace()
                        pass
                if bucket:
                    barrel.append(reversed([x.copy() for x in bucket]))
            return barrel

#
#        def _generate(self):
#            barrel = []
#            sstack = [[self.rules[self.start_rule]]]
#            while sstack:
#                print("SStack", sstack)
#                stack = sstack.pop()
#                bucket = []
#                while stack:
#                    print("Stack", stack)
#                    node = stack.pop()
#                    if isinstance(node, list):
#                        while node:
#                            print("Node", node)
#                            item = node.pop()
#                            print("Item", item)
#                            if isinstance(item, Reference):
#                                stack.append(self.rules[item.name])
#                            elif isinstance(item, (LiteralString, pattern)):
#                                stack.append(item.strings())
#                            elif isinstance(item, FirstmatchOf):
#                                stack.append(item.items[0])
#                                for _i in item.items[1:]:
#                                   sstack.append(node+[_i])
#                            else:
#                                import pdb; pdb.set_trace()
#                                pass
#                    elif node:
#                        bucket.append(node)
#                if bucket:
#                    barrel.append(bucket)
#            return barrel
#



        def __iter__(self):
            for bucket in self.barrel:
                for bottles in itertools.product(*bucket):
                        yield bottles

#    class Generator(object):
#        def __init__(self, rules, start_rule, maxloops=3):
#            self.rules = dict(rules)
#            self.start_rule = start_rule
#            self.maxloops = maxloops
#
#        def __iter__(self):
#            for gen in self._get_generators(self.start_rule):
#                yield gen
#
#        def _get_generators(self, rulename, path={}):
#
#            generators = [[]]
#
#            def _trimgenerators(generators):
#                newgens = []
#                for gen in generators:
#                    if all(item is not None for item in gen):
#                        newgens.append(gen)
#                if len(newgens) == 0:
#                    newgens.append([None])
#                return newgens
#
#            def _productextend(*items):
#                if len(items)>1:
#                    temp = []
#                    for item in itertools.product(items[0], _productextend(*items[1:])):
#                        try:
#                            temp.append(functools.reduce(lambda x,y: x+y, item))
#                        except Exception as err:
#                            import pdb; pdb.set_trace()
#                else:
#                    return items[0]
#                return temp
#
#            #print("AA", rulename, path)
#
#            #import pdb; pdb.set_trace()
##            # handling attributes
##            for item in self.rules[rulename]:
##                if isinstance(item, self.Attribute):
##                    # common attribute handling
##                    if isinstance(item, self.AngleAttribute):
##                        # angle attribute handling
##                        import pdb; pdb.set_trace()
##                    elif isinstance(item, self.BraceAttribute):
##                        # barce attribute handling
##                        import pdb; pdb.set_trace()
#
#            # generate structure for this rule
#            for item in self.rules[rulename]:
#                if isinstance(item, pattern):
#                    generators = _productextend(generators, [[item.copy()]])
#                elif isinstance(item, LiteralString):
#                    generators = _productextend(generators, [[item.copy()]])
#                elif isinstance(item, Reference):
#                    subgen = self._get_generators(item.name, path=path)
#                    generators = _productextend(generators, subgen)
#                elif isinstance(item, FirstmatchOf):
#                    itemgens = []
#                    for _item in item.items:
#                        itemid = str(sum([id(o) for o in _item]))
#                        if itemid not in self.rules:
#                            self.rules[itemid] = _item
#
#                        if itemid not in path:
#                            path[itemid] = self.maxloops
#
#                        if path[itemid] == self.maxloops:
##                            for nloops in range(self.maxloops):
##                                newpath = dict(path)
##                                newpath[itemid] = nloops
##                                subgen = self._get_generators(itemid, path=newpath)
##                                itemgens.append(subgen)
#
#                            newpath = dict(path)
#                            #newpath[itemid] = self.maxloops - 1
#                            newpath[itemid] = 1
#                            subgen = self._get_generators(itemid, path=newpath)
#                            itemgens.append(subgen)
#                        elif path[itemid] > 0:
#                            path[itemid] -= 1
#                            subgen = self._get_generators(itemid, path=path)
#                            itemgens.append(subgen)
#                        else:
#                            itemgens.append([None])
#                    itemgens = _trimgenerators(itemgens)
#                    #import pdb; pdb.set_trace()
#                    #for itemgen in itemgens:
#                    #    generators = _productextend(generators, itemgen)
#                    generators = _productextend(generators, *itemgens)
#                else:
#                    import pdb; pdb.set_trace()
#            #print("CC1", rulename, path, generators)
#            #print("CC", rulename, len(generators))
#            #import pdb; pdb.set_trace()
#            generators = _trimgenerators(generators)
#            #print("CC2", rulename, path, generators)
#            return generators

def translate(custom_grammar):
    new_syntax = Grammar(new_notation)
    grammar_tree = new_syntax.parse(custom_grammar)
    sampler = Sampler().visit(grammar_tree)
    for s in sampler:
        #if idx ==3: break
        print(''.join(s))
        #import pdb; pdb.set_trace()
    #import pdb; pdb.set_trace()
    #cgrammar = CanonicalGrammar().visit(parsetree)
    #parglare_grammar = translate_to_parglare(cgrammar)
    #parglare_parsers = generate_parglare_parsers(parglare_grammar)
