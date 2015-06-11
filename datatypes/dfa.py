'''
Created on Jun 3, 2014

@author: bkoenighofer
'''

from datatypes.dfanode import DfaNode
from datatypes.dfaedge import DfaEdge
from datatypes.productnode import ProductNode
from datatypes.errorTrackingNode import ErrorTrackingNode
from datatypes.dfalabel import DfaLabel
import math
import time

DEBUG = 0

class DFA(object):
    '''
    classdocs
    '''
    
    all_input_vars_ = []
    all_output_vars_ = []
    
    all_in_out_vars_ = []
    all_var_names_ = dict()
    
    '''
    Keep tracking all in out vars presented in all dfa used,
    And unify current dfa with all other vars
    The reasoning behind this:  
        when use non-det strategy from last iteration
        must make sure all var bdds is unified    
    '''
    def unify(self):
        
        unified_dfa = DFA()
        
        var_names = self.getVarNames().values()
        
        for var_name in var_names:
            if var_name not in DFA.all_in_out_vars_:
                DFA.all_in_out_vars_.append(var_name)
                DFA.all_var_names_[var_name] = len(DFA.all_in_out_vars_)
            
        #compute joint input and output variables
        for var_nr in self.getInputVars():
            var_name = self.getVarName(var_nr)
            unified_var_num = DFA.all_var_names_[var_name]
            unified_dfa.addInputVar(unified_var_num)
            unified_dfa.setVarName(unified_var_num, var_name)
            
        for var_nr in self.getOutputVars():
            var_name = self.getVarName(var_nr)
            unified_var_num = DFA.all_var_names_[var_name]
            unified_dfa.addOutputVar(unified_var_num)
            unified_dfa.setVarName(unified_var_num, var_name)          
            
        for node in self.getNodes():
            u_node = DfaNode(node.getNr())
            u_node.setInitial(node.isInitial())
            u_node.setFinal(node.isFinal())
            u_node.copyErrorStatus(node)
            unified_dfa.addNode(u_node, True)            
        
        for node in self.getNodes():
            for egde in node.getOutgoingEdges():
                u_source = unified_dfa.getNode(egde.getSourceNode().getNr())
                u_target = unified_dfa.getNode(egde.getTargetNode().getNr())
                u_label = self.transformLabel(egde.getLabel(), self, DFA.all_var_names_)
                unified_dfa.addEdge(u_source, u_target, u_label)          
        return unified_dfa       
        


    
    #TODO: keep initial "num" values consistent with construstor passed ones. update counters on add change delete modifications of the DFA.

    def __init__(self, numStates=0, numVI=0, numVO=0, numInitial=0, numFinal=0, numEdges=0):
        '''
        Constructor
        '''
        self.numStates_ = numStates       #number of states
        self.numVI_= numVI     #number of input variables
        self.numVO_ = numVO     #number of output variables
        self.numInitial_ = numInitial       #number of initial states
        self.numFinal_ = numFinal       #number of final states
        self.numEdges_ = numEdges      #number of edges
        
        self.Edges_=[]
        self.Nodes_=[]
        self.VarNames_=dict()
        
        self.inputVars_ = [i for i in range(1,numVI+1)]
        self.outputVars_ = [i for i in range(numVI+1,numVI+numVO+1)]        
        
    def __repr__(self):        
        retVal = self.getPrettyMe()
        return retVal
        
    def setInitalStates(self,initialStates):
        for stateNr in initialStates:
            stateNr=int(stateNr)
            node = self.getNode(stateNr)
            if not node:
                raise Exception("definition error: you tried to set a non-existent node to 'initial'. Node with number '"+str(stateNr)+"' does not exist.")
            node.setInitial(True)
       
    def getNumInitialStates(self):
        return len(self.getInitialNodes())
    
    def getNumFinalStates(self):
        return len(self.getFinalNodes())   

    def getNumEdges(self):
        return len(self.Edges_)
        
    def setFinalStates(self,finalStates):
        for stateNr in finalStates:
            stateNr=int(stateNr)
            node = self.getNode(stateNr)
            if not node:
                raise Exception("definition error: you tried to set a non-existent node to 'final'. Node with number '"+str(stateNr)+"' does not exist.")
            node.setFinal(True)
        
    def getInitialNodes(self):
        initialNodes=[]
        for node in self.Nodes_:
            if node.isInitial():
                initialNodes.append(node)
        return initialNodes
    
    def getFinalNodes(self):
        finalNodes=[]
        for node in self.Nodes_:
            if node.isFinal():
                finalNodes.append(node)
        return finalNodes
    
    def getNodeNum(self):
        return len(self.Nodes_)
    
    def getVarNum(self):
        return len(self.inputVars_)+len(self.outputVars_)
    
    
    def addNode(self,node, force=False):
        if force:
            self.Nodes_.append(node)
            return node

        if node in self.Nodes_:
            return self.Nodes_[self.Nodes_.index(node)]
        else:
            self.Nodes_.append(node)
            return node


    def addNodeByNr(self,nr):
        node = DfaNode(nr) 
        self.Nodes_.append(node)
        return node
        
    def getNode(self,nr):
        for node in self.Nodes_:
            if node.getNr() == nr:
                return node 
        return None
    
    def getNodes(self):
        return list(self.Nodes_)
    
        
    def addEdge(self,source,target,label):
        edge = DfaEdge(source,target,label)

        source.addOutEdge(edge)
        target.addInEdge(edge)
        
        self.Edges_.append(edge)
        
        return edge
    
    def changeEdgeSource(self,edge,newSource, force=False):
        oldSource = edge.getSourceNode()
        oldSource.removeOutEdge(edge, force)
        edge.setSourceNode(newSource)
        newSource.addOutEdge(edge)      
        if oldSource.getIncomingEdgesNum()==0:
            if oldSource.getOutgoingEdgesNum()==0: 
                self.Nodes_.remove(oldSource)
                   
    def changeEdgeTarget(self,edge,newTarget, force=False):
        oldTarget = edge.getTargetNode()    
        oldTarget.removeInEdge(edge, force)
        edge.setTargetNode(newTarget)
        newTarget.addInEdge(edge)                    
        if oldTarget.getIncomingEdgesNum()==0:
            if oldTarget.getOutgoingEdgesNum()==0: 
                self.Nodes_.remove(oldTarget) 
        
    def setVarName(self,varNr,name):
        self.VarNames_[varNr]=name
        
    def getVarName(self, varNr):
        return self.VarNames_[varNr]
    
    def setVarNames(self,varlist):
        self.VarNames_=varlist
        
    def getVarNames(self):
        return dict(self.VarNames_)
    
    def addInputVar(self, inputVar):
        if inputVar not in self.inputVars_:
            self.inputVars_.append(inputVar) 
    
    def addInputVars(self, inputVars):
        for inputVar in inputVars:
            self.addInputVar(inputVar)    
    
    def getInputVars(self):
        return list(self.inputVars_)
    
    def getNumInputVars(self):
        return len(self.inputVars_)
    
    def setInputVars(self, inputVars):
        self.inputVars_=inputVars
    
    def getNumOutputVars(self):
        return len(self.outputVars_)
    
        
    def addOutputVar(self, outputVar):
        if outputVar not in self.outputVars_:
            self.outputVars_.append(outputVar)  
            
    def addOutputVars(self, outputVars):
        for outputVar in outputVars:
            self.addOutputVar(outputVar)
    
    def getOutputVars(self):
        return list(self.outputVars_)
        
    def setOutputVars(self, outputVars):
        self.outputVars_=outputVars
    
    def negate(self, var):
        return var*-1
    
    def intersect(self, a, b):
        return list(set(a) & set(b))
    
    #returns all input literals from label
    def getInputLiterals(self,label):      
        litLabel = label.getLiterals()   
        allInputLiterals = map(self.negate, self.inputVars_) + self.inputVars_        
        return self.intersect(allInputLiterals, litLabel)    
    
    def getOutputLiterals(self,label):      
        litLabel = label.getLiterals()   
        allOutputLiterals = map(self.negate, self.outputVars_) + self.outputVars_        
        return self.intersect(allOutputLiterals, litLabel)  
         
     
    #returns true, if input values of two labels are compatible 
    #returns false, otherwise (Literal occurs both positive and negative)
    def checkInputCompatibility(self, label1, label2):
        inLit1 = self.getInputLiterals(label1)
        inLit2 = self.getInputLiterals(label2)
        negInLit2 = map(self.negate, inLit2)
        intersection = self.intersect(inLit1, negInLit2)
        if len(intersection):
            return False
        return True

    def removeEdge(self, edge, force=False):

        self.Edges_.remove(edge)
        #also delete entries in nodes, to be consistent
        
        sourceNode = edge.getSourceNode()
        targetNode = edge.getTargetNode()
        
        sourceNode.removeOutEdge(edge, force)
        targetNode.removeInEdge(edge, force)
        
        if sourceNode.getIncomingEdgesNum()==0:
            if sourceNode.getOutgoingEdgesNum()==0: 
                #print(self.getPrettyNode(sourceNode))
                self.Nodes_.remove(sourceNode)
                
        if targetNode.getIncomingEdgesNum()==0:
            if targetNode.getOutgoingEdgesNum()==0:
                if sourceNode!=targetNode:
                    self.Nodes_.remove(targetNode)
    
    def removeNode(self,node):
        #node removal also deletes all corresponding edges
        for edge in node.getIncomingEdges():
            self.removeEdge(edge,True)
        for edge in node.getOutgoingEdges():
            self.removeEdge(edge,True)
        #node gets deleted, when last edge is deleted
       
    
    def removeNodeByNr(self,nr):
        for node in self.Nodes_:
            if node.getNr() == nr:
                    self.removeNode(node)
                    break
    
    
    def applyFunctionToAllNodes(self, callBack):
        for node in self.Nodes_:
            callBack(self,node)
        return None
    
    def varToName(self,varNr):
        if varNr in self.VarNames_:
            return self.VarNames_[varNr]
        return ''+varNr #return number as string if not defined in dict

    '''
    Takes an automaton (with ErrorTrackingNodes, ProductNodes, or normal DfaNodes)
    and creates an equivalent automaton with DfaNodes or ProductNodes.
    Closes gaps in node numbers.
    '''
    def standardization(self, use_dfa_nodes = False):

        nodes = self.getNodes()

        node_nr = 1
        for node in nodes:
            node.setNr(node_nr)
            node_nr = node_nr + 1

        if type(nodes[0]) is DfaNode:
            return self

        if (not use_dfa_nodes) and type(nodes[0]) is ProductNode:
            return self

        resDFA = DFA()

        #inputs
        resDFA.setInputVars(self.getInputVars())
        for varNr in self.getInputVars():
            resDFA.setVarName(varNr, self.getVarName(varNr))
        #outputs
        resDFA.setOutputVars(self.getOutputVars())
        for varNr in self.getOutputVars():
            resDFA.setVarName(varNr, self.getVarName(varNr))

        #add nodes to result DFA
        for node in nodes:
            resNode = DfaNode(node.getNr())
            resNode.setInitial(node.isInitial())
            resNode.setFinal(node.isFinal())
            resNode.copyErrorStatus(node)
            resDFA.addNode(resNode, True)

        #add edges to result DFA
        for node in nodes:
            for inputEdge in node.getOutgoingEdges():
                resSource = resDFA.getNode(inputEdge.getSourceNode().getNr())
                resTarget = resDFA.getNode(inputEdge.getTargetNode().getNr())
                resDFA.addEdge(resSource, resTarget, inputEdge.getLabel())
        return resDFA













    '''
    Removes all redundant edges from dfa.
    
    E.g. first edge: Edge from node 1 to 2 with label a and b
         second edge: Edge from node 1 to 2 with label a
         first edge is contained in second edge, delete edge 1
    '''    
    def simplifyEdges(self):

        #remove equivalent edges
        removeEdges = set()
        for node in self.Nodes_:
            edges = node.getOutgoingEdges()
            for i in range(0, node.getOutgoingEdgesNum()):
                for j in range(i+1, node.getOutgoingEdgesNum()):
                    edge1 = edges[i]
                    edge2 = edges[j]
                    if edge2.getTargetNode() == edge1.getTargetNode():
                        lit1 = edge1.getLabel().getLiterals()
                        lit2 = edge2.getLabel().getLiterals()
                        combLabel = set(sorted(lit1 + lit2))
                        if len(combLabel) == len(lit1) and len(combLabel) == len(lit2):
                            removeEdges.add(edge2)

        for edge in removeEdges:
            self.removeEdge(edge, True)

        #remove edges, that are contained in another edge
        removeEdges = set()
        for node in self.Nodes_:
            edges = node.getOutgoingEdges()
            for i in range(0, node.getOutgoingEdgesNum()):
                for j in range(i+1, node.getOutgoingEdgesNum()):
                    edge1 =  edges[i]
                    edge2 =  edges[j]
                    if edge2.getTargetNode() == edge1.getTargetNode():
                        lit1 = edge1.getLabel().getLiterals()
                        lit2 = edge2.getLabel().getLiterals()
                        combLabel = set(sorted(lit1 + lit2))
                        if len(combLabel) == len(lit1) or len(combLabel) == len(lit2):
                            if(len(lit1)>len(lit2)):
                                removeEdges.add(edge1)
                            if(len(lit2)>len(lit1)):
                                removeEdges.add(edge2)

        for edge in removeEdges:
            self.removeEdge(edge, True)


    
    def getPrettyLabel(self,label):
        literals = label.getLiterals()
        literals.sort()

        if len(literals)==1:
            if literals[0]==0:
                return "false"

        if len(literals)==0:
            return "true"
        
        expression="("
        for variable in literals:
            varName=self.varToName(int(math.fabs(variable)))
            if variable < 0:
                expression+="!"
            expression+=varName+" AND "
            
        #remove last AND
        expression=expression[0:len(expression)-5]
        expression+=")"
                   
        return expression
    
    def getPrettyEdge(self,edge,nodeDetails=False):
        sourceNr=edge.getSourceNode().toString(nodeDetails, False)
        targetNr=edge.getTargetNode().toString(nodeDetails, False)
        prettyLabel= self.getPrettyLabel(edge.getLabel())
        return str(sourceNr)+" -> "+str(targetNr)+": "+prettyLabel
    
    def getPrettyNode(self,node, nodeDetails=False):
        return node.toString(nodeDetails)
    
    
    def getPrettyMe(self, nodeDetails=False):
        outputStr="\n=================================="

        outputStr+= "\n input vars: "
        for var in self.inputVars_:
            outputStr+= self.VarNames_[var] + " "

        outputStr+= "\n output vars: "
        for var in self.outputVars_:
            outputStr+= self.VarNames_[var] + " "

        outputStr+="\n states:\n"
        for node in self.Nodes_:
            outputStr+="    "+self.getPrettyNode(node, nodeDetails)+"\n"
        
        outputStr+="\n"
        
        outputStr+=" transitions:\n"
        for edge in self.Edges_:
             outputStr+="    "+self.getPrettyEdge(edge,nodeDetails)+"\n"
        
        
           
        outputStr+="==================================\n\n" 
        return outputStr

    def getEdges(self):
        return list(self.Edges_)

    def debugPrintDfa(self, nodeDetails = False):
        print(self.getPrettyMe(nodeDetails))

    '''
        Returns a new automaton, where everything is the same,
        except that all variables get input variables (even output variables).
        Result-Automaton gets new output variable "err", that is always false except in final states

    '''
    def createVerificationDfa(self):

        res_dfa = DFA()

        #add input vars as input vars
        res_dfa.setInputVars(self.getInputVars())
        for varNr in self.getInputVars():
            res_dfa.setVarName(varNr, self.getVarName(varNr))

        #add output vars as input vars
        for varNr in self.getOutputVars():
            res_dfa.addInputVar(varNr)
            res_dfa.setVarName(varNr, self.getVarName(varNr))

        #add new output variable err
        last_in_var_nr = max(res_dfa.getInputVars())
        out_var_nr = last_in_var_nr+1

        out_var_name = "err"
        res_dfa.setOutputVars([out_var_nr])
        res_dfa.setVarName(out_var_nr, out_var_name)

        #add nodes
        for node in self.getNodes():
            if type(node) is ProductNode:
                res_node = ProductNode()
                res_node.setSubNodes(node.getSubNodes())
                res_node.setNr(node.getNr())
            else:
                res_node = DfaNode(node.getNr())
            res_node.setInitial(node.isInitial())
            res_node.setFinal(node.isFinal())
            res_node.copyErrorStatus(node)
            res_dfa.addNode(res_node, True)

        #copy all edges
        for node in self.getNodes():
            for edge in node.getOutgoingEdges():

                literals = edge.getLabel().getLiterals()
                res_source = res_dfa.getNode(edge.getSourceNode().getNr())
                res_target = res_dfa.getNode(edge.getTargetNode().getNr())

                 #if source state is final, error bit is true
                if not res_source.isFinal():
                    res_label = DfaLabel(literals+[-out_var_nr])
                else:
                    res_label = DfaLabel(literals+[out_var_nr])

                res_dfa.addEdge(res_source, res_target, res_label)

        return res_dfa

    '''
    Returns the product of itself and dfa2
    "use_joint_vars" can be set to true, if input and output variables of automata do not match
    and new common variables numbers are needed.
    '''
    def buildProductOfAutomata(self, dfa2, use_joint_vars = False):
        prodDFA = DFA()

        #if variables do not match, create copies of self and dfa2 with common variables
        if use_joint_vars:
            dfas = self.buildAutomatonWithCommonVariables(self, dfa2)
            c_dfa1 = dfas[0]
            c_dfa2 = dfas[1]
        else:
            c_dfa1 = self
            c_dfa2 = dfa2

        if DEBUG:
            print( "      num states dfa1 = " + str(len(c_dfa1.getNodes())))
            print("      num states dfa2 = " + str(len(c_dfa2.getNodes())))

        #inputs = inputs from dfa1 and dfa2
        prodDFA.setInputVars(c_dfa1.getInputVars())
        for varNr in c_dfa1.getInputVars():
            prodDFA.setVarName(varNr, c_dfa1.getVarName(varNr))

        prodDFA.addInputVars(c_dfa2.getInputVars())
        for varNr in c_dfa2.getInputVars():
            prodDFA.setVarName(varNr, c_dfa2.getVarName(varNr))

        #outputs = outputs from dfa1 and dfa2
        prodDFA.setOutputVars(c_dfa1.getOutputVars())
        for varNr in c_dfa1.getOutputVars():
            prodDFA.setVarName(varNr, c_dfa1.getVarName(varNr))

        prodDFA.addOutputVars(c_dfa2.getOutputVars())
        for varNr in c_dfa2.getOutputVars():
            prodDFA.setVarName(varNr, c_dfa2.getVarName(varNr))

        initSubNodes1 = c_dfa1.getInitialNodes()
        initSubNodes2 = c_dfa2.getInitialNodes()

        for subNode1 in initSubNodes1:
            for subNode2 in initSubNodes2:
                init = ProductNode()
                init.appendSubNode(subNode1)
                init.copyErrorStatus(subNode1)
                init.appendSubNode(subNode2)
                init.copyErrorStatus(subNode2)
                prodDFA.addNode(init, True)

        workset=set(prodDFA.getNodes())

        if DEBUG:
            print("      ...start compute product")
            t = time.time()
        #build the product of df1 and df2
        while len(workset) > 0:
            state = workset.pop()
            state.setDone(True)

            sState1 = state.getSubNode(0)
            sState2 = state.getSubNode(1)

            for sEdge1 in sState1.getOutgoingEdges():
                for sEdge2 in sState2.getOutgoingEdges():
                    label1 = sEdge1.getLabel()
                    label2 = sEdge2.getLabel()
                    combLabel = label1.merge(label2)

                    if combLabel.isValidLabel():
                        targetState = ProductNode()
                        targetState.appendSubNode(sEdge1.getTargetNode())
                        targetState.copyErrorStatus(sEdge1.getTargetNode())
                        targetState.appendSubNode(sEdge2.getTargetNode())
                        targetState.copyErrorStatus(sEdge2.getTargetNode())
                        targetState = prodDFA.addNode(targetState)
                        prodDFA.addEdge(state, targetState, combLabel)

                        if not targetState.isDone():
                            workset.add(targetState)

        if DEBUG:
            elapsed_time = round(time.time() - t,2)
            print("      ....finished in " + str(elapsed_time))

        #set initial states
        for state in prodDFA.getNodes():
            isInitial = True
            for subState in state.getSubNodes():
                if not subState.isInitial():
                    isInitial = False
            state.setInitial(isInitial)

        #set final states
        for state in prodDFA.getNodes():
            isFinal = False
            for subState in state.getSubNodes():
                if subState.isFinal():
                    isFinal = True
            state.setFinal(isFinal)

        if DEBUG:
            print("      ...simplifyEdges")
            t = time.time()
        prodDFA.simplifyEdges()
        if DEBUG:
            elapsed_time = round(time.time() - t,2)
            print("      ....finished in " + str(elapsed_time))


        if DEBUG:
            print("      num states prodDFA = " + str(len(prodDFA.getNodes())))

        return prodDFA

    '''
    Returns a list of two DFAs. First dfa matches dfa1 and second dfa matches dfa2,
    except that common variables are used.

    '''
    def buildAutomatonWithCommonVariables(self, dfa1, dfa2):

        dfas = []

        c_dfa1 = DFA()
        c_dfa2 = DFA()

        joint_input_vars = set()
        joint_output_vars = set()

        c_var_nrs = dict()

        #compute joint input and output variables
        for var_nr in dfa1.getInputVars():
            joint_input_vars.add(dfa1.getVarName(var_nr))
        for var_nr in dfa2.getInputVars():
            joint_input_vars.add(dfa2.getVarName(var_nr))

        for var_nr in dfa1.getOutputVars():
            joint_output_vars.add(dfa1.getVarName(var_nr))
        for var_nr in dfa2.getOutputVars():
            joint_output_vars.add(dfa2.getVarName(var_nr))

        #set input and output variables
        var_count = 1
        for var_name in joint_input_vars:
            c_dfa1.addInputVar(var_count)
            c_dfa1.setVarName(var_count, var_name)
            c_dfa2.addInputVar(var_count)
            c_dfa2.setVarName(var_count, var_name)
            c_var_nrs[var_name] = var_count
            var_count = var_count + 1

        for var_name in joint_output_vars:
            c_dfa1.addOutputVar(var_count)
            c_dfa1.setVarName(var_count, var_name)
            c_dfa2.addOutputVar(var_count)
            c_dfa2.setVarName(var_count, var_name)
            c_var_nrs[var_name] = var_count
            var_count = var_count + 1


        #copy nodes from dfa1 and dfa2
        for node in dfa1.getNodes():
            c_node = DfaNode(node.getNr())
            c_node.setInitial(node.isInitial())
            c_node.setFinal(node.isFinal())
            c_node.copyErrorStatus(node)
            c_dfa1.addNode(c_node, True)

        for node in dfa2.getNodes():
            c_node = DfaNode(node.getNr())
            c_node.setInitial(node.isInitial())
            c_node.setFinal(node.isFinal())
            c_node.copyErrorStatus(node)
            c_dfa2.addNode(c_node, True)

        #copy edges from dfa1 and dfa2
        #note: labels from edges must be altered to use joint variables numbers
        for node in dfa1.getNodes():
            for egde in node.getOutgoingEdges():
                c_source = c_dfa1.getNode(egde.getSourceNode().getNr())
                c_target = c_dfa1.getNode(egde.getTargetNode().getNr())
                c_label = self.transformLabel(egde.getLabel(), dfa1, c_var_nrs)
                c_dfa1.addEdge(c_source, c_target, c_label)

        for node in dfa2.getNodes():
            for egde in node.getOutgoingEdges():
                c_source = c_dfa2.getNode(egde.getSourceNode().getNr())
                c_target = c_dfa2.getNode(egde.getTargetNode().getNr())
                c_label = self.transformLabel(egde.getLabel(), dfa2, c_var_nrs)
                c_dfa2.addEdge(c_source, c_target, c_label)


        dfas.append(c_dfa1)
        dfas.append(c_dfa2)

        return dfas

    '''
    Takes a label and a corresponding dfa, and returns a new label with
    variable numbers according to var_nr_map

    '''
    def transformLabel(self, label, dfa, var_nr_map):

        literals = label.getLiterals()

        if label.isValidLabel():
            c_literals = []
            for literal in literals:
                var_name = dfa.getVarName(abs(literal))
                c_literal = var_nr_map[var_name]
                if literal < 0:
                    c_literal = c_literal * -1
                c_literals.append(c_literal)
            c_label = DfaLabel(c_literals)
        else:
            c_label = DfaLabel(literals)

        return c_label


    '''
    Summarizes all unsafe states together into a single unsafe state. Once this state is reached,
    automaton stays in that unsafe state.

    '''
    def combineUnsafeStates(self):
        resultDfa = DFA()

        #add input vars
        resultDfa.setInputVars(self.getInputVars())
        for varNr in self.getInputVars():
            resultDfa.setVarName(varNr, self.getVarName(varNr))

        #add output vars
        resultDfa.setOutputVars(self.getOutputVars())
        for varNr in self.getOutputVars():
            resultDfa.setVarName(varNr, self.getVarName(varNr))

        #safety check only: check if all nodes (except initial nodes) have incoming and outgoing edges
        for node in self.getNodes():
            assert node.isInitial() or node.getIncomingEdgesNum() > 0
            assert node.getOutgoingEdgesNum() > 0


        #add safe nodes
        i=1
        nodeList = []
        for node in self.getNodes():
            if not node.isFinal():
                assert type(node) is ProductNode
                nodeList.append(node)
                resNode = ProductNode()
                resNode.setNr(i)
                resNode.setSubNodes(node.getSubNodes())
                resNode.setInitial(node.isInitial())
                resNode.setFinal(False)
                resNode.copyErrorStatus(node)
                resultDfa.addNode(resNode, True)
                i=i+1

        #add unsafe state
        errNode = ProductNode()
        errNode.setNr(i)
        errNode.setFinal(True)
        resultDfa.addNode(errNode, True)

        #add edge from error node to error node
        label = DfaLabel([])
        resultDfa.addEdge(errNode, errNode, label)

        #add edges for safe states
        for source in self.getNodes():
            if not source.isFinal():
                for edge in source.getOutgoingEdges():
                    target = edge.getTargetNode()
                    label = edge.getLabel()
                    sourceIdx = [i for i,x in enumerate(nodeList) if x == source]
                    resSource = resultDfa.getNode(sourceIdx[0]+1)
                    if not target.isFinal():
                        #copy edge
                        targetIdx = [i for i,x in enumerate(nodeList) if x == target]
                        resTarget = resultDfa.getNode(targetIdx[0]+1)
                        resultDfa.addEdge(resSource, resTarget, label)
                    else:
                        #redirect edge to error node
                        resultDfa.addEdge(resSource, errNode, label)

        #delete all nodes, with no incoming edges (states that can only be reached from error states)

        deleteNodes = []
        for node in resultDfa.getNodes():
            if (not node.isInitial()) and  node.getIncomingEdgesNum() == 0:
                deleteNodes.append(node)

        for node in deleteNodes:
            resultDfa.removeNode(node)

        resultDfa.simplifyEdges()

        return resultDfa.standardization()