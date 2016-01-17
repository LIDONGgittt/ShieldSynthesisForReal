'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

from types import IntType

class DfaNode(object):
    '''
    classdocs
    '''
 
    def __init__(self, node):
        '''
        Constructor
        '''
        
        if type(node) is DfaNode:
            self.NR_=node.getNr()
            self.incomingEdges_=[]
            self.outgoingEdges_=[]
            self.isFinal_=node.isFinal()
            self.isInitial_=node.isInitial()
            self.designError_=node.getDesignError()
            self.shieldDeviation_ = node.getShieldDeviation()
            self.shieldError_ = node.getShieldError()

        else:
            assert type(node) is IntType
            self.NR_=node
            self.incomingEdges_=[]
            self.outgoingEdges_=[]
            self.isFinal_=False
            self.isInitial_=False
            self.designError_=0
            self.shieldDeviation_=0
            self.shieldError_=0
    def __repr__(self):
        retVal = self.toString(details=True)
        retVal += '\n\t%s' % (str(self.getOutgoingEdges().__repr__()))
        retVal += '\n\t%s' % (str(self.getIncomingEdges().__repr__()))
        return retVal+'\n'


    def __hash__(self):
        return self.NR_.__hash__()
    
    def __eq__(self,other):
        if self.NR_!= other.NR_:
            return False
        return True

    def addOutEdge(self,edge):
        self.outgoingEdges_.append(edge)
        
    def addInEdge(self,edge):
        self.incomingEdges_.append(edge)
        
    def removeInEdge(self,edge,force=False):
        #self.incomingEdges_.remove(edge)
        del(self.incomingEdges_[self.incomingEdges_.index(edge)])
        if not force:
            if len(self.incomingEdges_)==0 and not self.isInitial_:
                raise Exception("you have removed the last incoming edge from non-initial node nr '"+str(self.NR_)+"'!")
           
    def removeOutEdge(self,edge,force=False):
        self.outgoingEdges_.remove(edge)
        if not force:
            if len(self.outgoingEdges_)==0:
                raise Exception("you have removed the last outgoing edge from node nr '"+str(self.NR_)+"'!")
    
    def getIncomingEdgesNum(self):
        return len(self.incomingEdges_)
    
    def getIncomingEdges(self):
        return list(self.incomingEdges_)
    
    def getOutgoingEdgesNum(self):
        return len(self.outgoingEdges_)
    
    def getOutgoingEdges(self):
        return list(self.outgoingEdges_)

    def getDesignError(self):
        return self.designError_

    def incrementDesignError(self):
        self.designError_+=1

    def setDesignError(self,designError):
        self.designError_=designError

    def getShieldDeviation(self):
        return self.shieldDeviation_

    def setShieldDeviation(self,shieldDeviation):
        self.shieldDeviation_=shieldDeviation

    def getShieldError(self):
        return self.shieldError_

    def setShieldError(self,shieldError):
        self.shieldError_=shieldError

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
    
    def getNr(self):
        return self.NR_
    
    def setNr(self, nr):
        self.NR_ = nr
    
    def setInitial(self,state):
        self.isInitial_=state

    def setFinal(self,state):
        self.isFinal_=state
        
    def isInitial(self):
        return self.isInitial_
    
    def isFinal(self):
        return self.isFinal_
    
    def toString(self,details=False, stateProperty=True):
        expression="<["
        expression+=str(self.NR_)#+str(self)
        expression+="]"
        if details:
            expression+=","
            expression+=str(self.designError_)
            expression+=","
            expression+=str(self.shieldError_)
            expression+=","
            expression+=str(self.shieldDeviation_)
        expression+=">"

        if stateProperty:
            if self.isInitial_:
                expression+=" (Initial)"
            if self.isFinal_:
                expression+=" (Final)"
            
        return expression