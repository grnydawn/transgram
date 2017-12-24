from context import transgram
import unittest, sys, os

here = os.path.dirname(os.path.realpath(__file__))
#grammar_test = 'test'
#grammar_test = 'boldtext'
grammar_test = 'expr'
#grammar_test = 'expr_ambi'
#grammar_test = 'expr_new'
#grammar_test = 'expr_old'
grammar_rules = os.path.join(here, 'grammar_%s.txt'%grammar_test)
#sample_input = os.path.join(here, 'sample_%s.txt'%grammar_test)

class TestParser(unittest.TestCase):

    def test_transgram(self):
        with open(grammar_rules, 'r') as fg:
            newgrammar = transgram.translate(fg.read())
            print(newgrammar)

if __name__ == '__main__':
    unittest.main.main()
