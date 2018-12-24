#!/usr/local/bin/python2.7
# encoding: utf-8
'''
shield -- shielded synthesis tool for real

shield is the a shield synthesize tool based on the tool of shield synthesis tool by Bettina Könighofer and Robert Könighofer.

extension of original tool to handle real domains

@author:     Meng Wu

@contact:    mengwu@vt.edu

'''

import sys
import os
import time

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from parser.dfaparser import DfaParser
from algorithm.kStabilizingAlgo import KStabilizingAlgo
from algorithm.burstErrorAlgo import BurstErrorAlgo
from encoding.synthesizer import  Synthesizer
from encoding.synthesizer_old import  Synthesizer_kstab
from encoding.ansicencoder import AnsicEncoder
from encoding.verilogencoder import VerilogEncoder
__all__ = []
__version__ = 0.11
__date__ = '2018-12-14'
__updated__ = '2018-12-14'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

SMV = 0
VERILOG = 1
ANSIC = 2

BURST_ERROR_ALGORITHM = 0
K_STABILIZING_ALGORITHM = 1
REAL_ALGORITHM = 2

MAX_DEVIATIONS = 4


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
  Copyright 2018, Virginia Polytechnic Institute and State University. All rights reserved.

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    t_total  = time.time()
    automata_time = t_total

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-a", "--algorithm", dest="algorithm", help="Used algorithm to synthesize shield. Support ksalgo (k-stabilizing algorithm), bealgo (burst error algorithm or realgo (real domain algorithm). [default: realgo]", default="realgo")
#         parser.add_argument("-d", "--design", dest="design", help="concrete design to be load (written as automaton or in verilog)")
        parser.add_argument("-e", "--encoding", dest="encoding", help="encoding format of the output file. Support verilog or ansic. [default: ansic]", default="ansic")
#         parser.add_argument("-v", "--visspec", dest="visspec", help="specification input file for VIS model checker")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-f', '--fastSynthesis', dest='fast', action='store_true', help='compute winning region using implication. Only valid when algorithm is set to bealgo.', default=False)
        parser.add_argument("-dev", "--deviation", dest="deviation", help="override the allowed deviation(assigned to 1 means must be greater than 1). Only valid when algorithm is set to ksalgo.[default: 1]", type=int, default=1)
        parser.add_argument('spec_file', nargs='+')

        # Process arguments
        args = parser.parse_args()

        if args.encoding=="verilog":
            encoding = VERILOG
        elif args.encoding=="ansic":
            encoding = ANSIC
        else:
            print("ERROR: Unknown encoding!")
            sys.exit(-1)

        fast_syn = False

        if args.algorithm == "bealgo":
            if args.deviation >1:
                print("Warning: deviation option has no effect in burst error algorithm!")
            if args.fast:
                fast_syn = True

        elif args.algorithm == "ksalgo":
            shield_algorithm = K_STABILIZING_ALGORITHM
            if args.deviation >0:
                allowed_dev = args.deviation
            else:
                parser.print_usage()
                print("ERROR: DEVIATION has to be greater than 1!")
                sys.exit(-1)
            if args.fast:
                print("Warning: right now fastSynthesis option is not supported in k-stabilizing algorithm!")
        elif args.algorithm == "realgo":
            shield_algorithm = REAL_ALGORITHM
            if args.deviation >1:
                print("Warning: deviation option has no effect in real algorithm!")
            if args.fast:
                print("Warning: fastSynthesis option is not supported in real algorithm!")
        else:
            parser.print_usage()
            print("ERROR: Unknown algorithm!")
            sys.exit(-1)


        spec_files = args.spec_file

        #output file name is a combination of all input file names
        if fast_syn:
            output_file_name="output/f_"
        else:
            output_file_name="output/"

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
    elif encoding == ANSIC:
        print("** Output File in ANSIC Format")
    elif encoding == ANSIC:
        print("** Output File in SMV Format")

    if shield_algorithm == K_STABILIZING_ALGORITHM:
        print("** Used Synthesis Algorithm: K-stabilizing Algorithm")
    elif shield_algorithm == BURST_ERROR_ALGORITHM:
        print("** Used Synthesis Algorithm: Burst Error Algorithm")
    else:
        print("** Used Synthesis Algorithm: Real Algorithm")

    if fast_syn:
        print("** Use implication to compute winning region")
    else:
        print("** Use standard algorithm to compute winning region")

    print("** Used specification automaton input files:")
    for spec_file in spec_files:
        print("*** "+ spec_file)

    print("************************************************\n")
    print("******************************************")
    #build specification DFA

    dfa_parser = DfaParser(args.spec_file[0])
    prod_dfa = dfa_parser.getParsedDFA()

    for i in range(1, len(args.spec_file)):
        dfa_parser = DfaParser(args.spec_file[i])
        spec_dfa_2 = dfa_parser.getParsedDFA()

        prod_dfa = prod_dfa.buildProductOfAutomata(spec_dfa_2, True)
        prod_dfa = prod_dfa.combineUnsafeStates()
        prod_dfa = prod_dfa.standardization(True)
    spec_dfa= prod_dfa


    # build Correctness Automaton, Error Tracking Automaton and Deviation Automaton
    # and synthesize output functions for shield
    allowed_burst = 0

    if shield_algorithm == BURST_ERROR_ALGORITHM:
        algorithm = BurstErrorAlgo(spec_dfa, allowed_burst)
        automata_time = round(time.time() - t_total,2)
        print("*** ET Automaton Construction time: " + str(automata_time))
        print("*** ET Automaton Size: " + str(algorithm.etDFA_.getNodeNum())+'/'+str(len(algorithm.etDFA_.getEdges())))
        if allowed_burst>0:
            finalNode = algorithm.etDFA_.getFinalNodes()[0]
            if finalNode.getIncomingEdgesNum()==1:
                print "This is a perfect shield!"
            else:
                print "This is NOT a perfect shield!"

        synthesis = Synthesizer(shield_algorithm, allowed_burst, fast_syn)
        synthesis.synthesize(algorithm.etDFA_, algorithm.sdDFA_, algorithm.scDFA_)
#         print "spec:"
#         print spec_dfa
#         print "et:"
#         print algorithm.etDFA_
#         print "dev:"
#         print algorithm.sdDFA_
#         print "correct:"
#         print algorithm.scDFA_
#
#         print "et and sd:"
#         et_sd_DFA = algorithm.etDFA_.buildProductOfAutomata(algorithm.sdDFA_, True)
#         et_sd_DFA = et_sd_DFA.combineUnsafeStates()
#         et_sd_DFA = et_sd_DFA.standardization(True)
#         print et_sd_DFA
#         print "game:"
#         game_DFA = et_sd_DFA.buildProductOfAutomata( algorithm.scDFA_, True)
#        game_DFA = game_DFA.combineUnsafeStates()
#        game_DFA = game_DFA.standardization(True)
#         print game_DFA

        while not synthesis.existsWinningRegion():
            print 'ERROR: Winning Region cannot find in burst error algorithm!'
            sys.exit(404)

    else:
        algorithm = KStabilizingAlgo(spec_dfa, allowed_dev)

        cur_time = time.time()
        automata_time = round(cur_time - t_total,2)
        pre_time = cur_time
        print("*** Automaton Construction time for k="+str(allowed_dev)+": "+ str(automata_time))
        print("*** ET Automaton Size: " + str(algorithm.etDFA_.getNodeNum())+'/'+str(len(algorithm.etDFA_.getEdges())))


        synthesis = Synthesizer_kstab(shield_algorithm, allowed_dev, algorithm.etDFA_, algorithm.sdDFA_, algorithm.scDFA_)

        while not synthesis.existsWinningRegion():
            synthesis = None    #give GC time to destroy previous manager instance
            allowed_dev = allowed_dev + 1
            if allowed_dev == MAX_DEVIATIONS:
                print "Killing because of deviation counter = " + str(MAX_DEVIATIONS)
                sys.exit(99)
#             print("allowed_dev=" + str(allowed_dev))

            algorithm = KStabilizingAlgo(spec_dfa, allowed_dev)


            cur_time = time.time()
            automata_time = round(cur_time - pre_time,2)
            pre_time = cur_time
            print("*** Automaton Construction time for k="+str(allowed_dev)+": "+ str(automata_time))
            print("*** ET Automaton Size: " + str(algorithm.etDFA_.getNodeNum())+'/'+str(len(algorithm.etDFA_.getEdges())))
            synthesis = Synthesizer_kstab(shield_algorithm, allowed_dev, algorithm.etDFA_, algorithm.sdDFA_, algorithm.scDFA_)

    #create output file and verify shield

    verify = False
    result = True
    t_verify = 0
    verify_time = 0
    if encoding == SMV:
        pass

    elif encoding == VERILOG:
        #no verification, Output File contains only Shield Module
        verilog_encoder = VerilogEncoder(spec_dfa)
        verilog_encoder.addShieldModel(synthesis.getResultModel(encoding), synthesis.getNumOfBits(), synthesis.getTmpCount())
        verilog_str = verilog_encoder.getEncodedData()

        with open(output_file_name+".v", "w+") as text_file:
            text_file.write(verilog_str)
    else: #encoding = ANSIC
        ansic_encoder = AnsicEncoder(spec_dfa)
        ansic_encoder.addShieldModel(synthesis.getResultModel(encoding), synthesis.getNumOfBits(), synthesis.getMaxTmpCount())
        ansic_str = ansic_encoder.getEncodedData()

        with open(output_file_name+".c", "w+") as text_file:
            text_file.write(ansic_str)


    #print final message
    total_time = round(time.time() - t_total, 2)

    
    print("*** Final Spec Automaton:")
    print("***     num states: " + str(spec_dfa.getNodeNum()))
    print("***     num edges: " + str(spec_dfa.getNumEdges()))
    print("***     num inputs: " + str(len(spec_dfa.getInputVars())))
    print("***     num outputs: " + str(len(spec_dfa.getOutputVars())))
    if verify:
        print("*** Time for synthesis: " + str(total_time-verify_time))
        print("*** Time for verification: " + str(verify_time))
    print("*** Total execution time: " + str(total_time))
    print("*** Num wining states: "+ str(synthesis.winStateNum)+"/"+str(synthesis.allStateNum))
    print("******************************************")

    if result:
        return 101
    else:
        return 100
    
    
if __name__ == "__main__":
    sys.exit(main())