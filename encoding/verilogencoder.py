__author__ = 'bkoenighofer'

import math
import re

class VerilogEncoder(object):

    def __init__(self, specDFA):
        self.specDFA = specDFA
        self.shieldModel_= ""
        self.numOfShieldBits_ = 0
        self.tmpCount_ = 0
        self.designModel_ = []
        self.designModelStr_ = ""
        self.shieldInputVarNames_ = []
        self.shieldOutputVarNames_ = []


    """
    Stores DFA in global variables
    """
    def addShieldModel(self, shieldModel, numOfShieldBits, tmpCount):
        self.shieldModel_ = shieldModel
        self.numOfShieldBits_ = numOfShieldBits
        self.tmpCount_= tmpCount

    """
    Stores DFA in global variables
    """
    def addDesignModel(self, designModel):
        self.designModel_= designModel.split('\n')
        self.designModelStr_= designModel

    """
    Creates entire verilog file, consisting of main, shield, design Module
    and returns result as string
    """
    def getEncodedData(self):

        for var in self.specDFA.getInputVars():
            self.shieldInputVarNames_.append(self.specDFA.getVarName(var))
        for var in self.specDFA.getOutputVars():
            self.shieldInputVarNames_.append(self.specDFA.getVarName(var))

        for var in self.specDFA.getOutputVars():
            var_name = self.specDFA.getVarName(var) + "__1"
            self.shieldOutputVarNames_.append(var_name)

        shield_module = self.encodeShieldModel()
        if len(self.designModel_)== 0:
            return shield_module

        verilog_res = ""

        #add constants from design
        design_header = ""
        design_module = ""

        #build design header
        line_count = 0
        for line in self.designModel_:
            line = line.strip()
            line = re.sub(' +',' ',line)
            if line.startswith("module"):
                break
            design_header += line + '\n'
            line_count = line_count + 1
        self.designModel_ = self.designModel_[line_count:]

        #build design module
        for line in self.designModel_:
            design_module += line + '\n'

        verilog_res = design_header
        verilog_res += self.createMainModule()
        verilog_res += shield_module
        verilog_res += design_module

        return verilog_res

    """
    Builds an Verilog Module from a given shield model
    """
    def encodeShieldModel(self):

        enc = ""

        enc += self.encode_header("shield", ["clock"] + self.shieldInputVarNames_ + self.shieldOutputVarNames_)
        enc += self.encode_variables(self.shieldInputVarNames_, self.shieldOutputVarNames_, self.numOfShieldBits_, self.tmpCount_)
        enc += self.shieldModel_
        enc += self.encode_initial_block(self.shieldInputVarNames_, self.shieldOutputVarNames_, self.numOfShieldBits_)
        enc += self.encode_always_block(self.shieldInputVarNames_, self.shieldOutputVarNames_, self.numOfShieldBits_)
        enc += "endmodule\n\n"

        return enc



    """
    Encodes the Main Module of the Verilog File that connects Design and Shield to one module
    """
    def createMainModule(self):

        #design module could define more modules. parse variables only from design module.
        module_str = ""
        for line in self.designModel_[1:]:
            line = line.strip()
            line = re.sub(' +', ' ', line)
            if line.startswith("endmodule"):
                break
            module_str += line + '\n'
        design_input_vars = self.parseVariables(module_str, True)
        design_output_vars = self.parseVariables(module_str, False)

        enc = ""
        enc += self.encode_header("main", design_input_vars+design_output_vars)


        #encode_variables

        #declare inputs and outputs
        for var in design_input_vars:
            enc += "  input " + var + ";\n"
        for var in design_output_vars:
            enc += "  output " + var + ";\n"
        enc += "\n"

        #declare wires (design outputs that are also shield inputs)
        shield_inputs_from_design = []
        for shield_in_var in self.shieldInputVarNames_:
            if shield_in_var in design_output_vars:
                enc += "  wire " + shield_in_var + "_design;\n"
                shield_inputs_from_design.append(shield_in_var)
        enc += "\n"

        #define design (outputs of design that are also inputs for shield are renamed)
        design_var_list = []
        for in_var in design_input_vars:
            design_var_list.append(in_var)
        for out_var in design_output_vars:
            if out_var in shield_inputs_from_design:
                design_var_list.append(out_var+"_design")
            else:
                design_var_list.append(out_var)

        design_vars = ""
        for var in design_var_list:
            design_vars += var + ", "
        design_vars=design_vars[0:len(design_vars)-2]

        enc += "  design m_design(" + design_vars + ");\n"

        #define shield
        if "clock" in design_var_list:
            shield_vars = "clock, "
        else:
            shield_vars = "clk, "
        for var in self.shieldInputVarNames_:
            if var in shield_inputs_from_design:
                shield_vars += var + "_design, "
            else:
                shield_vars += var + ", "
        #shiled output variables without terminating "1"
        for var in shield_inputs_from_design:
            shield_vars += var + ", "
        shield_vars=shield_vars[0:len(shield_vars)-2]

        enc += "  shield m_shield(" + shield_vars  + ");\n\n"

        enc += "endmodule\n\n"""

        return enc


    '''
    Returns header

    '''
    def encode_header(self, dfa_name, var_names):
        header = ""
        header += "module " + dfa_name + "("

        for name in var_names:
            header += name + ", "

        header = header[0:len(header)-2]
        header += ");\n"

        return header


    '''
    Returns the declaration of all input and output, temporary, and state variables

    '''
    def encode_variables(self, input_vars, output_vars, num_of_bits, tmp_count):

        var_enc = ""

        #declare input and output variables
        var_enc += "  input clock;\n"
        for var_name in input_vars:
            var_enc += "  input " + var_name + ";\n"
        for var_name in output_vars:
            var_enc += "  output " + var_name + ";\n"
        var_enc += "\n"


        #encode temporary variables (wires)
        for statePos in range(0, num_of_bits):
            state_wire = "s" + str(statePos) + "n"
            var_enc += "  wire " + state_wire + ";\n"

        for i in range(1, tmp_count):
            tmp_wire = "tmp" + str(i)
            var_enc += "  wire " + tmp_wire + ";\n"
        var_enc += "\n"

        #encode regs
        for statePos in range(0, num_of_bits):
            state = "s" + str(statePos)
            var_enc += "  reg " + state + ";\n"
        var_enc += "\n"

        return var_enc


    '''
    Returns the encoding of the initial block (init of reg variables)

    '''
    def encode_initial_block(self, input_vars, output_vars, num_of_bits):

        initial_state = "  initial\n"
        initial_state += "   begin\n"
        for statePos in range(0, num_of_bits):
            state_bit = "s" + str(statePos)
            initial_state += "    " + state_bit +" = 0;\n"
        initial_state += "   end\n\n"
        return initial_state

    '''
    Returns the encoding of the always block (update of state variables)

    '''
    def encode_always_block(self, input_vars, output_vars, num_of_bits):

        always_block = "  always @(posedge clock)\n"
        always_block += "   begin\n"
        for statePos in range(0, num_of_bits):
            state_bit = "s" + str(statePos)
            always_block += "    " + state_bit +" = "+ state_bit +"n;\n"
        always_block += "   end\n"
        return always_block

    '''
    Parses all variables from a given Verilog Module.
    If parseInputs=True, the function returns all input variables (except clock), otherwise the output variables.

    '''
    def parseVariables(self, verilogModule, parseInputs):

        variables=[]
        for line in verilogModule.split('\n'):
            line = line.strip()
            line = re.sub(' +',' ',line)
            if parseInputs:
                if line.startswith("input"):
                    var = line.split(" ")[1][:-1]
                    variables.append(var)
            else:
                if line.startswith("output"):
                    var = line.split(" ")[1][:-1]
                    variables.append(var)
        return variables


