__author__ = 'bkoenighofer'

from datatypes.dfanode import DfaNode
from datatypes.dfa import DFA
from datatypes.dfalabel import DfaLabel
from datatypes.productnode import ProductNode
from datatypes.errorTrackingNode import ErrorTrackingNode
from itertools import combinations

import time

DEBUG = 0

class KStabilizingAlgo(object):
    '''
    If the design violates a safety property, the outputs of the shield are allowed to
    deviate from the design output for at most k consecutive time steps.
    Only after these k time steps, the next specification violation can be tolerated.
    '''

    def __init__(self, specDfa, numShieldDeviations):

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

        self.numShieldDeviations_ = numShieldDeviations

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

        #print("1) Final Error Tracking DFA after Standardization")
        #self.etDFA_.debugPrintDfa(True)
        #print("2) Final Shield Deviation DFA")
        #self.sdDFA_.debugPrintDfa(True)
        #print("3) Final Shield Correctness DFA")
        #self.scDFA_.debugPrintDfa(True)

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
            eTNode.setInitial(True)
            etDFA.addNode(eTNode, True)
            
#         print 'log: Size of spec: '+str(len(self.specDfa_.getNodes()))
        workset=etDFA.getNodes()
        done=[]
        iter_num =0
        #designError_ counter counts from self.numShieldDeviations_ to 0. only if designError_ is 0, a new design error is ok

        #add error state
        if self.numShieldDeviations_ > 1:
            errorState = ErrorTrackingNode()
            finalSubNodes = self.specDfa_.getFinalNodes()
            errorState.appendSubNode(finalSubNodes[0])
            errorState.setDesignError(self.numShieldDeviations_+1)
            errorState.setFinal(True)
            etDFA.addNode(errorState, True)
            etDFA.addEdge(errorState, errorState, DfaLabel())

        while len(workset) > 0:

            iter_num = iter_num+1
#             print 'log: Iteration of etDFA construction: '+str(iter_num)
            state = workset[0]
            del workset[0]
            done.append(state)

            #compute targetStates from state
            #Compute target state by combining all sTargetStates from all sStates from state
            #-start with sTargetStates from first sState

            sState = state.getSubNode(0)
            for sEdge in sState.getOutgoingEdges():
                targetState = ErrorTrackingNode()
                targetState.appendSubNode(sEdge.getTargetNode())
                #decrease counter until next design error for target state
                if state.getDesignError()>0:
                    targetState.setDesignError(state.getDesignError()-1)
                else:
                    targetState.setDesignError(0)
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
                            combTargetState = edge.getTargetNode().combineNodes(sTargetState)
                            combTargetState = etDFA.addNode(combTargetState)
                            etDFA.addEdge(state, combTargetState, combLabel)
                    etDFA.removeEdge(edge, True)

            #Deal with errors
            edges = state.getOutgoingEdges()
            for edge in edges:
                targetState = ErrorTrackingNode(edge.getTargetNode())

                #Case 1: At least one TargetSState is ok, remove errorState from TargetState
                if not targetState.isOnlyFinal():
                    targetState.removeFinalSubNodes()
                    targetState = etDFA.addNode(targetState)
                    etDFA.changeEdgeTarget(edge, targetState, True)

            edges =  state.getOutgoingEdges()
            for edge in edges:
                targetState = ErrorTrackingNode(edge.getTargetNode())

                if targetState.isOnlyFinal():
                    #Case 2: If all TargetSStates are errorStates, and designError is 0, set designError to numShieldDeviations_
                    if state.getDesignError() <= 1:
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

                        newTargetState.setDesignError(self.numShieldDeviations_)
                        newTargetState = etDFA.addNode(newTargetState)
                        etDFA.changeEdgeTarget(edge, newTargetState, True)
                        if not newTargetState in done and not newTargetState.isOnlyFinal() and not newTargetState in workset:
                            newTargetState = etDFA.addNode(newTargetState)
                            workset.append(newTargetState)
                    else:
                        #Case 3: Go to error State, and stay there forever
                        etDFA.changeEdgeTarget(edge, errorState, True)
                else:
                    if not targetState in done and not targetState in workset:
                        targetState = etDFA.addNode(targetState)
                        workset.append(targetState)
        
        
#         print "iteration number for etDFA:"+str(iter_num)
        etDFA.setInputVars(self.specDfa_.getInputVars()+self.specDfa_.getOutputVars())
        etDFA.setOutputVars([])

        #self.updateNodeFlags(etDFA)
        #print("1) Final Error Tracking DFA")
        #etDFA.debugPrintDfa(True)
        self.etDFA_ = etDFA.standardization()

    '''
    Creates automata for tracking shield deviations.

    This function builds an automata to track deviations between shield outputs and design outputs.
    If there was a deviation in the last time step, the dfa will be in state 2.
    If not, the dfa will be in state 1.

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