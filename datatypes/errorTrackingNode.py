'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

from types import IntType
from datatypes.dfanode import DfaNode

#   Error Tracking Node has a set of of SubNodes (Same Subnode should not appear twice)
#   Product Node has list of Subnodes (Same Subnode can and should appear multiple times)
class ErrorTrackingNode(DfaNode):


    def __hash__(self):
        return (self.designError_, self.shieldDeviation_, self.shieldError_, self.relaxError_, self.subNodes_).__hash__()

    def __eq__(self,other):
        if self.designError_ != other.designError_:
            return False

        if self.shieldDeviation_ !=other.shieldDeviation_:
            return False

        if self.shieldError_ != other.shieldError_:
            return False

        if self.subNodes_ != other.subNodes_:
            return False
        
        if self.relaxError_ != other.relaxError_:
            return False

        return True

    def __init__(self, eTNode=None):
        '''
        Constructor
        '''
        if eTNode:
            self.NR_=eTNode.NR_
            self.isFinal_=eTNode.isFinal_
            self.isInitial_=eTNode.isInitial_
            self.subNodes_=set(eTNode.subNodes_)
            self.designError_=eTNode.getDesignError()
            self.shieldDeviation_ = eTNode.getShieldDeviation()
            self.shieldError_ = eTNode.getShieldError()
            self.relaxError_ = eTNode.getRelaxError()
            self.incomingEdges_=list(eTNode.incomingEdges_)
            self.outgoingEdges_=list(eTNode.outgoingEdges_)

        else:
            self.NR_=None
            self.isFinal_=None
            self.isInitial_=None
            self.subNodes_=set()
            self.designError_=0
            self.shieldDeviation_=0
            self.shieldError_=0
            self.relaxError_ =0
            self.incomingEdges_=[]
            self.outgoingEdges_=[]

    def appendSubNode(self,subNode):
        self.subNodes_.add(subNode)

    def setSubNodes(self,subNodes):
        self.subNodes_=subNodes

    def getSubNode(self,nr):
        return list(self.subNodes_)[nr]

    def getSubNodeNum(self):
        return len(self.subNodes_)

    def isSubNodeFinal(self):
        for sNode in self.subNodes_:
            if sNode.isFinal():
                return True
        return False
    def isSingleGood(self):
        if len(self.subNodes_)==1 and not self.isSubNodeFinal():
            return True
        return False
        
    def isOnlyFinal(self):
        if len(self.subNodes_)==1 and self.isSubNodeFinal():
            return True
        return False
    def isMultiGood(self):
        if len(self.subNodes_) > 1 and not self.isSubNodeFinal():
            return True
        return False

    def removeFinalSubNodes(self):
        for sNode in self.getSubNodes():
            if sNode.isFinal():
                self.removeSubNode(sNode)

    def removeSubNode(self, subNode):
        self.subNodes_.remove(subNode)


    def getSubNodes(self):
        return list(self.subNodes_)

    # returns new node containing sub nodes from itself and node2.
    def combineNodes(self, node2):

        combTargetState = ErrorTrackingNode()

        combTargetState.setDesignError(self.getDesignError())
        for sNode in self.getSubNodes():
            combTargetState.appendSubNode(sNode)

        if type(node2) is DfaNode:
            combTargetState.appendSubNode(node2)

        else:
            print("combineNodes not implemented for types other than DfaNode!!!")


        return combTargetState


    def toString(self,details = False, stateProperty = True):
        expression="<["
        for sNode in self.subNodes_:
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
