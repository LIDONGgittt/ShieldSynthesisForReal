'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

class DfaLabel(object):
    '''
    classdocs
    '''
 
    def __init__(self, literals=None):
        '''
        Constructor
        '''

        if literals:
            self.literals_=literals
        else:
            self.literals_=[]
    def __repr__(self):
        
        lableLiterals = self.literals_
        lableLiterals.sort()
        
        if len(lableLiterals)==1:
            if lableLiterals[0]==0:
                return "false"
        if len(lableLiterals)==0:
            return "true"            
        retVal="("
        for literal in lableLiterals:
            retVal+=str(literal)+" & "
        retVal=retVal[0:len(retVal)-3]
        return retVal+")"
        
    
    
    def merge(self,otherLabel):
        otherLiterals = otherLabel.getLiterals()
        union = set(sorted(self.literals_ + otherLiterals))
        absUnionLen = len(set(map(abs, union)))
             
        if absUnionLen != len(union):
            union=[0]

        return DfaLabel(list(union))
        
    def getLiterals(self):
        return list(self.literals_)    
    
    def isValidLabel(self):
        if len(self.literals_)==0:
            return True
        literals = list(self.literals_)
        if literals[0]==0:
            return False
        return True