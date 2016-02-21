'''
Created on Dec 20, 2015
    Build error tracking automaton for burst error: keep replacing error states without going to fail safe state.

@author: meng wu

'''

from datatypes.dfanode import DfaNode
from datatypes.dfa import DFA
from datatypes.dfalabel import DfaLabel
from datatypes.productnode import ProductNode
from datatypes.errorTrackingNode import ErrorTrackingNode
from itertools import combinations
from collections import deque
import time

DEBUG = 0

class BurstErrorAlgo(object):
    '''
    If the design violates a safety property, the outputs of the shield are allowed to
    deviate from the design output for at most k consecutive time steps.
    Only after these k time steps, the next specification violation can be tolerated.
    '''

    def __init__(self, specDfa, numDesignBurst):

        '''
        Constructor
        '''
        #original Specification Automaton

        

        
        self.specDfa_ = specDfa
        
        self.finalDFA_ = specDfa
            
        #Error Tracking Automaton
        self.etDFA_ = DFA()
        #Shield Deviation Automaton
        self.sdDFA_ = DFA()
        #Shield Correctness Automaton
        self.scDFA_ = DFA()
        #Design Relax Automaton
        
        self.numDesignBurst = numDesignBurst
        if DEBUG:
            print( "  start building ErrorTrackingAutomaton...")
            
        self.etDFA_  = self.buildErrorTrackingAutomaton()
        
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

        
        for sNode in self.specDfa_.getNodes():
            if not sNode.isFinal():
                eTNode = ErrorTrackingNode()
                eTNode.appendSubNode(sNode)
                eTNode.setInitial(sNode.isInitial())
                etDFA.addNode(eTNode, True)               
        
#         print 'log: Size of spec(node/edge): '+str(len(self.specDfa_.getNodes()))+'/'+str(len(self.specDfa_.getEdges()))
        workset= deque(etDFA.getNodes())
        done=[]
        iter_num = 0
        
        if self.numDesignBurst > 0:
            errorState = ErrorTrackingNode()
            finalSubNodes = self.specDfa_.getFinalNodes()
            errorState.appendSubNode(finalSubNodes[0])
            errorState.setDesignError(self.numDesignBurst+1)
            errorState.setFinal(True)
            etDFA.addNode(errorState, True)
            etDFA.addEdge(errorState, errorState, DfaLabel())



        
        
        
        while len(workset) > 0:
            iter_num = iter_num+1
#             print 'log: Iteration of etDFA construction: '+str(iter_num)
            
            state = workset.popleft()
            done.append(state)

            
            sState = state.getSubNode(0)
            for sEdge in sState.getOutgoingEdges():
                targetState = ErrorTrackingNode()
                
                sTargetState = sEdge.getTargetNode()
                
                if sTargetState.isFinal():
                    #targetState.setDesignError(state.getDesignError()+1)
                    targetState.setDesignError(1)
                    label = sEdge.getLabel()
                    for edge2 in sState.getOutgoingEdges():
                        targetState2 = edge2.getTargetNode()
                        label2 = edge2.getLabel()
                        if etDFA.checkInputCompatibility(label, label2):
                            if not targetState2.isFinal():
                                targetState.appendSubNode(targetState2)
                else:
                    targetState.setDesignError(0)
                    targetState.appendSubNode(sTargetState)


                targetState = etDFA.addNode(targetState)
                etDFA.addEdge(state, targetState, sEdge.getLabel())

            #-intersect all edges with spec edges of involved spec states
            for i in range(1,state.getSubNodeNum()):
                edges =  state.getOutgoingEdges()
                for edge in edges:
                    label = edge.getLabel()
                    sState = state.getSubNode(i)
                    sEdges = sState.getOutgoingEdges()
                    for sEdge in sEdges:
                        sTargetState = sEdge.getTargetNode()
                        sLabel = sEdge.getLabel()
                        combLabel = sLabel.merge(label)
                        if combLabel.isValidLabel():
                            if sTargetState.isFinal():
                                #label1 = sEdge.getLabel()
                                for sEdge2 in sEdges:
                                    targetState2 = sEdge2.getTargetNode()
                                    label2 = sEdge2.getLabel()
                                    if etDFA.checkInputCompatibility(label2, combLabel):
                                        if not targetState2.isFinal():
                                            combTargetState = edge.getTargetNode().combineNodes(targetState2)
                                            #combTargetState.setDesignError(state.getDesignError()+1)  
                                            combTargetState.setDesignError(1)
                            else:
                                combTargetState = edge.getTargetNode().combineNodes(sTargetState)
                                                         
                            combTargetState = etDFA.addNode(combTargetState)
                            etDFA.addEdge(state, combTargetState, combLabel)
                    etDFA.removeEdge(edge, True)
                            
                            
             
                
            #Deal with errors
            edges = state.getOutgoingEdges()
            for edge in edges:
                targetState = edge.getTargetNode()
