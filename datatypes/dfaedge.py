'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

class DfaEdge(object):
    '''
    classdocs
    '''
    
    def __init__(self, sourceNode,targetNode,label):
        '''
        Constructor
        '''
        self.sourceNode_=sourceNode
        self.targetNode_=targetNode
        self.label_=label
    def __repr__(self):
        sourceNr=self.sourceNode_.toString(False, False)
        targetNr=self.targetNode_.toString(False, False)
        retVal = str(sourceNr)+" -> "+str(targetNr)+": "+str(self.label_.__repr__())
        return retVal
  
    def setSourceNode(self,newSourceNode):
        self.sourceNode_=newSourceNode

    def setTargetNode(self,newTargetNode):
        self.targetNode_=newTargetNode
        
    def getSourceNode(self):
        return self.sourceNode_

    def getTargetNode(self):
        return self.targetNode_
    
    def getLabel(self):
        return self.label_
    