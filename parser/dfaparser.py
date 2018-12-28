'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

from datatypes.dfa import DFA
from datatypes.dfalabel import DfaLabel
class DfaParser(object):
    '''
    classdocs
    '''
    
    def __init__(self, inputFile):
        '''
        Constructor
        '''
        self.dfa_ = self.readDfaFromInputFile(inputFile)
        
    def readDfaFromInputFile(self,inputFile):
        f = open(inputFile)
        line = f.readline()
        toProcess = ""
        while line:
            line = f.readline()
     
            if "#" in line:
                parts = line.split('#')
                nonCommentPart=parts[0]
                if len(nonCommentPart.strip(' \t')) > 0:
                    toProcess+=nonCommentPart+'\n'
            else:
                if len(line.strip(' \t').rstrip()) >0:
                    toProcess += line.rstrip()+'\n'
        f.close()

        #remove trailing new line
        toProcess=toProcess[0:len(toProcess)-1]
           
        dfa=None        
        if len(toProcess)>0:
            dfa = self.createDfaFromDefinition(toProcess)
        else:
            raise Exception("inputfile is empty or contains only comments!")
           
        return dfa
    
    def createDfaFromDefinition(self, dfaDef):
        lines = dfaDef.split('\n') 
        
        dfaParams = lines[0].split(' ')
        
        if dfaParams[0] != "dfa":
            raise Exception("syntax error: expect dfa definition in first line. keyword 'dfa' is missing.")
        
        if len(dfaParams) != 7:
            raise Exception("dfa definition expects exactly 6 arguments! found '"+str(len(dfaParams))+"'") 
        
        #create DFA
        dfa = DFA(int(dfaParams[1]), int(dfaParams[2]), int(dfaParams[3]), int(dfaParams[4]), int(dfaParams[5]), int(dfaParams[6]))

        #TODO: improve checks for sufficient input lines and that line is really initial/final definition and not an edge by accident. <bk>
        #TODO: not sure if parser can handle all variants of leading and trailing whitespace. be careful at formatting your inputfiles for now. <bk>
        
        #setup edges and create nodes on the fly
        #try to go through all remaining lines. maybe killed of, if letter found as 2nd parameter. then parsing is passed on to var-parsing loop (following below!)         
        proccesingPosition=3
        for i in range(3, len(lines)):
            proccesingPosition=i    # update start position for variable name definitions
            edgeDef = lines[i].rstrip().split(' ')
            
            if len(edgeDef)<2:
                raise Exception("definition-error: edge definition invalid. less than 2 parameters found!\n  line:'"+lines[i]+"'")
            
            if not edgeDef[1].isdigit(): #exit this loop. we seem to have reached a variable name definition
                break
            else: # seems to be edge definition. process
                sourceNr=int(edgeDef[0])
                targetNr=int(edgeDef[1])
                
                #try to get edge label
                literals=[]
                for i in range(2,len(edgeDef)):
                    literals.append(int(edgeDef[i]))
                
                label = DfaLabel(literals)
                
                #try to fetch existing source node 
                sourceNode = dfa.getNode(sourceNr)
                if not sourceNode:  #or create new one
                    sourceNode=dfa.addNodeByNr(sourceNr)  
                
                #try to fetch existing target node
                targetNode = dfa.getNode(targetNr)
                if not targetNode:  #or create a new one
                    targetNode=dfa.addNodeByNr(targetNr)
                
                dfa.addEdge(sourceNode, targetNode, label)
                
        #after edges have created nodes, we can set initial and final attribute flags correctly
        #get initial states
        initialStates = lines[1].rstrip().split(' ')                 
        dfa.setInitalStates(initialStates)
        
        #get final states
        finalStates = lines[2].rstrip().split(' ')
        dfa.setFinalStates(finalStates)
        
                               
        #parse variable name definitions, if present
        for i in range(proccesingPosition, len(lines)):
            varDef = lines[i].rstrip().split(' ')
            dfa.setVarName(int(varDef[0]), varDef[1])

            if len(varDef)> 2:
                pre = lines[i]
                pre = pre[pre.find("(") + 1:pre.rfind(")")]
                dfa.predicates_[int(varDef[0])] = pre
        return dfa

    def getParsedDFA(self):
        return self.dfa_          