#
                if not targetState in done and not targetState in workset:
                    workset.append(targetState)
                

        
        etDFA.setInputVars(self.specDfa_.getInputVars()+self.specDfa_.getOutputVars())
        etDFA.setOutputVars([])

        etDFA = etDFA.standardization()
        return etDFA
            
 
   
    '''
    Creates automata for tracking shield deviations.

    This function builds an automata to track deviations between shield outputs and design outputs.
    If there was a deviation in the last time step, the dfa will be in state 2.
    If not, the dfa will be in state 1.

    '''
    #FIXME: just build deviation monitor for spec_dfa, cause this shield only change the output for current spec property 
    def buildShieldDeviationAutomaton(self):

        #input vars consist of outputs of design and outputs of shield
        #output of design = spec outputs
        self.sdDFA_.setInputVars(self.specDfa_.getOutputVars())
        for varNr in self.sdDFA_.getInputVars():
            self.sdDFA_.setVarName(varNr, self.specDfa_.getVarName(varNr))

        #output of shield = copies of spec outputs
        numDesignOutVars = self.specDfa_.getVarNum()
        for varNr in self.specDfa_.getOutputVars():
            shieldVarNr = varNr + numDesignOutVars
            shieldVarName = self.specDfa_.getVarName(varNr) + "__1"
            self.sdDFA_.addOutputVar(shieldVarNr)
            self.sdDFA_.setVarName(shieldVarNr, shieldVarName)

        #add first state (no deviations happened)
        stateOne = DfaNode(1)
        stateOne.setInitial(True)
        stateOne.setShieldDeviation(0)
        self.sdDFA_.addNode(stateOne, True)

        #add second state (deviations happened)
        stateTwo = DfaNode(2)
        stateTwo.setShieldDeviation(1)
        self.sdDFA_.addNode(stateTwo, True)

        #no deviations (from state 1 to state 1)
        disgnOutVars = self.specDfa_.getOutputVars()
        for var in range(0, len(disgnOutVars)+1):
            for subset in combinations(disgnOutVars, var):
                #construct label: all vars in subset are negated
                label = self.createLabelFromSubset(subset)
                self.sdDFA_.addEdge(stateOne, stateOne, label)

        #deviations (from state 1 to state 2, and from state 1 to state 2)
        for designNr in self.specDfa_.getOutputVars():
            shieldNr = designNr+self.specDfa_.getVarNum()
            label = DfaLabel([designNr, shieldNr*-1])
            self.sdDFA_.addEdge(stateOne, stateTwo, label)
            label = DfaLabel([designNr*-1, shieldNr])
            self.sdDFA_.addEdge(stateOne, stateTwo, label)

        #no deviations (from state 2 to state 1)
        disgnOutVars = self.specDfa_.getOutputVars()
        for var in range(0, len(disgnOutVars)+1):
            for subset in combinations(disgnOutVars, var):
                #construct label: all vars in subset are negated
                label = self.createLabelFromSubset(subset)
                self.sdDFA_.addEdge(stateTwo, stateOne, label)

        #deviations (from state 2 to state 2, and from state 1 to state 2)
        for designNr in self.specDfa_.getOutputVars():
            shieldNr = designNr+self.specDfa_.getVarNum()
            label = DfaLabel([designNr, shieldNr*-1])
            self.sdDFA_.addEdge(stateTwo, stateTwo, label)
            label = DfaLabel([designNr*-1, shieldNr])
            self.sdDFA_.addEdge(stateTwo, stateTwo, label)


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

        for designNr in self.finalDFA_.getOutputVars():
            shieldNr = designNr+self.finalDFA_.getVarNum()
            if designNr in subset:
                literals.append(designNr*-1)
                literals.append(shieldNr*-1)
            else:
                literals.append(designNr)
                literals.append(shieldNr)

        return DfaLabel(literals)

    '''
    Creates automata that ensures correctness of the shield.

    This automaton corresponds to the spec-automaton and design automaton, 
    but all occurrence of an design output oi renamed by the corresponding 
    shield output oi'.

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
        for sState in self.specDfa_.getNodes():
            state = DfaNode(sState)
            if state.isFinal():
                state.setShieldError(1)
            self.scDFA_.addNode(state, True)

        #copy edges from spec automata, alter label
        for sState in self.specDfa_.getNodes():
            for specEdge in sState.getOutgoingEdges():
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
    Creates automata that relax the game automaton using the verified property

    This automaton will copy the design dfa, and change all its outputs to inputs
    '''

    def buildDesignRelaxAutomaton(self):
        
        #inputs = design inputs
        self.drDFA_.setInputVars(self.designDFA_.getInputVars())
        for varNr in self.drDFA_.getInputVars():
            self.drDFA_.setVarName(varNr, self.designDFA_.getVarName(varNr))

        self.drDFA_.setOutputVars(self.designDFA_.getOutputVars())
        for varNr in self.drDFA_.getOutputVars():
            self.drDFA_.setVarName(varNr, self.designDFA_.getVarName(varNr))
            
        #copy nodes from design automata
        for sState in self.designDFA_.getNodes():
            state = DfaNode(sState)
            if state.isFinal():
                state.setRelaxError(1)
            self.drDFA_.addNode(state, True)
        
        #copy edges from design automata
        for sState in self.designDFA_.getNodes():
            for designEdge in sState.getOutgoingEdges():
                sLabel = designEdge.getLabel()
                sTarget = self.drDFA_.getNode(designEdge.getTargetNode().getNr())
                sSource = self.drDFA_.getNode(designEdge.getSourceNode().getNr())

                self.drDFA_.addEdge(sSource, sTarget, sLabel)

        self.drDFA_.setInputVars(self.designDFA_.getInputVars()+self.designDFA_.getOutputVars())
        self.drDFA_.setOutputVars([])
        
            
        