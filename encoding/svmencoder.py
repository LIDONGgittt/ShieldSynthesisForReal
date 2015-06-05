__author__ = 'bkoenighofer'

import math

class SMVEncoder(object):
    '''
    Takes an automaton and the functions for the output variables and encodes them into smv.
    If no output functions are given, the output function is created from the automaton
    '''

    def __init__(self):
        self.dfas_ = dict() #correctness, deviation, specification and design dfa
        self.shieldModel_ = ""
        self.numOfShieldBits_ = 0
        self.shieldInputVarNames_ = []
        self.shieldOutputVarNames_ = []

    """
    Stores DFA in global variables
    """
    def addDFA(self, dfa_name, dfa):
        self.dfas_[dfa_name] = dfa


    """
    Stores DFA in global variables
    """
    def addShieldModel(self, shieldModel, numOfShieldBits):
        self.shieldModel_ = shieldModel
        self.numOfShieldBits_ = numOfShieldBits

    """
    Creates entire smv file, consisting of main, shield, design, correctness and  deviation Module
    and returns result as string
    """
    def getEncodedData(self):

        spec_dfa = self.dfas_["specification"]
        self.shieldInputVarNames_ = []
        for var in spec_dfa.getInputVars():
            self.shieldInputVarNames_.append(spec_dfa.getVarName(var))
        for var in spec_dfa.getOutputVars():
            self.shieldInputVarNames_.append(spec_dfa.getVarName(var))

        self.shieldOutputVarNames_ = []
        for var in spec_dfa.getOutputVars():
            var_name = spec_dfa.getVarName(var) + "__1"
            self.shieldOutputVarNames_.append(var_name)

        smv_res = ""

        smv_res += self.encodeShieldModel()

        if len(self.dfas_) > 1:
            smv_res += self.encodeAutomaton("design")
            smv_res += self.encodeAutomaton("correctness")
            smv_res += self.encodeAutomaton("deviation")
            smv_res += self.createMainModule()
            smv_res += self.createSpecification()

        return smv_res


    """
    Creates the LTL Specification that a Shield should be correct and
    should only produce an allowed number of deviations
    """
    def createSpecification(self):

        return "LTLSPEC G (!m_cshield.err & (m_deviation.err -> m_cdesign.err));"



    """
    Encodes the Main Module of the SMV File that connects all other modules
    """
    def createMainModule(self):

        design_dfa = self.dfas_["design"]
        correctness_dfa = self.dfas_["correctness"]

        smv_enc = "MODULE main\n"

        #encode input variables
        smv_enc += "VAR\n"

        for var in design_dfa.getInputVars():
            var_name = design_dfa.getVarName(var)
            smv_enc += "  " + var_name + ": boolean;\n"

        #create Design Module
        design_in_var_str = ""
        for var in design_dfa.getInputVars():
            var_name = design_dfa.getVarName(var)
            design_in_var_str += var_name + ", "
        design_in_var_str=design_in_var_str[0:len(design_in_var_str)-2]
        smv_enc += "  m_design: design(" + design_in_var_str  + ");\n"

        design_in_vars = []
        for var in design_dfa.getInputVars():
            design_in_vars.append(design_dfa.getVarName(var))

        design_out_vars = []
        for var in design_dfa.getOutputVars():
            design_out_vars.append(design_dfa.getVarName(var))


        #create Shield Module
        #shield in vars =  global in vars used in shield + design out vars used in shield
        #Note: not all design vars have to be present in the shield
        shield_in_var_str = ""
        for var_name in self.shieldInputVarNames_:
            if var_name in design_in_vars:
                shield_in_var_str += var_name + ", "
        shield_in_var_str=shield_in_var_str[0:len(shield_in_var_str)-2]

        for var_name in self.shieldInputVarNames_:
            if var_name in design_out_vars:
                if len(shield_in_var_str):
                     shield_in_var_str += ", "
                shield_in_var_str += "m_design." +  var_name
        smv_enc += "  m_shield: shield(" + shield_in_var_str  + ");\n"


        #create correctness Module for shield
        #correctness in vars = global in vars used in shield + shield out vars
        #Note: not all design in vars have to be present in the correctness dfa

        cshield_in_var_str = ""
        for var in correctness_dfa.getInputVars():
            var_name = correctness_dfa.getVarName(var)
            if var_name in design_in_vars:
                cshield_in_var_str += var_name + ", "
        cshield_in_var_str=cshield_in_var_str[0:len(cshield_in_var_str)-2]

        for var_name in self.shieldOutputVarNames_:
            if len(cshield_in_var_str):
                 cshield_in_var_str += ", "
            cshield_in_var_str += "m_shield." + var_name
        smv_enc += "  m_cshield: correctness(" + cshield_in_var_str  + ");\n"

        #create correctness Module for design
        #correctness in vars = global in vars used in shield + design out vars used in shield
        cdesign_in_var_str = shield_in_var_str
        smv_enc += "  m_cdesign: correctness(" + cdesign_in_var_str  + ");\n"

        #create Deviation Module
        # Deviation in vars = design out vars used in shield + shield out vars
        deviation_in_var_str = ""
        for var_name in self.shieldInputVarNames_:
            if var_name in design_out_vars:
                deviation_in_var_str += "m_design." + var_name + ", "
        for var_name in self.shieldOutputVarNames_:
            deviation_in_var_str += "m_shield." + var_name + ", "

        deviation_in_var_str=deviation_in_var_str[0:len(deviation_in_var_str)-2]
        smv_enc += "  m_deviation: deviation(" + deviation_in_var_str  + ");\n"

        smv_enc += "\n"
        return smv_enc

    """
    Builds an SMV Module from a given shield model
    """
    def encodeShieldModel(self):

        smv_enc = ""

        smv_enc += self.encode_header("shield", self.shieldInputVarNames_)
        smv_enc += self.encode_variables(self.numOfShieldBits_)
        smv_enc += self.encode_initial_state(self.numOfShieldBits_)
        smv_enc += self.encode_next_state_shield()
        smv_enc += self.encode_shield_transitions_and_outputs()
        smv_enc += "\n"

        return smv_enc


    """
    Encodes the next Outputs of the Shield Module using the shield model
    """

    def encode_shield_transitions_and_outputs(self):
        output_funcs = "DEFINE\n"

        for var_name in self.shieldOutputVarNames_:
            tmp_var_name = var_name + "_1"
            output_funcs += "  " + var_name + " := " + tmp_var_name + ";\n"

        output_funcs += "\n"
        output_funcs += self.shieldModel_

        output_funcs += "\n"

        return output_funcs

    """
    Encodes the next States of the Shield Module depending on shield model variables
    """

    def encode_next_state_shield(self):

        next_state_str = ""
        for state_pos in range(0, self.numOfShieldBits_):
            state_bit = "s" + str(state_pos)
            next_state_bit = state_bit + "n_1"
            next_state_str += "  next(" + state_bit + ") := " + next_state_bit + ";\n"

        return next_state_str



    """
    Encodes an automaton to an SMV Module
    """
    def encodeAutomaton(self, dfa_name):
        dfa = self.dfas_[dfa_name]

        num_of_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))

        input_var_names = []
        for var in dfa.getInputVars():
            input_var_names.append(dfa.getVarName(var))

        pos_func_by_var = self.create_func_by_var(dfa, True)
        neg_func_by_var = self.create_func_by_var(dfa, False)

        smv_enc = ""
        smv_enc += self.encode_header(dfa_name, input_var_names)
        smv_enc += self.encode_variables(num_of_bits)
        smv_enc += self.encode_initial_state(num_of_bits)
        smv_enc += self.encode_state_transitions(dfa)
        smv_enc += self.encode_output_functions(dfa_name, pos_func_by_var, neg_func_by_var)
        smv_enc += "\n"
        return smv_enc

    """
    Creates the output functions for all output variables from dfa
    """
    def create_func_by_var(self, dfa, sign):

        num_of_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))

        funcs_by_var = dict()
        for out_var in dfa.getOutputVars():
            if sign == False:
                 out_lit = -out_var
            else:
                out_lit = out_var


            func_for_var = []

            #check all transitions
            for node in dfa.getNodes():
                for edge in node.getOutgoingEdges():

                    #check if out_var occurs with correct sign in label
                    label = edge.getLabel()

                    if not set(label.getLiterals()).isdisjoint(set([out_lit])):
                        assignment = dict()

                        #add state
                        state_ass = dict()

                        bin_node_nr = bin(int(node.getNr()-1))[2:]
                        bin_str = "" + bin_node_nr.zfill(num_of_bits)

                        for state_bit in range(0,num_of_bits):
                            value = bin_str[num_of_bits-1-state_bit]
                            if value is "0":
                                state_ass[state_bit] = 0
                            else:
                                state_ass[state_bit] = 1

                        assignment["state"] = state_ass

                        #add input variable
                        vars_ass = dict()

                        input_literals = dfa.getInputLiterals(edge.getLabel())
                        for literal in input_literals:
                            if literal < 0:
                                vars_ass[int(math.fabs(literal))] = 0
                            else:
                                vars_ass[int(math.fabs(literal))] = 1

                        assignment["var"] = vars_ass
                        func_for_var.append(assignment)
            funcs_by_var[out_var] = func_for_var
        return funcs_by_var


    '''
    Returns header
    '''
    def encode_header(self, dfa_name, input_var_names):
        header = ""
        header += "MODULE " + dfa_name + "("

        for name in input_var_names:
            header += name + ", "
        if len(input_var_names)>0:
            header = header[0:len(header)-2]
        header += ")\n"

        return header


    '''
    Returns the declaration of all state variables
    '''
    def encode_variables(self, num_of_bits):

        var_enc = "VAR\n"
        #encode state bits
        for statePos in range(0, num_of_bits):
            state = "s" + str(statePos)
            var_enc += "  " + state + ": boolean;\n"

        var_enc += "\n"
        return var_enc

    '''
    Returns the encoding of the initial state
    '''
    def encode_initial_state(self, num_of_bits):

        initial_state = "ASSIGN\n"
        for statePos in range(0, num_of_bits):
            state_bit = "s" + str(statePos)
            initial_state += "  init(" + state_bit +") := FALSE;\n"

        initial_state += "\n"
        return initial_state

    '''
    Returns the encoding of the transition relation of the automaton

    '''
    def encode_state_transitions(self, dfa):

        num_of_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))

        transitions = ""

        for state_pos in range(0, num_of_bits):
            state_bit_name = "s" + str(state_pos)
            transitions += "  next(" + state_bit_name + ") := case\n"

            #find all transitions, where the bit "state_bit" is true in the next state

            for node in dfa.getNodes():
                curr_state_bits = self.get_state_bits(node.getNr()-1, num_of_bits)

                for edge in node.getOutgoingEdges():
                    next_state_bits = self.get_state_bits(edge.getTargetNode().getNr()-1, num_of_bits)

                    if(next_state_bits[state_pos]==state_bit_name):
                        #encode transition
                        transition = "    ("

                        #source state of transition
                        for curr_bit in curr_state_bits:
                            transition += curr_bit + " & "
                        transition=transition[0:len(transition)-3]

                        #input variables of transition
                        input_literals = dfa.getInputLiterals(edge.getLabel())
                        for literal in input_literals:
                            transition += " & "
                            if literal < 0:
                                transition += "!"
                            transition += dfa.varToName(int(math.fabs(literal)))

                        #next value of state bit
                        transition += ") | \n"

                        transitions += transition

            transitions=transitions[0:len(transitions)-4]
            transitions += " : TRUE;\n"
            #for all other transitions, the bit "state_bit is false in the next state
            transitions += "    TRUE   : FALSE;\n"

            transitions += "  esac;\n"

        transitions += "\n"
        return transitions


    '''
    Returns the encoding of the next values of the output variables of the automaton

    '''
    def encode_output_functions(self, dfa_name, pos_func_by_var_, neg_func_by_var_):

        dfa = self.dfas_[dfa_name]

        output_funcs = "DEFINE\n"

        for out_var in dfa.getOutputVars():
            var_name = dfa.getVarName(out_var)
            output_func = "  " + var_name + " := "

            #decide to use positive or negative definition of output variable
            sign = True

            func_by_var = pos_func_by_var_[out_var]

            if (len(neg_func_by_var_[out_var])==0 or len(pos_func_by_var_[out_var])==0):
                if len(neg_func_by_var_[out_var])==0:
                    output_func += "TRUE;\n"
                else:
                    output_func += "FALSE;\n"

            else:
                if len(neg_func_by_var_[out_var]) < len(pos_func_by_var_[out_var]):
                    sign = False
                    func_by_var = neg_func_by_var_[out_var]

                #append combinatorial logic for output variable
                if sign is False:
                    output_func += "!"
                    if len(func_by_var) > 1:
                        output_func += "("

                for assignment in func_by_var:
                    output_func += "("

                    state_assignment = assignment["state"]
                    for state_bit, state_bit_value in state_assignment.iteritems():
                        if state_bit_value == 0:
                            output_func += "!"
                        output_func += "s" + str(state_bit) + " & "

                    var_assignment = assignment["var"]
                    for var_nr, var_value in var_assignment.iteritems():
                        if var_value == 0:
                            output_func += "!"
                        output_func += dfa.getVarName(var_nr) + " & "

                    output_func=output_func[0:len(output_func)-3]
                    output_func += ")|\n        "

                output_func=output_func[0:len(output_func)-10]

                if sign is False:
                    if len(func_by_var) > 1:
                        output_func += ")"


                output_func += ";\n"
            output_funcs += output_func


        output_funcs += "\n"
        return output_funcs


    '''
    Transforms a state number into its bit representation.
    Returns the list with state bits.
    E.g. state_nr = 6, Return [!s0, s1, s2]

    '''
    def get_state_bits(self, state_nr, num_of_bits):

        state_bits = []

        binNodeNr = bin(int(state_nr))[2:]
        binStr = ""+binNodeNr.zfill(num_of_bits)

        for state_pos in range(0,num_of_bits):
            state_str = ""
            sign = binStr[num_of_bits-1-state_pos]
            if sign is "0":
                state_str += "!"
            state_str += "s" + str(state_pos)
            state_bits.append(state_str)

        return state_bits










