'''
Created on Dec 27, 2018

@author: meng wu

	
'''
import re
from z3 import *

class AstNode(object):
    def __init__(self, ty, value):
        self.type_ = ty
        self.value_ = value
        self.left_ = self.right_ = self.parent_ = None

    def __repr__(self):
        if self.type_ < 3 or self.type_ ==4:
            return self.value_

        xstr = lambda s: '' if s is None else s.__repr__()

        return xstr(self.left_) + ' ' + self.value_ + ' ' + xstr(self.right_)

    def setParent(self, parent):
        self.parent_ = parent

    def getParent(self):
        return self.parent_

    def setLeft(self, left):
        self.left_ = left
        left.setParent(self)

    def setRight(self, right):
        self.right_ = right
        right.setParent(self)

    def getLeft(self):
        return self.left_

    def getRight(self):
        return self.right_

    def getType(self):
        return self.type_

    def setType(self, ty):
        self.type_ = ty

    def getValue(self):
        return self.value_

    def setValue(self, val):
        self.value_ = val

    def getLits(self):
        lit = set()
        if self.type_ == 0:
            lit.add(self.value_)
        if self.left_:
            lit = lit.union(self.left_.getLits())
        if self.right_:
            lit = lit.union(self.right_.getLits())
        return lit


class Predicate(object):

    opCode = ['equal', 'and', 'or', 'xor', 'not',
              'le', 'ge', 'lt', 'gt',
              'add', 'sub', 'mul', 'div', 'rem', 'mod', 'pow']

    opSymbol = ['==', '&', '|', 'xor', '!',
              '<=', '>=', '<', '>',
              '+', '-', '*', '/', '%', 'mod', '^']
    type = ['var', 'intConst', 'realConst', 'op', 'parenthesis']

    def __init__(self):
        self.tokens = []
        self.tok = None
        self.nexttok = None
        self.vars = dict()

    def tokenizeAndParse(self, predStr):
        self.tokens = []
        self.tok = None
        self.nexttok = None
        self.tokenize(predStr)
        return self.parse()


    def consume(self):
        self.tok = self.nexttok
        self.nexttok = next(self.tokens, None)

    def accept(self, val):
        if self.nexttok and self.nexttok.getValue() in val:
            self.consume()
            return True
        else:
            return False


    def factor(self):
        # factor := Num | (expr)
        if self.nexttok.getType() < 3:
            self.consume()
            return self.tok
        elif self.nexttok.getType() == 4 and self.nexttok.getValue()=='(':
            self.consume()
            expr = self.expr()
            if self.nexttok.getType() == 4 and self.nexttok.getValue()==')':
                self.consume()
            else:
                raise SyntaxError("expect ')'.")
            return expr
        else:
            raise SyntaxError("expect a factor.")

    def term(self):
        # term := factor {*|/|^|% factor}*
        termval = self.factor()
        termSymbol = ['*', '/', '%', 'mod', '^']
        while self.accept(termSymbol):
            self.tok.setLeft(termval)
            termval = self.tok
            right = self.factor()
            termval.setRight(right)

        return termval

    def expr(self):
        # expression := term { ('+'|'-') term }*"
        exprSymbol = ['+', '-']
        exprval = self.term()

        while self.accept(exprSymbol):
            self.tok.setLeft(exprval)
            exprval = self.tok
            right = self.term()
            exprval.setRight(right)
        return exprval

    def pred1(self):
        # pred1 := expr ('>'|'<'|'<='|'>='|'==') expr "
        predSymbol = ['>', '<', '>=', '<=', '==']

        predval = self.expr()
        if self.accept(predSymbol):
            self.tok.setLeft(predval)
            predval = self.tok
            predval.setRight(self.expr())
        return predval

    def pred2(self):
        # pred2 := pred1 { ('&'|'|') pred }*"
        predSymbol = ['&', '|', '!', 'xor', '&&', '||']

        predval = self.pred1()
        while self.accept(predSymbol):
            self.tok.setLeft(predval)
            predval = self.tok
            predval.setRight(self.pred1())

        return predval

    def parse(self):
        self.consume()
        return self.pred2()


    def s_ident(self, scanner, token):
        return AstNode(0, token)

    def s_operator(self, scanner, token):
        return AstNode(3, token)

    def s_float(self, scanner, token):
        return AstNode(2, token)

    def s_int(self, scanner, token):
        return AstNode(1, token)

    def s_paren(self, scanner, token):
        return AstNode(4, token)

    def tokenize(self, string):
        scanner = re.Scanner([
            (r"[a-zA-Z_]\w*", self.s_ident),
            (r"-?\d+\.\d*", self.s_float),
            (r"-?\d+", self.s_int),
            (r"==|\+|-|\*|/|>=|<=|>|<|&|\|\||\|", self.s_operator),
            (r"\(|\)", self.s_paren),
            (r"\s+", None),
        ])
        tok = scanner.scan(string)[0]
        self.tokens = iter(scanner.scan(string)[0])


    def generateConstrain(self, ast, sat=True):

        constrain = None
        if ast.getType()==3:
            left = self.generateConstrain(ast.getLeft())
            right = self.generateConstrain(ast.getRight())

            op = ast.getValue()
            override = ['+', '-', '*', '/', '==', '<=', '>=', '<', '>', '%']

            if op in override:
                constrain = eval('left' + ast.getValue() + 'right')
            elif op == '&' or op == '&&':
                constrain = And(left, right)
            elif op == '|' or op == '||':
                constrain = Or(left, right)
            else:
                raise SyntaxError('Unknown operator in predicates!')

        elif ast.getType() == 0:# fix: mk_int_var
            if ast.getValue() in self.vars:
                constrain = self.vars[ast.getValue()]
            else:
                constrain = Real(ast.getValue())
                self.vars[ast.getValue()] = constrain

        elif ast.getType() == 1:
            constrain = int(ast.getValue())
        elif ast.getType() == 2:
            constrain = float(ast.getValue())

        if not sat:
            constrain = Not(constrain)

        return constrain

