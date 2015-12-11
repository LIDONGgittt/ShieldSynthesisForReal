#!/usr/local/bin/python2.7
# encoding: utf-8
'''
shield -- shielded synthesis tool

shield is the first shield synthesize tool.

It defines classes_and_methods

@author:     Bettina Könighofer, Robert Könighofer

@copyright:  2014 IAIK, Graz University of Technology. All rights reserved.

@license:    license

@contact:    bettina.koennighofer@iaik.tugraz.at, robert.koenighofer@iaik.tugraz.at

@change: 2015/06/11 by mengwu@vt.edu
         implement of our new idea to compositionally synthesis the shield
'''

import sys
import os
import time

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
from checker.nusmv import NuSMV
from checker.vis import VIS

from parser.dfaparser import DfaParser
from algorithm.finiteDesignErrorAlgo import FiniteDesignErrorAlgo
from algorithm.kStabilizingAlgo import KStabilizingAlgo
from encoding.synthesizer import  Synthesizer
from encoding.svmencoder import SMVEncoder
from encoding.verilogencoder import VerilogEncoder
from datatypes.dfa import DFA

__all__ = []
__version__ = 0.1
__date__ = '2014-06-03'
__updated__ = '2014-06-04'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

SMV = 0
VERILOG = 1
AUTOMATON = 2

FINITE_ERROR_ALGORITHM = 0
K_STABILIZING_ALGORITHM = 1

