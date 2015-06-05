'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

from types import IntType
from datatypes.dfanode import DfaNode

class ProductNode(DfaNode):

    def __hash__(self):
        return self.hashValue_

    def __eq__(self,other):
        return (self.hashValue_==other.hashValue_)

    def update_hash(self):
        tuple = (self.designError_, self.shieldDeviation_, self.shieldError_, self.relaxError_)

        for node in self.subNodes_:
            tuple=tuple+(node.getNr(),)

        self.hashValue_=tuple.__hash__()

    def __init__(self, pNode=None):
        '''
        Constructor
        '''

        self.hashValue_=None
        if pNode:
            self.NR_=pNode.NR_
            self.isFinal_=pNode.isFinal_
            self.isInitial_=pNode.isInitial_
            self.subNodes_=list(pNode.subNodes_)
            self.designError_=pNode.getDesignError()
            self.shieldDeviation_ = pNode.getShieldDeviation()
            self.shieldError_ = pNode.getShieldError()
            self.relaxError_ = pNode.getRelaxError()
            self.incomingEdges_=list(pNode.incomingEdges_)
            self.outgoingEdges_=list(pNode.outgoingEdges_)
            self.doneBit_=pNode.doneBit_

        else:
            self.NR_=None
            self.isFinal_=None
            self.isInitial_=None
            self.subNodes_=[]
            self.designError_=0
            self.shieldDeviation_=0
            self.shieldError_=0
            self.relaxError_=0
            self.incomingEdges_=[]
            self.outgoingEdges_=[]
            self.doneBit_=False

        self.update_hash()

    def setDone(self,doneBit):
        self.doneBit_=doneBit

    def isDone(self):
        return self.doneBit_

    def appendSubNode(self,subNode):
        self.subNodes_.append(subNode)
        self.update_hash()

    def setSubNodes(self,subNodes):
        self.subNodes_=subNodes
        self.update_hash()

    def getSubNode(self,nr):
        return list(self.subNodes_)[nr]

    def getSubNodeNum(self):
        return len(self.subNodes_)

    def getSubNodes(self):
        return list(self.subNodes_)

    def incrementDesignError(self):
        self.designError_+=1
        self.update_hash()

    def setDesignError(self,designError):
        self.designError_=designError
        self.update_hash()

    def setShieldDeviation(self,shieldDeviation):
        self.shieldDeviation_=shieldDeviation
        self.update_hash()

    def setShieldError(self,shieldError):
        self.shieldError_=shieldError
        self.update_hash()
    def setRelaxError(self, relaxError):
        self.relaxError_ =relaxError
        self.update_hash()

    def copyErrorStatus(self, node):
        if node.getDesignError()!=0:
            assert self.designError_==0
            self.designError_=node.getDesignError()
        if node.getShieldDeviation()!=0:
            assert self.shieldDeviation_==0
            self.shieldDeviation_=node.getShieldDeviation()
        if node.getShieldError()!=0:
            assert self.shieldError_==0
            self.shieldError_=node.getShieldError()
        if node.getRelaxError()!=0:
            assert self.relaxError_==0
            self.relaxError_=node.getRelaxError()        
        self.update_hash()

    def toString(self, details=False, stateProperty = True):
        expression="<"
        if self.NR_!=0:
            if False:
                numOfBits = 6
                binNodeNr = bin(int(self.NR_-1))[2:]
                binStr = ""+binNodeNr.zfill(numOfBits)

                reverseBinStr = ""
                for i in range(numOfBits):
                    reverseBinStr+=binStr[len(binStr)-1-i]

                expression+=reverseBinStr
            else:
                expression+=str(self.NR_)#+str(self)
            expression+=","
        expression+="["
        if len(self.subNodes_)!=0:
            for sNode in self.subNodes_:
                if type(sNode) is ProductNode:
                    for ssNode in sNode.getSubNodes():
                        expression+=str(ssNode.getNr())
                        expression+=","
                    expression=expression[0:len(expression)-1]
                else:
                    expression+=str(sNode.getNr())
                expression+=","
            expression=expression[0:len(expression)-1]
        expression+="]"
        if details:
            expression+=","
            expression+=str(self.designError_)
            expression+=","
            expression+=str(self.shieldError_)
            expression+=","
            expression+=str(self.shieldDeviation_)
            expression+=","
            expression+=str(self.relaxError_)
        expression+=">"

        if stateProperty:
            if self.isInitial_:
                expression+=" (Initial)"
            if self.isFinal_:
                expression+=" (Final)"

        return expression