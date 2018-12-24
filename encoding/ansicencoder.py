__author__ = 'meng wu'

import re

class AnsicEncoder(object):

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
        return shield_module



    """
    Builds an Verilog Module from a given shield model
    """
    def encodeShieldModel(self):

        enc = ""
        enc += self.encode_header()
        enc += self.encode_variables(self.shieldInputVarNames_, self.shieldOutputVarNames_)
        enc += self.encode_model(self.numOfShieldBits_, self.tmpCount_)
        enc += self.encode_transit(self.numOfShieldBits_)
        enc += '  return 0; \n}\n'
        return enc


    '''
    Returns header

    '''
    def encode_header(self):
        header = "//This file is automatically generated by Shield Synthesis tool.\n\n"

        header += "#include <stdbool.h>\n#include<z3.h>\n\n"

        return header


    '''
    Returns the declaration of all input and output, temporary, and state variables

    '''
    def encode_variables(self, input_vars, output_vars):

        var_enc = "struct IOVars{\n"

        #declare input and output variables
        for var_name in input_vars:
            var_enc += "  bool " + var_name + ";  //input\n"
        for var_name in output_vars:
            var_enc += "  bool " + var_name + ";  //output\n"
        var_enc += "};\n\n"


        return var_enc

    def encode_model(self, num_of_bits, tmp_count):
        mod = 'int shield( struct IOVars *var){\n'

        # encode temporary variables (wires)
        for statePos in range(0, num_of_bits):
            state_wire = "s" + str(statePos) + "n"
            mod += "  bool " + state_wire + " = 0;\n"

        for i in range(1, tmp_count):
            tmp_wire = "tmp" + str(i)
            mod += "  bool " + tmp_wire + " = 0;\n"

        # encode regs
        for statePos in range(0, num_of_bits):
            state = "s" + str(statePos)
            mod += "  static bool " + state + " = 0;\n"

        mod += self.shieldModel_
        return mod

    def encode_transit(self, num_of_bits):
        mod = '\n  //encode transition state\n'
        for statePos in range(0, num_of_bits):
            mod += "  s" + str(statePos) + " = " "s" + str(statePos) + "n;\n"
        return mod