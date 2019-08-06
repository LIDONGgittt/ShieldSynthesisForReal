'''
Created on Jun 10, 2014

@author: bkoenighofer
'''

 # -*- coding: utf-8 -*-

import pycudd
import math
import time
from datatypes.dfa import DFA
from datatypes.productnode import ProductNode
from datatypes.dfalabel import DfaLabel

FINITE_ERROR_ALGORITHM = 0
K_STABILIZING_ALGORITHM = 1

NUSMV = 0
VERILOG = 1
ANSIC = 2

class Synthesizer_kstab(object):
    '''
    Takes an "Error Tracking", a "Correctness" and a "Deviation" DFA. Synthesizer computes
    the product, but with special rules for final states, according to the used Shield-Algorithm.
    The final synthesis result can be given in Verilog or SMV.
    '''

    def __init__(self, algorithm, num_shield_deviations, error_tracking_dfa, deviation_dfa, correctness_dfa,
                 feasibility_dfa=None, relax_dfa=None):
        #print ("======================================\n synthesis  \n======================================\n")
        #init pycudd
        self.mgr_ = pycudd.DdManager()
        self.mgr_.SetDefault()

        #init member vars
        self.algorithm_ = algorithm
        self.num_shield_deviations_ = num_shield_deviations
        self.allowed_design_error_ = 1

        self.error_tracking_dfa_ = error_tracking_dfa.unify()
        self.deviation_dfa_ = deviation_dfa.unify()
        self.correctness_dfa_ = correctness_dfa.unify()

        self.error_tracking_dfa_.setName("error tracking dfa")
        self.deviation_dfa_.setName("deviation dfa")
        self.correctness_dfa_.setName("correctness dfa")

        self.dfa_list_ = [self.error_tracking_dfa_, self.deviation_dfa_, self.correctness_dfa_]
        self.feasibility_dfa_ = None
        self.relax_dfa_ = None

        if feasibility_dfa:
            self.feasibility_dfa_ = feasibility_dfa.unify()
            self.feasibility_dfa_.setName("feasibility dfa")
            self.dfa_list_ += [self.feasibility_dfa_]
        else:
            self.feasibility_dfa_ = None

        if relax_dfa:
            self.relax_dfa_ = relax_dfa.unify()
            self.relax_dfa_.setName("design relax dfa")
            self.dfa_list_ += [self.relax_dfa_]

        self.input_vars_ = []
        self.output_vars_ = []
        self.in_out_var_names_ = dict()
        self.num_of_bits_ = 0
        self.var_names_ = [] #list of all state bits, input and output variabes

        self.state_offsets_ = dict()
        self.var_bdds_ = dict()

        self.init_state_bdd_ = self.mgr_.One()
        self.transition_bdd_ = self.mgr_.One()
        self.err_state_bdd_ = self.mgr_.Zero()
        self.win_region_ = self.mgr_.Zero()

        self.tmp_count_= 1
        self.max_tmp_count = 1
        self.result_model_ = ""

        self.winStateNum = 0
        self.allStateNum = 0

    def synthesize_real(self):

        synthe_0 = time.time()
        for dfa in self.dfa_list_:
            # add input vars
            for input_var in dfa.getInputVars():
                if input_var not in self.input_vars_:
                    self.input_vars_.append(input_var)
                    self.in_out_var_names_[input_var] = dfa.getVarName(input_var)
            # add output vars
            for output_var in dfa.getOutputVars():
                if output_var not in self.output_vars_:
                    self.output_vars_.append(output_var)
                    self.in_out_var_names_[output_var] = dfa.getVarName(output_var)

        # encode states and create init_state
        # (create state bdds for all state bits of all automata)
        state_order = self.encode_states()

        self.create_init_states(self.dfa_list_)
        # encode variables
        var_order = self.encode_variables()

        # build next state vars
        self.next_state_vars_bdd_ = []
        for state_pos in range(0, self.num_of_bits_):
            self.next_state_vars_bdd_.append(self.var_bdds_['s' + str(self.num_of_bits_ - 1 - state_pos) + 'n'])

        # build input variables bdds
        self.in_var_bdds_ = []
        for var in self.input_vars_:
            self.in_var_bdds_.append(self.var_bdds_["v" + str(var - 1)])

        # build output variables bdds
        self.out_var_bdd_ = []
        for var in self.output_vars_:
            self.out_var_bdd_.append(self.var_bdds_["v" + str(var - 1)])

        transition_bdds = []
        for dfa in self.dfa_list_:
            transition_bdd = self.encode_transitions(dfa)
            # print dfa
            # transition_bdd.PrintMinterm()
            transition_bdds.append(transition_bdd)

        # encode final transition relation
        for transition_bdd in transition_bdds:
            self.transition_bdd_ &= transition_bdd

        self.create_error_states()

        synthe_1 = time.time()
        #         print("log: 1st stage time: " + str(round(synthe_1 - synthe_0,2)))

        # calculate winning region
        self.win_region_ = self.calc_winning_region()
        # print "win_region"
        # self.win_region_.PrintMinterm()

        if self.win_region_ != self.mgr_.Zero():
            # print("winning region:")
            # self.win_region_.PrintMinterm()
            non_det_strategy = self.get_nondet_strategy(self.win_region_)
            det_strategy = self.get_det_strategy(non_det_strategy)

            self.func_by_var_ = self.extract_output_funcs(det_strategy)

        else:
            print 'cannot find wining region for real algorithm!'
            return

        synthe_2 = time.time()

    #         print("log: 2nd stage time: " + str(round(synthe_2 - synthe_1,2)))


    def synthesize(self):

        #compute set joint input variables and output variables
        for dfa in self.dfa_list_:
            #add input vars
            for input_var in dfa.getInputVars():
                if input_var not in self.input_vars_:
                    self.input_vars_.append(input_var)
                    self.in_out_var_names_[input_var]= dfa.getVarName(input_var)

            #add output vars
            for output_var in dfa.getOutputVars():
                if output_var not in self.output_vars_:
                    self.output_vars_.append(output_var)
                    self.in_out_var_names_[output_var]= dfa.getVarName(output_var)


        #encode states and create init_state
        # (create state bdds for all state bits of all automata)
        state_order= self.encode_states_and_create_init_state()

        #encode variables
        var_order = self.encode_variables()

        #build next state vars
        self.next_state_vars_bdd_ = []
        for state_pos in range(0,self.num_of_bits_):
            self.next_state_vars_bdd_.append(self.var_bdds_['s'+str(self.num_of_bits_-1-state_pos)+'n'])

        #build input variables bdds
        self.in_var_bdds_ = []
        for var in self.input_vars_:
            self.in_var_bdds_.append(self.var_bdds_["v"+str(var-1)])

        #build output variables bdds
        self.out_var_bdd_ = []
        for var in self.output_vars_:
            self.out_var_bdd_.append(self.var_bdds_["v"+str(var-1)])

        #print "variable order to console"
        #print("variable order:"+state_order+var_order)

        #encode transition relation for each dfa
        transition_bdds = []
        for dfa in self.dfa_list_:
            transition_bdd = self.encode_transitions(dfa)
            # print dfa
            # transition_bdd.PrintMinterm()
            transition_bdds.append(transition_bdd)

        #encode final transition relation
        for transition_bdd in transition_bdds:
            self.transition_bdd_ &= transition_bdd
        #print "Final Transition_BDD:"
        #self.transition_bdd_.PrintMinterm()

        #create error states
        self.create_error_states()

        #calculate winning region
        self.win_region_ = self.calc_winning_region()
        #print "win_region"
        #self.win_region_.PrintMinterm()

        if self.win_region_ != self.mgr_.Zero():
            #print("winning region:")
            #self.win_region_.PrintMinterm()
            
            non_det_strategy = self.get_nondet_strategy(self.win_region_)
            #print ("non-det-strategy")
            #non_det_strategy.PrintMinterm()
            det_strategy = self.get_det_strategy(non_det_strategy)
            #comute next states functions bdd and output functions bdd
            self.func_by_var_ = self.extract_output_funcs(det_strategy)


    def getResultModel(self, out_format=NUSMV):

        #encode output function bdd
        for var_num in self.output_vars_:
            var_bdd = self.var_bdds_["v"+str(var_num-1)]
            var_lit = var_bdd.NodeReadIndex()
            var_name = "var->" + self.var_names_[var_lit]
            self.model_to_output_format(var_name, var_bdd, self.func_by_var_[var_bdd], out_format)

        #encode next state function bdd
        for state_pos in range(0,self.num_of_bits_):
            state_name = 's'+str(self.num_of_bits_-1-state_pos)+'n'
            state_bdd = self.var_bdds_[state_name]
            self.model_to_output_format(state_name, state_bdd, self.func_by_var_[state_bdd], out_format)

        return self.result_model_

    def getNumOfBits(self):
        return self.num_of_bits_

    def getTmpCount(self):
        return self.tmp_count_
    def getMaxTmpCount(self):
        return self.max_tmp_count

    def existsWinningRegion(self):
        if self.win_region_ != self.mgr_.Zero():
            return True
        else:
            return False


    def create_init_states(self, dfa_list):

        for dfa in dfa_list:
            init_state = dfa.getInitialNodes()[0]
            self.init_state_bdd_ &= self.make_node_state_bdd(init_state.getNr() - 1, dfa)

    def encode_states(self):
        num_of_bits_dict = dict()

        for dfa in self.dfa_list_:
            num_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))
            self.num_of_bits_ = self.num_of_bits_ + num_bits
            num_of_bits_dict[dfa] = num_bits

        self.state_offsets_[self.dfa_list_[0]] = 0
        offset = 0
        for i in range(1, len(self.dfa_list_)):
            offset = offset + num_of_bits_dict[self.dfa_list_[i - 1]]
            self.state_offsets_[self.dfa_list_[i]] = offset

        state_order = ""

        self.state_index = len(self.var_bdds_)
        # create var bdds
        for state_pos in range(0, self.num_of_bits_):
            node_bdd = self.mgr_.IthVar(len(self.var_bdds_))
            state_name = 's' + str(self.num_of_bits_ - 1 - state_pos)
            self.var_names_.append(state_name)
            self.var_bdds_[state_name] = node_bdd
            state_order += state_name + " "

        for state_pos in range(0, self.num_of_bits_):
            node_bdd = self.mgr_.IthVar(len(self.var_bdds_))
            state_name = 's' + str(self.num_of_bits_ - 1 - state_pos) + 'n'
            self.var_names_.append(state_name)
            self.var_bdds_[state_name] = node_bdd
            state_order += state_name + " "

        # print "Init_state_BDD"
        # self.init_state_bdd_.PrintMinterm()
        return state_order



    def encode_states_and_create_init_state(self):

        num_of_bits_dict = dict()

        for dfa in self.dfa_list_:
            num_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))
            self.num_of_bits_ = self.num_of_bits_ + num_bits
            num_of_bits_dict[dfa] = num_bits

        self.state_offsets_[self.dfa_list_[0]] = 0
        offset = 0
        for i in range(1, len(self.dfa_list_)):
            offset = offset + num_of_bits_dict[self.dfa_list_[i-1]]
            self.state_offsets_[self.dfa_list_[i]] = offset

        state_order = ""

        #create var bdds
        for state_pos in range(0, self.num_of_bits_):
            node_bdd = self.mgr_.IthVar(len(self.var_bdds_))
            state_name = 's'+str(self.num_of_bits_-1-state_pos)
            self.var_names_.append(state_name)
            self.var_bdds_[state_name] = node_bdd
            state_order += state_name + " "

        for state_pos in range(0, self.num_of_bits_):
            node_bdd = self.mgr_.IthVar(len(self.var_bdds_))
            state_name = 's'+str(self.num_of_bits_-1-state_pos)+'n'
            self.var_names_.append(state_name)
            self.var_bdds_[state_name] = node_bdd
            state_order += state_name + " "


        for dfa in self.dfa_list_:
            init_state = dfa.getInitialNodes()[0]
            self.init_state_bdd_ &= self.make_node_state_bdd(init_state.getNr() - 1, dfa)

        # #create initial state bdd
        # init_state_et = self.error_tracking_dfa_.getInitialNodes()[0]
        # self.init_state_bdd_ &= self.make_node_state_bdd(init_state_et.getNr()-1, self.error_tracking_dfa_)
        #
        # init_state_dev = self.deviation_dfa_.getInitialNodes()[0]
        # self.init_state_bdd_ &= self.make_node_state_bdd(init_state_dev.getNr()-1, self.deviation_dfa_)
        #
        # init_state_cor = self.correctness_dfa_.getInitialNodes()[0]
        # self.init_state_bdd_ &= self.make_node_state_bdd(init_state_cor.getNr()-1, self.correctness_dfa_)

        #print "Init_state_BDD"
        #self.init_state_bdd_.PrintMinterm()
        return state_order

    def encode_variables(self):
        var_order=""
        for var in self.in_out_var_names_:
            var_num = var-1
            var_name = self.in_out_var_names_[var]
            var_order += var_name+" "
            self.var_names_.append(var_name)
            node_bdd = self.mgr_.IthVar(len(self.var_bdds_))
            self.var_bdds_["v"+str(var_num)] = node_bdd
        return var_order

    def encode_transitions(self, dfa):

        transition_bdd = self.mgr_.Zero()

        edges = dfa.getEdges()
        for edge in edges:
            source = edge.getSourceNode().getNr()
            target = edge.getTargetNode().getNr()
            literals = edge.getLabel().getLiterals()

            #encode state and next_state for this edge
            source_state_bdd = self.make_node_state_bdd(source-1, dfa)
            target_state_bdd = self.make_node_state_next_bdd(target-1, dfa)
            edge_transition = source_state_bdd
            edge_transition &= target_state_bdd

            #encode literals for this edge
            for literal in literals:
                sign = literal > 0
                abs_literal = abs(literal)
                var_literal=self.var_bdds_["v"+str(abs_literal-1)]
                if sign:
                    edge_transition &= var_literal
                else:
                    edge_transition &= ~var_literal

            transition_bdd += edge_transition

        #print "Transition_BDD"
        #transition_bdd.PrintMinterm()
        return transition_bdd

    def create_error_states(self):

        # find final states according to given algorithm (K_STABILIZING_ALGORITHM or FINITE_ERROR_ALGORITHM)

        self.err_state_bdd_ = self.mgr_.Zero()

        relax_state_bdds = None
        if self.relax_dfa_:
            relax_state_bdds = self.mgr_.Zero()
            for state in self.relax_dfa_.getNodes():
                if not state.isFinal():
                    relax_state_bdd = self.make_node_state_bdd(state.getNr() - 1, self.relax_dfa_)
                    relax_state_bdds += relax_state_bdd
        else:
            relax_state_bdds = self.mgr_.One()

        #Rules for error states:
        #1. Correctness: A state is unsafe, if shieldError_ is true
        error_bdd_1 = self.mgr_.Zero()
        for state in self.correctness_dfa_.getNodes():
            if state.getShieldError():
                error_state_bdd = self.make_node_state_bdd(state.getNr()-1, self.correctness_dfa_)
                error_state_bdd &= relax_state_bdds
                error_bdd_1 += error_state_bdd

        #print "ERROR BDD 1. Correctness: A state is unsafe, if shieldError_ is true"
        #error_bdd_1.PrintMinterm()
        #print "=============="

        #2. No shield-deviation before system error:
        error_bdd_2 = self.mgr_.Zero()
        for dev_state in self.deviation_dfa_.getNodes():
            for et_state in self.error_tracking_dfa_.getNodes():
                if dev_state.getShieldDeviation()>0:
                    if et_state.getDesignError()==0:
                        err_state_bdd_1 = self.make_node_state_bdd(dev_state.getNr()-1, self.deviation_dfa_)
                        err_state_bdd_2 = self.make_node_state_bdd(et_state.getNr()-1, self.error_tracking_dfa_)
                        err_state_bdd = err_state_bdd_1 & err_state_bdd_2
                        err_state_bdd &= relax_state_bdds
                        error_bdd_2 += err_state_bdd

        #print "ERROR BDD 2. No shield-deviation without system error:"
        #error_bdd_2.PrintMinterm()
        #print "=============="

        self.err_state_bdd_ += error_bdd_1
        self.err_state_bdd_ += error_bdd_2

        if self.algorithm_ == FINITE_ERROR_ALGORITHM:
            #3. At most k shield-deviation in case of exactly "allowed_design_error_" system error
            error_bdd_3 = self.mgr_.Zero()
            for dev_state in self.deviation_dfa_.getNodes():
                for et_state in self.error_tracking_dfa_.getNodes():
                    if dev_state.getShieldDeviation() == self.num_shield_deviations_ + 1:
                        if et_state.getDesignError() <= self.allowed_design_error_:
                            err_state_bdd_1 = self.make_node_state_bdd(dev_state.getNr()-1, self.deviation_dfa_)
                            err_state_bdd_2 = self.make_node_state_bdd(et_state.getNr()-1, self.error_tracking_dfa_)
                            err_state_bdd = err_state_bdd_1
                            err_state_bdd &= err_state_bdd_2
                            error_bdd_3 += err_state_bdd

            #print "ERROR BDD 3. At most k shield-deviation in case of exactly allowed_design_error_ system error"
            #error_bdd_3.PrintMinterm()
            #print "=============="
            self.err_state_bdd_ += error_bdd_3

        if self.feasibility_dfa_:
            error_bdd_4 = self.mgr_.Zero()
            for fs_state in self.feasibility_dfa_.getNodes():
                if fs_state.isFinal():
                    state_bdd = self.make_node_state_bdd(fs_state.getNr() - 1, self.feasibility_dfa_)
                    state_bdd &= relax_state_bdds
                    error_bdd_4 += state_bdd
            self.err_state_bdd_ += error_bdd_4
        #print "Error_BDD:"
        #self.err_state_bdd_.PrintMinterm()

    def calc_winning_region(self):
        not_error_bdd = ~self.err_state_bdd_
        new_set_bdd = not_error_bdd
        while True:
            curr_set_bdd = new_set_bdd
            new_set_bdd = not_error_bdd & self.pre_sys_bdd(curr_set_bdd, self.transition_bdd_)

            # print "removed state:"
            # self.printStatesInBdd((~new_set_bdd) & curr_set_bdd)
            # print "========================"
            # print "safe state in region:"
            # self.printStatesInBdd(curr_set_bdd)
            # print "========================"

            if (new_set_bdd & self.init_state_bdd_) == self.mgr_.Zero():
                return self.mgr_.Zero()

            if new_set_bdd == curr_set_bdd:
                return new_set_bdd

    def printStatesInBdd(self, bdd):

        for node1 in self.error_tracking_dfa_.getNodes():
            nodebdd1 = self.make_node_state_bdd(node1.getNr() - 1, self.error_tracking_dfa_)
            for node2 in self.correctness_dfa_.getNodes():
                nodebdd2 = nodebdd1 & self.make_node_state_bdd(node2.getNr() - 1, self.correctness_dfa_)
                for node3 in self.deviation_dfa_.getNodes():
                    nodebdd3 = nodebdd2 & self.make_node_state_bdd(node3.getNr() - 1, self.deviation_dfa_)
                    for node4 in self.feasibility_dfa_.getNodes():
                        nodebdd4 = nodebdd3 & self.make_node_state_bdd(node4.getNr() - 1, self.feasibility_dfa_)
                        for node5 in self.relax_dfa_.getNodes():
                            nodebdd5 = nodebdd4 & self.make_node_state_bdd(node5.getNr() - 1, self.relax_dfa_)
                            if (nodebdd5 & bdd) != self.mgr_.Zero():
                                print node1.toString(False,False) + ' ' + node2.toString(False,False) + ' '\
                                      + node3.toString(False,False) + ' ' + node4.toString(False,False) + ' ' + node5.toString(False,False)




    def getWinStateNum(self, strategy):
        self.winStateNum = 0
        self.allStateNum = 0
        for dev_state in self.deviation_dfa_.getNodes():
            for et_state in self.error_tracking_dfa_.getNodes():
                for cor_state in self.correctness_dfa_.getNodes():
                    for fs_state in self.feasibility_dfa_.getNodes():
                        for relax_state in self.relax_dfa_.getNodes():

                            state_bdd_1 = self.make_node_state_bdd(dev_state.getNr()-1, self.deviation_dfa_)
                            state_bdd_2 = self.make_node_state_bdd(et_state.getNr()-1, self.error_tracking_dfa_)
                            state_bdd_3 = self.make_node_state_bdd(cor_state.getNr()-1, self.correctness_dfa_)
                            state_bdd_4 = self.make_node_state_bdd(fs_state.getNr() - 1, self.feasibility_dfa_)
                            state_bdd_5 = self.make_node_state_bdd(relax_state.getNr() - 1, self.relax_dfa_)

                            state_bdd = state_bdd_1 & state_bdd_2 & state_bdd_3 & state_bdd_4 & state_bdd_5
                            self.allStateNum += 1
                            if (state_bdd & strategy) != self.mgr_.Zero():
                                self.winStateNum += 1


    def suc_sys_bdd(self, src_states_bdd, transition_bdd):
        abstract_bdd = self.get_cube(self.out_var_bdd_ + self.in_var_bdds_ + self.get_all_state_bdds())

        suc_bdd = transition_bdd.AndAbstract(src_states_bdd, abstract_bdd)

        return self.prime_states(suc_bdd)


    def pre_sys_bdd(self, dst_states_bdd, transition_bdd):
        """ Calculate predecessor states of given states.

        :return: BDD representation of predecessor states

        :hints: if current states are not primed they should be primed before calculation (why?)
        :hints: calculation of ``o t(a,b,o)`` using cudd: ``t.ExistAbstract(get_cube(o))``
        :hints: calculation of ``i t(a,b,i)`` using cudd: ``t.UnivAbstract(get_cube(i))``
        """

        #: :type: DdNode
        transition_bdd = transition_bdd
        #: :type: DdNode
        primed_dst_states_bdd = self.prime_states(dst_states_bdd)

        #: :type: DdNode
        intersection = transition_bdd & primed_dst_states_bdd  # all predecessors (i.e., if sys and env cooperate)

        # cudd requires to create a cube first..
        if len(self.out_var_bdd_) != 0:
            out_vars_cube_bdd = self.get_cube(self.out_var_bdd_)
            exist_outs = intersection.ExistAbstract(out_vars_cube_bdd)
        else:
            exist_outs = intersection
        # print
        # print
        #
        # print('exist_outs: quantified vars')
        # print"0123456789"
        # out_vars_cube_bdd.PrintMinterm()
        # print('before quantifying')
        # intersection.PrintMinterm()
        # print('after quantifying')
        # exist_outs.PrintMinterm()

        next_state_vars_cube = self.prime_states(self.get_cube(self.get_all_state_bdds()))
        exist_next_state = exist_outs.ExistAbstract(next_state_vars_cube)

        # print('exists_next_states: quantified vars')
        # next_state_vars_cube.PrintMinterm()
        # print('before quantifying')
        # exist_outs.PrintMinterm()
        # print('after quantifying')
        # exist_next_state.PrintMinterm()

        uncontrollable_output_bdds = self.in_var_bdds_
        if len(self.in_var_bdds_) !=0:
            in_vars_cube_bdd = self.get_cube(uncontrollable_output_bdds)
            forall_inputs = exist_next_state.UnivAbstract(in_vars_cube_bdd)
        else:
            forall_inputs = exist_next_state

        # print('forall_exists')
        # forall_inputs.PrintMinterm()

        return forall_inputs



    def get_det_strategy(self,non_det_strategy):
        
        # 1. randomly determinize the output
        output_models = dict()
        all_outputs = list(self.out_var_bdd_)
        all_inputs = list(self.in_var_bdds_)
        all_in_out = all_outputs + all_inputs
        
        all_next_state_vars = list(self.next_state_vars_bdd_)
        all_next_states_and_outputs = all_outputs + all_next_state_vars
         
        
        next_vars_cube = self.prime_states(self.get_cube(self.get_all_state_bdds()))
        out_var_strategy = non_det_strategy.ExistAbstract(next_vars_cube)
 
        #----------- output functions--------------
 
        for c in self.out_var_bdd_:
 
            others = set(set(all_outputs).difference({c}))
 
            if others:
                others_cube = self.get_cube(others)
                #: :type: DdNode
                c_arena = out_var_strategy.ExistAbstract(others_cube)
            else:
                c_arena = out_var_strategy
 
            can_be_true = c_arena.Cofactor(c)  # states (x,i) in which c can be true
            can_be_false = c_arena.Cofactor(~c)
 
            must_be_true = (~can_be_false) & can_be_true
            must_be_false = (~can_be_true) & can_be_false
 
            care_set = (must_be_true | must_be_false)
             
            c_model = must_be_true.Restrict(care_set)
            out_var_strategy = out_var_strategy & self.make_bdd_eq(c, c_model)
            
            non_det_strategy = non_det_strategy & self.make_bdd_eq(c, c_model)
        
        det_strategy = non_det_strategy  #all output has been determinized
        
        det_transition = det_strategy.ExistAbstract(self.get_cube(all_in_out))
        # 2. eliminate unreachable states in strategy
        self.reachable_state_bdd =  self.mgr_.Zero()
        new_reachable_state_bdd = self.init_state_bdd_
        while self.reachable_state_bdd != new_reachable_state_bdd:
            self.reachable_state_bdd = new_reachable_state_bdd
            
            cur_edges = self.reachable_state_bdd & det_transition
            
            cur_edges = cur_edges.ExistAbstract(self.get_cube(self.get_all_state_bdds()))
            
            new_reachable_state_bdd = self.reachable_state_bdd | (self.unprime_states(cur_edges))
            
        det_strategy = det_strategy & self.reachable_state_bdd
        
        self.getWinStateNum(det_strategy)
        return det_strategy
        
  
  


    def get_nondet_strategy(self,win_region_bdd):
        """ Get non-deterministic strategy from the winning region.
        If the system outputs values that satisfy this non-deterministic strategy, then the system wins.
        I.e., a non-deterministic strategy describes for each state all possible plausible output values:

        :return: non deterministic strategy bdd
        :note: The strategy is still not-deterministic. Determinization step is done later.
        """

        #: :type: DdNode
        primed_win_region_bdd = self.prime_states(win_region_bdd)

        #print "primed_win_region_bdd"
        #primed_win_region_bdd.PrintMinterm()

        strategy = (primed_win_region_bdd & self.transition_bdd_) & win_region_bdd

        #print "intersection"
        #intersection.PrintMinterm()




        #print "nondet strategy"
        #print strategy.PrintMinterm()

        return strategy

    def extract_output_funcs(self, strategy):
        """
        Calculate BDDs for output functions given a non-deterministic winning strategy.
        Cofactor-based approach.

        :return: dictionary ``controllable_variable_bdd -> func_bdd``
        """
        next_vars_cube = self.prime_states(self.get_cube(self.get_all_state_bdds()))
        non_det_strategy = strategy.ExistAbstract(next_vars_cube)
        
        output_models = dict()
        all_outputs = list(self.out_var_bdd_)
        all_next_state_vars = list(self.next_state_vars_bdd_)
        all_next_states_and_outputs = all_outputs + all_next_state_vars

        #----------- output functions--------------

        for c in self.out_var_bdd_:

            others = set(set(all_outputs).difference({c}))

            if others:
                others_cube = self.get_cube(others)
                #: :type: DdNode
                c_arena = non_det_strategy.ExistAbstract(others_cube)
            else:
                c_arena = non_det_strategy

            can_be_true = c_arena.Cofactor(c)  # states (x,i) in which c can be true
            can_be_false = c_arena.Cofactor(~c)

            #print'can_be_true'
            #can_be_true.PrintMinterm()
            #print'can_be_false'
            #can_be_false.PrintMinterm()
            #print

            # We need to intersect with can_be_true to narrow the search.
            # Negation can cause including states from !W (with err=1)
            #: :type: DdNode
            must_be_true = (~can_be_false) & can_be_true
            must_be_false = (~can_be_true) & can_be_false

            #print "must_be_true"
            #must_be_true.PrintMinterm()
            #print "must_be_false"
            #must_be_false.PrintMinterm()
            #print

            care_set = (must_be_true | must_be_false)
            
            # begin compute reachable states:
            # reach = self.init_state_bdd_
            # old_reach = self.mgr_.Zero()
            # while reach != old_reach:
            #     old_reach = reach
            #     reach = reach | self.suc_sys_bdd(reach, non_det_strategy & self.transition_bdd_ )
            # care_set = care_set & reach
            # end compute reachable states

            #print'care set is'
            #care_set.PrintMinterm()

            # We use 'restrict' operation, but we could also do just:
            # c_model = must_be_true -> care_set
            # ..but this is (probably) less efficient, since we cannot set c=1 if it is not in care_set, but we could.
            #
            # Restrict on the other side applies optimizations to find smaller bdd.
            # It cannot be expressed using boolean logic operations since we would need to say:
            # must_be_true = ite(care_set, must_be_true, "don't care")
            # and "don't care" cannot be expressed in boolean logic.

            # Restrict operation:
            #   on care_set: must_be_true.restrict(care_set) <-> must_be_true
            c_model = must_be_true.Restrict(care_set)

            output_models[c] = c_model

            non_det_strategy = non_det_strategy & self.make_bdd_eq(c, c_model)

            #print "Strategy for output variable "
            #c.PrintMinterm()

            #print'on_set: Var is True'
            #c_model.PrintMinterm()
            #print'off_set: Var is False'
            #(~c_model).PrintMinterm()

        #----------- next state functions--------------

        non_det_strategy = non_det_strategy & self.transition_bdd_

        for c in self.next_state_vars_bdd_:
            others = set(set(all_next_states_and_outputs).difference({c}))
            if others:
                others_cube = self.get_cube(others)
                #: :type: DdNode
                c_arena = non_det_strategy.ExistAbstract(others_cube)
            else:
                c_arena = non_det_strategy

            can_be_true = c_arena.Cofactor(c)  # states (x,i) in which c can be true
            can_be_false = c_arena.Cofactor(~c)

            must_be_true = (~can_be_false) & can_be_true
            must_be_false = (~can_be_true) & can_be_false

            care_set = (must_be_true | must_be_false)

            c_model = must_be_true.Restrict(care_set)

            output_models[c] = c_model

            non_det_strategy = non_det_strategy & self.make_bdd_eq(c, c_model)

        return output_models


    def get_cube(self,variables):
        assert len(variables)

        cube = self.mgr_.One()
        for v in variables:
            cube &= v
        return cube


    def make_bdd_eq(self,value1, value2):
        return (value1 & value2) | (~value1 & ~value2)


    def get_all_state_bdds(self):
        states=[]
        for i in range(0,self.num_of_bits_):
            states.append(self.var_bdds_["s"+str(i)])
        return states

    def prime_states(self,unprimed_states):
        all_var_bdds=self.var_bdds_.values()
        num_bdds= len(all_var_bdds)

        #: :type: DdArray
        primed_var_array = pycudd.DdArray(num_bdds)
        curr_var_array = pycudd.DdArray(num_bdds)

        for l_bdd in all_var_bdds:
            #: :type: DdNode
            l_bdd = l_bdd
            curr_var_array.Push(l_bdd)
            lit = l_bdd.NodeReadIndex()

            #range of current state bits, is moved by len of state field
            if 0 <= lit < self.num_of_bits_:
                new_l_bdd = self.mgr_.IthVar(lit+self.num_of_bits_)
            else:
                new_l_bdd = l_bdd

            primed_var_array.Push(new_l_bdd)

        replaced_states_bdd = unprimed_states.SwapVariables(curr_var_array, primed_var_array, num_bdds)

        return replaced_states_bdd

    def unprime_states(self,primed_states):
        all_var_bdds=self.var_bdds_.values()
        num_bdds= len(all_var_bdds)

        #: :type: DdArray
        curr_var_array = pycudd.DdArray(num_bdds)
        unprimed_var_array = pycudd.DdArray(num_bdds)

        for l_bdd in all_var_bdds:
            #: :type: DdNode
            l_bdd = l_bdd
            curr_var_array.Push(l_bdd)
            lit = l_bdd.NodeReadIndex()

            #range of current state bits, is moved by len of state field
            if self.num_of_bits_ <= lit < self.num_of_bits_*2:
                new_l_bdd = self.mgr_.IthVar(lit-self.num_of_bits_)
            else:
                new_l_bdd = l_bdd

            unprimed_var_array.Push(new_l_bdd)

        replaced_states_bdd = primed_states.SwapVariables(curr_var_array, unprimed_var_array, num_bdds)

        return replaced_states_bdd




    def make_node_state_bdd(self, nodeNr, dfa):

        num_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))
        offset = self.state_offsets_[dfa]

        bin_node_nr = bin(int(nodeNr))[2:]
        bin_str = ""+bin_node_nr.zfill(num_bits)

        result = self.mgr_.One()
        j = 1
        for i in range(0,self.num_of_bits_):
            if i >= offset and i < offset + num_bits:
                sign = bin_str[len(bin_str)-j] #sign of s
                if int(sign)==1:
                    result &= self.var_bdds_["s"+str(i)] #bdd of s
                elif int(sign)==0:
                    result &= ~self.var_bdds_["s"+str(i)]
                j=j+1

        return result

    def make_node_state_next_bdd(self,nodeNr, dfa):

        num_bits = int(math.ceil(math.log(len(dfa.getNodes()), 2)))
        offset = self.state_offsets_[dfa]

        bin_node_nr = bin(int(nodeNr))[2:]
        bin_str = ""+bin_node_nr.zfill(num_bits)

        result = self.mgr_.One()
        j = 1
        for i in range(0,self.num_of_bits_):
            if i >= offset and i < offset + num_bits:
                sign = bin_str[len(bin_str)-j] #sign of s
                if int(sign)==1:
                    result &= self.var_bdds_["s"+str(i)+"n"] #bdd of s
                elif int(sign)==0:
                    result &= ~self.var_bdds_["s"+str(i)+"n"]
                j=j+1
        return result

    def walk(self, a_bdd, out_format):
        """
        Walk given BDD node (recursively).

        :returns: literal representing input BDD
        :warning: variables in cudd nodes may be complemented, check with: ``node.IsComplement()``
        """

        #: :type: DdNode
        a_bdd = a_bdd
        if a_bdd.IsConstant():
            if out_format == NUSMV:
                if a_bdd == self.mgr_.One():
                    return "TRUE"
                else:
                    return "FALSE"
            else:
                if a_bdd == self.mgr_.One():
                    return "1"
                else:
                    return "0"

        #check if bdd node was already visited
        if a_bdd in self.visited_:
            return self.visited_[a_bdd]

        node_name = "tmp" + str(self.tmp_count_)
        self.tmp_count_ = self.tmp_count_ + 1
        self.max_tmp_count = max(self.tmp_count_, self.max_tmp_count)

        self.visited_[a_bdd] = node_name
        self.bdd_node_counter_ = self.bdd_node_counter_ + 1

        # get an index of variable,
        a_lit = a_bdd.NodeReadIndex()

        #: :type: DdNode
        t_bdd = a_bdd.T()
        #: :type: DdNode
        e_bdd = a_bdd.E()

        t_lit = self.walk(t_bdd, out_format)
        e_lit = self.walk(e_bdd, out_format)

        a_name = self.var_names_[a_lit]

        if a_name in self.in_out_var_names_.values():
            a_name = "var->"+a_name

        if out_format == NUSMV:
            ite_lit = "((" + a_name + " & " + t_lit + ") | (!" + a_name + " & " + e_lit +"))"
            if a_bdd.IsComplement():
                ite_lit = "!" + ite_lit
            self.output_model_ += "  " + node_name + " := " + ite_lit + ";\n"
        elif out_format == VERILOG:
            ite_lit = a_name + " ? " + t_lit + " : " + e_lit
            if a_bdd.IsComplement():
                ite_lit = "~(" + ite_lit + ")"
            self.output_model_ += "  assign " + node_name + " = " + ite_lit + ";\n"
        else: #out_format == ANSIC:
            ite_lit = a_name + " ? " + t_lit + " : " + e_lit
            if a_bdd.IsComplement():
                ite_lit = "!(" + ite_lit + ")"
            self.output_model_ += "  " + node_name + " = " + ite_lit + ";\n"
        return node_name

    def model_to_output_format(self, c_name, c_bdd, func_bdd, out_format):
        """ encodes definition of output variable c
        """
        #: :type: DdNode

        c_bdd = c_bdd

        self.visited_ = dict()
        self.bdd_node_counter_ = 1
        self.output_model_ = ""

        top_level_var = self.walk(func_bdd, out_format)

        if out_format == NUSMV:
            self.output_model_ += "  " + c_name + "_1 := " + top_level_var + ";\n"
        elif out_format == ANSIC:
            self.tmp_count_ = 1
            self.output_model_ += "  " + c_name + " = " + top_level_var + ";\n"
        else:
            self.output_model_ += "  assign " + c_name + " = " + top_level_var + ";\n"

        self.result_model_ += self.output_model_ + "\n"