MAX_DEVIATIONS = 3


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created on %s.
  Copyright 2014 IAIK, Graz University of Technology. All rights reserved.

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    t_total  = time.time()
    automata_time = t_total

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-a", "--algorithm", dest="algorithm", help="Used algorithm to synthesize shield. Support fealgo (finite design error algorithm) or ksalgo (k-stabilizing algorithm. [default: ksalgo]", default="ksalgo")
        parser.add_argument("-d", "--design", dest="design", help="concrete design to be load (written as automaton or in verilog)")
        parser.add_argument("-e", "--encoding", dest="encoding", help="encoding format of the output file. Support verilog or smv. [default: smv]", default="smv")
        parser.add_argument("-v", "--visspec", dest="visspec", help="specification input file for VIS model checker")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-c', '--compositional', dest='compo', action='store_true', help='generate compositional shield for each property specified.', default=False)
        parser.add_argument("-dev", "--deviation", dest="deviation", help="override the allowed deviation(assigned to 1 means must be greater than 1).[default: 1]", type=int, default=1)
        parser.add_argument('spec_file', nargs='+')

        #4 possible options to run the program:
        #
        #Case 1: Input: Spec automaton
        #        Output: Shield in SMV
        #        Arguments: spec_filename
        #
        #Case 2: Input: Spec automaton, Design Automaton:
        #        Output: SMV File with Main, Shield, and Design Module, Verification Result from NuSMV,
        #        Arguments: -d design_filename spec_filename
        #
        #Case 3: Input: Spec automaton
        #        Output: Shield in Verilog;
        #        Arguments: -e verilog spec_filename
        #
        #Case 4: Input: Spec automaton, Design Module in Verilog, VIS Spec File in LTL;
        #        Output: Verilog File with Main, Shield and Design Module, Verification Result from VIS,
        #        Arguments: -d design_filename -v visspec_filename -e verilog spec_filename


        # Process arguments
        args = parser.parse_args()

        if not args.encoding == "smv" and not args.encoding == "verilog":
            parser.print_usage()
            print("ERROR: ENCODING has to be 'smv' or 'verilog'!")
            sys.exit(-1)
            
        if not args.algorithm == "fealgo" and not args.algorithm == "ksalgo":
            parser.print_usage()
            print("ERROR: ALGORITHM has to be 'fealgo' or 'ksalgo'!")
            sys.exit(-1)
        

           
        if args.deviation >0:
            allowed_dev = args.deviation
        else:
            parser.print_usage()
            print("ERROR: DEVIATION has to be greater than 1!")
            sys.exit(-1)
        
        encoding = SMV
        if args.encoding=="verilog":
            encoding = VERILOG

        shield_algorithm = K_STABILIZING_ALGORITHM
        if args.algorithm=="fealgo":
            shield_algorithm = FINITE_ERROR_ALGORITHM

        compostional_shield = False  
        if args.compo:
            compostional_shield = True  
            shield_algorithm = K_STABILIZING_ALGORITHM  # FIXME: for compositional synthesis, block finite_error algorithm
            
        spec_files = args.spec_file
        design_dfa = None
        design_present = True
        if not args.design:
            design_present = False
        else:
            design_file =  args.design
            #parse design file
            if encoding == SMV:   #FIXME: cannot have smv design file and want to produce a verilog output file?
                #design must be an automaton
                dfa_parser = DfaParser(design_file)
                design_dfa = dfa_parser.getParsedDFA()
            else:
                #design must be a verilog module
                with open (design_file, "r") as myfile:
                    verilog_design_str=myfile.read()

        visspec_present = False
        if args.visspec:
            visspec_present = True
            vis_spec = args.visspec

        if visspec_present and encoding == SMV:
            print("\n[WARNIG:] Changed encoding to verilog. Otherwise no verification with VIS possible.\n")
            encoding = VERILOG

        #output file name is a combination of all input file names
        output_file_name = ''
        if compostional_shield:
            output_file_name="output/imp/c_"
        else:
            output_file_name="output/imp/"   
            
        for input_file in spec_files:
            input_file_name = input_file.split("/")
            input_file_name = input_file_name[len(input_file_name)-1]
            input_file_name = input_file_name.split(".")[0]
            output_file_name+=input_file_name+"_"
        output_file_name = output_file_name[:-1]  
        
    

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


    #print initial message
    print("************************************************")
    print("* Setup for Shield Synthesis:")

    if encoding == VERILOG:
        print("** Output File in Verilog Format")
    else:
        print("** Output File in SMV Format")

    if shield_algorithm == FINITE_ERROR_ALGORITHM:
        print("** Used Synthesis Algorithm: Finite-Design-Error Algorithm")
    else:
        print("** Used Synthesis Algorithm: k-stabilizing Shield Algorithm")

    if encoding == SMV and not design_present:
        print("** No design file specified. No verification with NuSMV")

    if encoding == VERILOG and (not visspec_present or not design_present):
        print("** No VIS Specification or Design file present. No verification with VIS")
    
    if compostional_shield:
        print("** Generate compositional shields for each property")
    else:
        print("** Generate one unified shield for all properties")

    print("** Used specification automaton input files:")
    for spec_file in spec_files:
        print("*** "+ spec_file)

    print("************************************************\n")

    #build specification DFA
    spec_dfas=[]
    
    if compostional_shield:
        for i in range(0, len(args.spec_file)):
            dfa_parser = DfaParser(args.spec_file[i])
            spec_dfas.append(dfa_parser.getParsedDFA())
    else:
        dfa_parser = DfaParser(args.spec_file[0])   
        prod_dfa = dfa_parser.getParsedDFA()
        
        for i in range(1, len(args.spec_file)):
            dfa_parser = DfaParser(args.spec_file[i])
            spec_dfa_2 = dfa_parser.getParsedDFA()
            
            #design_dfa = spec_dfa_2 # TODO: test code
            prod_dfa = prod_dfa.buildProductOfAutomata(spec_dfa_2, True)
            prod_dfa = prod_dfa.combineUnsafeStates()
            prod_dfa = prod_dfa.standardization(True)
        spec_dfas.append(prod_dfa)
    

    # build Correctness Automaton, Error Tracking Automaton and Deviation Automaton
    # and synthesize output functions for shield
    allowed_burst = 3
    if shield_algorithm == K_STABILIZING_ALGORITHM:
        algorithm = KStabilizingAlgo(spec_dfas, allowed_dev, allowed_burst)
    else:
        print 'This version does not support Finite Design Error algorithm'
        return
        #algorithm = FiniteDesignErrorAlgo(spec_dfas[0], 1, allowed_dev)
    automata_time = round(time.time() - t_total,2)
    print("*** Automaton Construction time: " + str(automata_time) + "        ***")
    
    finalNode = algorithm.etDFAs_[0].getFinalNodes()[0]

    if finalNode.getIncomingEdgesNum()==1:
        print "This is a perfect shield!"
    else:
        print "This is NOT a perfect shield!"
    synthesis = Synthesizer(shield_algorithm, allowed_dev, compostional_shield)
    synthesis.synthesize(algorithm.etDFAs_, algorithm.sdDFA_, algorithm.scDFA_)
    
    
    while not synthesis.existsWinningRegion():
        #synthesis = None    #give GC time to destroy previous manager instance
        allowed_dev = allowed_dev + 1
        if allowed_dev >= MAX_DEVIATIONS:
            print "Killing because of deviation counter greater than " + str(MAX_DEVIATIONS)
            sys.exit(99)
        print("allowed_dev=" + str(allowed_dev))

        algorithm = KStabilizingAlgo(spec_dfas, allowed_dev, allowed_burst)
        
        del synthesis
        synthesis = Synthesizer(shield_algorithm, allowed_dev, compostional_shield)
        synthesis.synthesize(algorithm.etDFAs_, algorithm.sdDFA_, algorithm.scDFA_)
        #synthesis = Synthesizer(shield_algorithm, allowed_dev, algorithm.etDFA_, algorithm.sdDFA_, algorithm.scDFA_, algorithm.drDFA_)
    
    # for compositional synthesis, there will be more than one spec_dfa
    # so we update design_dfa to include the property just synthesized
    final_dfa = algorithm.finalDFA_ 
    
    
    
            
    
    #create output file and verify shield
    

    
    verify = False
    result = True
    t_verify = 0
    verify_time = 0
    if encoding == SMV:
        if design_present:
            #Outputfile of the Shield module, the Design module and a Main Module connecting both of them
            #Afterwards, verification with SMV
            verify = True
            correctness_dfa = final_dfa.createVerificationDfa()
            deviation_dfa= algorithm.sdDFA_.createVerificationDfa()

            smv_encoder = SMVEncoder()
            smv_encoder.addShieldModel(synthesis.getResultModel(encoding), synthesis.getNumOfBits())
            smv_encoder.addDFA("design", design_dfa)
            smv_encoder.addDFA("correctness", correctness_dfa)
            smv_encoder.addDFA("deviation", deviation_dfa)
            smv_encoder.addDFA("specification", final_dfa)
            smv_str = smv_encoder.getEncodedData()

            with open(output_file_name+".smv", "w+") as text_file:
                text_file.write(smv_str)

            t_verify = time.time()
            smv_checker = NuSMV()
            result = smv_checker.check(smv_str)
            verify_time = round(time.time() - t_verify,2)
        else:
            #no verification, Output File contains only Shield Module
            smv_encoder = SMVEncoder()
            smv_encoder.addShieldModel(synthesis.getResultModel(encoding), synthesis.getNumOfBits())
            smv_encoder.addDFA("specification", final_dfa)
            smv_str = smv_encoder.getEncodedData()
            with open(output_file_name+".smv", "w+") as text_file:
                text_file.write(smv_str)

    else: #encoding = VERILOG
        if visspec_present and design_present:
            #Outputfile of the Shield module, the Design module and a Main Module connecting both of them
            #Afterwards, verification with VIS
            verify = True
            verilog_encoder = VerilogEncoder(final_dfa)
            verilog_encoder.addShieldModel(synthesis.getResultModel(encoding), synthesis.getNumOfBits(), synthesis.getTmpCount())
            verilog_encoder.addDesignModel(verilog_design_str)
            verilog_str = verilog_encoder.getEncodedData()

            with open(output_file_name+".v", "w+") as text_file:
                text_file.write(verilog_str)

            t_verify = time.time()
            vis = VIS()
            vis.readVerilog(output_file_name+".v")
            vis.flattenHierarchy()
            vis.staticOrder()
            vis.buildPartitionMdds()
            result = vis.ltlModelCheck(vis_spec)
            vis.quit()
            verify_time = round(time.time() - t_verify,2)
        else:
            #no verification, Output File contains only Shield Module
            verilog_encoder = VerilogEncoder(final_dfa)
            verilog_encoder.addShieldModel(synthesis.getResultModel(encoding), synthesis.getNumOfBits(), synthesis.getTmpCount())
            verilog_str = verilog_encoder.getEncodedData()

            with open(output_file_name+".v", "w+") as text_file:
                text_file.write(verilog_str)
    synthesis.inc_loop()

    #print final message
    total_time = round(time.time() - t_total,2)

    print("******************************************")
    print("*** Final Spec Automaton:        ***")
    print("**** num states: " + str(final_dfa.getNodeNum()) + "        ***")
    print("**** num edges: " + str(final_dfa.getNumEdges()) + "        ***")
    print("**** num inputs: " + str(len(final_dfa.getInputVars())) + "        ***")
    print("**** num outputs " + str(len(final_dfa.getOutputVars())) + "        ***")
    if verify:
        print("*** Time for synthesis: " + str(total_time-verify_time) + "       ***")
        print("*** Time for verification: " + str(verify_time) + "       ***")
    print("*** Total execution time: " + str(total_time) + "        ***")
    print("******************************************")

    if result:
        return 101
    else:
        return 100
    
    
if __name__ == "__main__":
    sys.exit(main())