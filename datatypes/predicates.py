'''
Created on Dec 27, 2018

@author: meng wu

	
'''

class Predicate(object):

    opCode = ['equal', 'and', 'or', 'xor', 'not',
              'le', 'ge', 'lt', 'gt',
              'add', 'sub', 'mul', 'div', 'rem', 'mod', 'pow']

    opSymbol = ['=', '&', '|', 'xor', '!',
              '<=', '>=', '<', '>',
              '+', '-', '*', '/', '%', 'mod', '^']

    type = ['bool', 'int', 'real', 'intConst', 'realConst']

    def __init__(self, op, type, name, left, right):
        if op in Predicate.opCode:
            self.op = Predicate.opCode.index(op)
        else:
            return -1

        self.left_ = left
        self.right_ = right
        self.name_ = name
        if type in Predicate.type:
            self.type_ = Predicate.type.index(type)
        else:
            return -1

    def initialFromStr(self, preStr):
        if preStr.startwith('('):
            preStr = preStr[preStr.find("(")+1:preStr.find(")")]


    def __repr__(self):
        if self.type_ > 2:
            retVal = self.name_
        else:
            retVal = '(' + self.left_.__repr__() + ') ' + Predicate.opSymbol[self.op] + ' (' + self.right_.__repr__() + ')'
        return retVal
        





