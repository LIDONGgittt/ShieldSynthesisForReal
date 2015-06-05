'''
Created on Jun 10, 2014

@author: bkoenighofer
'''

from datatypes.dfanode import DfaNode
from datatypes.dfa import DFA
from datatypes.dfalabel import DfaLabel
from datatypes.productnode import ProductNode
from itertools import combinations
from datatypes.errorTrackingNode import ErrorTrackingNode

import time

DEBUG = 0

class FiniteDesignErrorAlgo(object):
    '''
    The Shield is only able to deal with a finite number of design errors.
    If the total number of design errors is less or equal than "allowedDesignError", then the shield can
    fix the output with max. "numShieldDeviations" deviations from the design output.
    '''

    def __init__(self, specDfa, allowedDesignError, numShieldDeviations, compute_product_explicit):
        '''
        Constructor
        '''
        #original Specification Automaton
        self.specDfa_ = specDfa


        #Error Tracking Automaton
        self.etDFA_ = DFA()
        #Shield Deviation Automaton
        self.sdDFA_ = DFA()
        #Shield Correctness Automaton
        self.scDFA_ = DFA()
        #Final Product DFA
        self.finalDFA_ = DFA()


        self.allowedDesignError_ = allowedDesignError
        self.numShieldDeviations_ = numShieldDeviations
        self.prodDFA_ = DFA()

        if DEBUG:
            print( "  start building ErrorTrackingAutomaton...")
        self.buildErrorTrackingAutomaton()
        if DEBUG:
            print( "  ...done")
            print( "  start building ShieldDeviationAutomaton...")
        self.buildShieldDeviationAutomaton()
        if DEBUG:
            print( "  ...done")
            print( "  start building ShieldCorrectnessAutomaton...")
        self.buildShieldCorrectnessAutomaton()
        if DEBUG:
            print( "  ...done")

        #print("1) Final Error Tracking DFA")
        #self.etDFA_.debugPrintDfa(True)
        #print("2) Final Shield Deviation DFA")
        #self.sdDFA_.debugPrintDfa(True)
        #print("3) Final Shield Correctness DFA")
        #self.scDFA_.debugPrintDfa(True)

    '''
    Creates automata that ensures correctness of the shield.
    
    This automaton corresponds to the spec-automaton, but all occurrence
    of an design output oi renamed by the corresponding shield output oi'.

    '''
    def buildShieldCorrectnessAutomaton(self):
        
        #inputs = design inputs
        self.scDFA_.setInputVars(self.specDfa_.getInputVars())
        for varNr in self.scDFA_.getInputVars():
            self.scDFA_.setVarName(varNr, self.specDfa_.getVarName(varNr))
        
        #outputs = shield outputs
        numDesignOutVars = self.specDfa_.getVarNum()
        for varNr in self.specDfa_.getOutputVars():
            shieldVarNr = varNr + numDesignOutVars
            sieldVarName = self.specDfa_.getVarName(varNr) + "__1"
            self.scDFA_.addOutputVar(shieldVarNr)
            self.scDFA_.setVarName(shieldVarNr, sieldVarName)
        
        #copy nodes from spec automata
        for specState in self.specDfa_.getNodes():
            state = DfaNode(specState)
            if state.isFinal():
                state.setShieldError(1)
            self.scDFA_.addNode(state, True)
            
        #copy edges from spec automata, alter label
        for specState in self.specDfa_.getNodes():
            for specEdge in specState.getOutgoingEdges():
                specLabel = specEdge.getLabel()
                #rename output variables from specLabel
                specInLiterals = self.specDfa_.getInputLiterals(specLabel)
                specOutLiterals = self.specDfa_.getOutputLiterals(specLabel)
                
                signs = [ 1 if lit > 0 else -1 for lit in specOutLiterals]
                specOutVars = map(abs, specOutLiterals)
                shieldOutVars = [var + self.specDfa_.getVarNum() for var in specOutVars]
                shieldOutLiterals = [sign*var for sign,var in zip(signs,shieldOutVars)]
                             
                shieldLabel = DfaLabel(specInLiterals+shieldOutLiterals)
                
                shieldTarget = self.scDFA_.getNode(specEdge.getTargetNode().getNr())
                sourceTarget = self.scDFA_.getNode(specEdge.getSourceNode().getNr())               
                                
                self.scDFA_.addEdge(sourceTarget, shieldTarget, shieldLabel)
      
    '''
    Creates automata for tracking shield deviations.
    
    The shield is allowed to deviate from the output 'numShieldDerivations' times, 
    if the design makes one safety error. The function builds an automata to track
    deviations.
    
    '''  
    def buildShieldDeviationAutomaton(self):
        
        #input vars consist of outputs of design and outputs of shield
        #output of design = spec outputs
        self.sdDFA_.setInputVars(self.specDfa_.getOutputVars())
        for varNr in self.sdDFA_.getInputVars():
            self.sdDFA_.setVarName(varNr, self.specDfa_.getVarName(varNr))
            
        #output of shield = copies of spec outputs
        for varNr in self.specDfa_.getOutputVars():
            shieldVarNr = varNr + self.specDfa_.getVarNum()
            shieldVarName = self.specDfa_.getVarName(varNr) + "__1"
            self.sdDFA_.addOutputVar(shieldVarNr)
            self.sdDFA_.setVarName(shieldVarNr, shieldVarName)
            
        #add error state      
        errorState = DfaNode(self.numShieldDeviations_+2)
        errorState.setFinal(True)
        errorState.setShieldDeviation(self.numShieldDeviations_+1)
        self.sdDFA_.addNode(errorState, True)
            
        #add initial state
        initialState = DfaNode(1)
        initialState.setInitial(True)
        initialState.setShieldDeviation(0)
        self.sdDFA_.addNode(initialState, True)
        
        for i in range(1,self.numShieldDeviations_+2):
            curState = self.sdDFA_.getNode(i)
            nextState = None
            if i==self.numShieldDeviations_+1:
                nextState = errorState
            else:
                nextState = DfaNode(i+1)
                nextState.setShieldDeviation(i)
                self.sdDFA_.addNode(nextState, True)
        
            #add self loop edges at current state
            disgnOutVars = self.specDfa_.getOutputVars()
            for L in range(0, len(disgnOutVars)+1):
                for subset in combinations(disgnOutVars, L):
                    #construct label: all vars in subset are negated
                    label = self.createLabelFromSubset(subset)
                    self.sdDFA_.addEdge(curState, curState, label)
            
            #add edges to next state     
            for designNr in self.specDfa_.getOutputVars():       
                shieldNr = designNr+self.specDfa_.getVarNum()
                label = DfaLabel([designNr, shieldNr*-1])  
                self.sdDFA_.addEdge(curState, nextState, label)
                label = DfaLabel([designNr*-1, shieldNr]) 
                self.sdDFA_.addEdge(curState, nextState, label)

        self.sdDFA_.addEdge(errorState, errorState, DfaLabel())
        
    '''
    Computes a label from a subset
    
    Helper Function to build a ShieldDeviationAutomaton.
    Takes a subset of Design-Variables, e.g. o1, o3.
    All Design-Vars in Subset are negated, all other Design_Vars are positive.
    Shield-Vars have same values then Design-Vars
    e.g. returns ~o1^~o1'^o2^o2'^~o3^~o3'^o4^o4',
    
    '''        
    def createLabelFromSubset(self, subset):
        
        literals = []
        
        for designNr in self.specDfa_.getOutputVars():
            shieldNr = designNr+self.specDfa_.getVarNum()
            if designNr in subset:        
                literals.append(designNr*-1)
                literals.append(shieldNr*-1)
            else:
                literals.append(designNr)
                literals.append(shieldNr)     
 
        return DfaLabel(literals)   
        

    '''
    Creates automata to track the behavior of the design.
    
    Creates automata that tracks the errors made by the design. Each state has an error level.
    Each time the design makes an error, the error level of the next state is increased
    until 'allowedDesignError' is reached. The next error leads to the only real error state,
    in which the automata stays forever. 
    '''        
    def buildErrorTrackingAutomaton(self):
        #build state list
        
        etDFA = DFA()
        etDFA.setVarNames(self.specDfa_.getVarNames())

        etDFA.setInputVars(self.specDfa_.getInputVars())
        etDFA.setOutputVars(self.specDfa_.getOutputVars())
        
        initialSNodes = self.specDfa_.getInitialNodes()
        for sNode in initialSNodes:
            eTNode = ErrorTrackingNode()
            eTNode.appendSubNode(sNode)
            etDFA.addNode(eTNode, True)

        workset=etDFA.getNodes()
        done=[]

        #add error state
        errorState = ErrorTrackingNode()
        finalSubNodes = self.specDfa_.getFinalNodes()
        errorState.appendSubNode(finalSubNodes[0])
        errorState.setDesignError(self.allowedDesignError_+1)
        etDFA.addNode(errorState, True)
        etDFA.addEdge(errorState, errorState, DfaLabel())
        
        while len(workset) > 0:

            state = workset[0]
            del workset[0]
            done.append(state)
            
            designError = state.getDesignError()
            
            #compute targetStates from state
            #Compute target state by combining all sTargetStates from all sStates from state
            #-start with sTargetStates from first sState

            sState = state.getSubNode(0)
            for sEdge in sState.getOutgoingEdges():
                targetState = ErrorTrackingNode()
                targetState.appendSubNode(sEdge.getTargetNode())
                targetState.setDesignError(state.getDesignError())
                targetState = etDFA.addNode(targetState)
                etDFA.addEdge(state, targetState, sEdge.getLabel())
            
            #-intersect all edges with spec edges of involved spec states
            for i in range(1,state.getSubNodeNum()):
                edges =  state.getOutgoingEdges()
                for edge in edges:
                    #print "num edges " + str(len(edges))
                    label = edge.getLabel()
                    sState = state.getSubNode(i)
                    sEdges = sState.getOutgoingEdges()
                    for sEdge in sEdges:
                        sTargetState = sEdge.getTargetNode()
                        sLabel = sEdge.getLabel()                   
                        combLabel = sLabel.merge(label)
                        if combLabel.isValidLabel():                          
                            combTargetState = edge.getTargetNode().combineNodes(sTargetState)
                            # if at least one TargetSState is ok, remove errorState from TargetState
                            if combTargetState.isSubNodeFinal:
                                if not combTargetState.isOnlyFinal():
                                    combTargetState.removeFinalSubNodes()
                            combTargetState = etDFA.addNode(combTargetState)
                            etDFA.addEdge(state, combTargetState, combLabel)
                    etDFA.removeEdge(edge, True)

            edges =  state.getOutgoingEdges()
            for edge in edges:
                targetState = edge.getTargetNode()

                #Deal with errors
                if targetState.isOnlyFinal():
                    # If all TargetSStates are errorStates, increase error level if possible
                    if designError < self.allowedDesignError_ :
                        #go to any targetState possible with the same input vars
                        newTargetState = ErrorTrackingNode()
                        label = edge.getLabel()
                        edges2 =  state.getOutgoingEdges()
                        for edge2 in edges2:
                            targetState2 = edge2.getTargetNode()
                            if not targetState2.isOnlyFinal():
                                label2 = edge2.getLabel()
                                if etDFA.checkInputCompatibility(label, label2):
                                    #go to targetState2
                                    for i in range(0,targetState2.getSubNodeNum()):
                                        newTargetState.appendSubNode(targetState2.getSubNode(i))

                        newTargetState.setDesignError(edge.getSourceNode().getDesignError()+1)
                        newTargetState = etDFA.addNode(newTargetState)
                        etDFA.changeEdgeTarget(edge, newTargetState, True)
                        if not newTargetState in done and not newTargetState.isOnlyFinal() and not newTargetState in workset:
                            newTargetState = etDFA.addNode(newTargetState)
                            workset.append(newTargetState)

                    else:
                        # Go to error State, and stay there forever
                        etDFA.changeEdgeTarget(edge, errorState, True)
                else:
                    if not targetState in done and not targetState in workset:
                        targetState = etDFA.addNode(targetState)
                        workset.append(targetState)

        etDFA.setInputVars(self.specDfa_.getInputVars()+self.specDfa_.getOutputVars())
        etDFA.setOutputVars([])

        self.updateNodeFlags(etDFA)
        self.etDFA_ = etDFA.standardization()

    def updateNodeFlags(self,etDFA):
        for node in etDFA.getNodes():
            final=True
            initial=True
            for subnode in node.getSubNodes():
                if not subnode.isFinal():
                    final=False

                if not subnode.isInitial():
                    initial=False

            if node.getDesignError() !=0:
                initial=False

            node.setInitial(initial)
            node.setFinal(final)

