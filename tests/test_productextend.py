from context import transgram
import unittest, sys, os, itertools, functools

here = os.path.dirname(os.path.realpath(__file__))

def _productextend(*items):
#                temp = []
#                for gen in items[0]:
#                    if len(items)>1:
#                        for item in _productextend(*items[1:]):
#                            import pdb; pdb.set_trace()
#                            temp.append(gen+item)
#                    else:
#                        temp.append(gen)
#                return temp

    if len(items)>1:
        temp = []
        for item in itertools.product(items[0], _productextend(*items[1:])):
            temp.append(functools.reduce(lambda x,y: x+y, item))
    else:
        return items[0]
    return temp

data1 = [1, 2, 3]
data2 = ['a', 'b', 'c']
data3 = ['x', 'y', 'z']
data4 = []
data5 = [4.0, 5.0, 6.0]
data6 = [{}, (), []]

item1 = [ data1, data2 ]
item2 = [ data3, data4 ]
item3 = [ data5, data6 ]

class TestParser(unittest.TestCase):

    def test_productextend1(self):
        items = [ item1, item2, item3]
        print('ITEMS: ', *items)
        output = _productextend(*items)
        print('OUTPUT: ', output)

    def test_productextend2(self):
        items = [ [[]], item1, item2]
        print('ITEMS: ', *items)
        output = _productextend(*items)
        print('OUTPUT: ', output)

    def test_productextend3(self):
        items = [ [[]], [[1],[2]]]
        print('ITEMS: ', *items)
        output = _productextend(*items)
        print('OUTPUT: ', output)

if __name__ == '__main__':
    unittest.main.main()


