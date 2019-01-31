__author__ = 'meng wu'

from datatypes.predicates import Predicate

class AnsicEncoder(object):

    def __init__(self, specDFA):
        self.specDFA = specDFA
        self.shieldModel_ = ""
        self.numOfShieldBits_ = 0
        self.tmpCount_ = 0
        self.designModel_ = []
        self.designModelStr_ = ""
        self.inputNames_ = []
        self.outputNames_ = []
        self.assertions = []
        self.count = 0

        self.predicates = dict()
        self.predicates_out = dict()
        self.predicates_lits = set()
        self.predicates_lits_out = set()
        self.hist_len = 10

        for var in self.specDFA.getInputVars():
            self.inputNames_.append(self.specDFA.getVarName(var))
        for var in self.specDFA.getOutputVars():
            self.inputNames_.append(self.specDFA.getVarName(var))

        for var in self.specDFA.getOutputVars():
            var_name = self.specDFA.getVarName(var) + "__1"
            self.outputNames_.append(var_name)


        #prepaer predicates
        predicates = self.specDFA.getPredicates()
        for var_name in predicates:
            predicate_parser = Predicate()
            predicate_parser.tokenize(predicates[var_name])
            predicate_ast = predicate_parser.parse()
            self.predicates[var_name] = predicate_ast
            self.predicates_lits = self.predicates_lits.union(predicate_ast.getLits())
            if var_name + "__1" in self.outputNames_:
                self.predicates_out[var_name] = predicate_ast
                self.predicates_lits_out = self.predicates_lits_out.union(predicate_ast.getLits())

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


        shield_module = self.encodeShieldModel()
        return shield_module



    """
    Builds an Verilog Module from a given shield model
    """
    def encodeShieldModel(self):

        enc = ""
        enc += self.encode_header()
        enc += self.encode_boolVar()
        enc += self.encode_realVar()
        enc += self.encode_histVar()

        enc += self.encode_func_equal()
        enc += self.encode_func_still()
        enc += self.encode_func_real2bool()
        enc += self.encode_func_updateHis()
        enc += self.encode_func_lp()
        enc += self.encode_func_lr()


        enc += self.encode_model(self.numOfShieldBits_, self.tmpCount_)
        enc += self.encode_transit(self.numOfShieldBits_)
        enc += '  return 0; \n}\n\n'




        enc += self.encode_main_shield()
        return enc


    '''
    Returns header

    '''
    def encode_header(self):
        template = open("inputfiles/template.c")
        header = template.read()
        template.close()
        return header


    '''
    Returns the declaration of all input and output, temporary, and state variables

    '''
    def encode_boolVar(self):

        var_enc = "struct boolVar{\n"

        #declare input and output variables
        for var_name in self.inputNames_:
            var_enc += "  bool " + var_name + ";  //input\n"
        for var_name in self.outputNames_:
            var_enc += "  bool " + var_name + ";  //output\n"
        var_enc += "};\n\n"


        return var_enc

    def encode_realVar(self):
        var_enc = "struct realVar{\n"

        # declare input and output variables
        for var_name in self.inputNames_:
            if var_name not in self.specDFA.getPredicates():
                var_enc += "  bool " + var_name + ";  //bool input\n"
        for var_name in self.outputNames_:
            if var_name[:-3] not in self.specDFA.getPredicates():
                var_enc += "  bool " + var_name + ";  //bool output\n"

        for var_name in self.predicates_lits:
            var_enc += "  float " + var_name + ";  //real variables input\n"
        for var_name in self.predicates_lits_out:
            var_enc += "  float " + var_name + "__1;  //real variables output\n"

        var_enc += "};\n\n"

        return var_enc

    def encode_histVar(self):
        var_enc = "struct hist_t{\n"
        for var_name in self.predicates_lits_out:
            var_enc += "  float " + var_name + "__1[" + str(self.hist_len)+"];\n"
        var_enc += "};\n\n"
        return var_enc

    def encode_func_equal(self):
        func_enc = "bool equal(struct boolVar *var){\n  return  "

        placeholder = '('
        for var_name in self.outputNames_:
            func_enc += placeholder +"(var->"+var_name + " == var->"+var_name[:-3]+") && \n"
            placeholder = '          '

        func_enc = func_enc[:-5] + ");\n}\n\n"
        return func_enc

    def encode_func_still(self):
        func_enc = "void still(struct realVar *rvar){\n"

        for var_name in self.predicates_lits_out:
            func_enc += "  rvar->" + var_name + "__1 = rvar->" + var_name + ";\n"

        func_enc += "}\n\n"
        return func_enc

    def encode_func_real2bool(self):
        func_enc = "void real2bool(struct boolVar *bvar, struct realVar *rvar){\n"
        predicates = self.specDFA.getPredicates()

        # create local real var
        for var_name in self.predicates_lits:
            func_enc += "  float " + var_name + " = rvar->" + var_name + ";\n"

        # copy bool var
        for var_name in self.inputNames_:
            if var_name in predicates:
                func_enc += "  bvar->" + var_name + "= (" + predicates[var_name] + ");\n"
            else:
                func_enc += "  bvar->" + var_name + "= rvar->" + var_name + ";\n"


        func_enc += "}\n\n"
        return func_enc

    def encode_func_lr(self):
        func_enc = "void linearReg(struct realVar *rvar, struct hist_t *hist){\n"
        for var_name in self.predicates_lits_out:
            func_enc += "  rvar->" + var_name + "__1 = compute(hist->" + var_name + "__1, "\
                    + str(self.hist_len) + ");\n"

        func_enc += "}\n\n"
        return  func_enc

    def encode_func_updateHis(self):
        func_enc = "void updateHis(struct realVar *var, struct hist_t *hist){\n"
        for var_name in self.predicates_lits_out:
            func_enc += "  for(int i=0; i < " + str(self.hist_len-2) + "; i++) " \
                        "hist->" + var_name + "__1[i] = hist->" + var_name + "__1[i+1];\n"
            func_enc += "  hist->" + var_name + "__1[" + str(self.hist_len-1) + "] = var->" + var_name +";\n"

        func_enc += "}\n\n"
        return func_enc

    def encode_main_shield(self):


        main_enc ='''void realShield(struct realVar *var){
  static struct hist_t hist;
  struct boolVar bv;
  real2bool(&bv, var);

  shield(&bv);
  if(equal(&bv)){
    still(var);
  }
  else{
    linearReg(var, &hist);
    lp(&bv,var);
  }
  updateHis(var, &hist);
}
'''
        return main_enc

    def encode_model(self, num_of_bits, tmp_count):
        mod = 'int shield( struct boolVar *var){\n'

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

    def encode_func_lp(self):

        func_enc = "int lp(struct boolVar *bvar, struct realVar *rvar){\n"

        func_enc += self.solver_init()
        self.count = 0
        assertions = '  //assert predicates constrains\n'
        for var_name in self.predicates_out:
            assertion, ast = self.solver_assert(self.predicates[var_name])
            assertion += '  if(bvar->' + var_name+'__1) Z3_solver_assert(ctx, s,' + ast + ');\n'
            assertion += '  else Z3_solver_assert(ctx, s, Z3_mk_not(ctx,' + ast + '));\n\n'
            assertions += assertion

        assertions += '  Z3_solver_push(ctx, s);  //checkpoint for backtracking\n\n  //check linear reg result\n'

        for lit in self.predicates_lits_out:
            assertions += '  Z3_solver_assert(ctx, s, Z3_mk_eq(ctx,'+ lit + ', Z3_mk_real(ctx, (int)(rvar->' +lit + '__1*1000), 1000)));\n'

        func_enc += assertions
        func_enc += self.solver_check()
        func_enc += "}\n\n"
        return func_enc


    def solver_init(self):
        init = '  //initial z3 solver \n'
        init +=  '  Z3_context ctx;\n'
        init += '  Z3_solver s;\n'
        init += '  Z3_model m = 0;\n'
        init += '  Z3_ast args[2];\n'
        init += '  int64_t num, den;\n  Z3_ast v;\n'

        for lit in self.predicates_lits_out:
            init += '  Z3_ast ' + lit + ' = mk_real_var(ctx, "' + lit + '");\n'
        init += '  ctx = mk_context();\n'
        init += '  s = mk_solver(ctx);\n\n'
        return init

    def solver_cc(self): # check & clean solver
        check = '  check(ctx, s);\n'
        check += '  del_solver(ctx, s);\n'
        check += '  Z3_del_context(ctx);\n'
        check += '\n}\n'
        return check

    def solver_check(self):  # check feasibility
        check = '''
  if (Z3_solver_check(ctx, s) == Z3_L_TRUE){
    printf("sat with linear reg algo.\\n");
    del_solver(ctx, s);
    Z3_del_context(ctx);
    return 0;
  }
  else{
    Z3_solver_pop(ctx, s, 1); // remove linear reg constrains
    // try to solve lp directly
    if (Z3_solver_check(ctx, s) == Z3_L_TRUE){
      m = Z3_solver_get_model(ctx, s);
      //assign model to realVar
'''
        for lit in self.predicates_lits_out:
            check += '      if(Z3_model_eval(ctx, m, ' + lit +', 1, &v)){\n'
            check += '        Z3_get_numeral_rational_int64(ctx, v,&num, &den);\n'
            check += '        rvar->' + lit + ' = ((float)num)/((float)den);\n'
            check += '      }\n'
            check += '      else{\n'
            check += '        //fail to eval\n'
            check += '      }\n'

        check += '''
      //printf("sat\\n%s\\n", Z3_model_to_string(ctx, m));
      del_solver(ctx, s);
      Z3_del_context(ctx);
      return 1;
    }
    else{
      printf("Error: failed to get real value.\\n");
      return 2;
    }
  }\n'''
        return check

    def solver_assert(self, predicate):
        ast_name = ''

        if predicate.getType()==3:
            lassertion, last = self.solver_assert(predicate.getLeft())
            rassertion, rast = self.solver_assert(predicate.getRight())
            assertion = lassertion + rassertion
            ret = self.op2api(predicate.getValue(), last, rast)
            assertion += ret[0]
            ast_name = 'ast_' + str(self.count)
            assertion += '  Z3_ast ' + ast_name + ' = ' + ret[1]
            self.count += 1

        elif predicate.getType() == 0:# fix: mk_int_var
            assertion = ''
            ast_name = predicate.getValue()
        elif predicate.getType() == 1:
            ast_name = 'ast_' + str(self.count)
            assertion = '  Z3_ast ' + ast_name + ' = mk_int(ctx, ' + predicate.getValue() + ');\n'
            self.count += 1
        elif predicate.getType() == 2:
            ast_name = 'ast_' + str(self.count)
            assertion = '  Z3_ast ' + ast_name + ' = Z3_mk_numeral(ctx, "' + predicate.getValue() + '",Z3_mk_real_sort(ctx));\n'
            self.count += 1


        return assertion, ast_name


    def op2api(self, op, left, right):
        ret = ['', '']

        if op == '+':
            ret[0] = '  args[0] = ' + left + ';\n  args[1] = ' + right + ';\n'
            ret[1] = 'Z3_mk_add(ctx, 2, args);\n'
        elif op == '-':
            ret[0] = '  args[0] = ' + left + ';\n  args[1] = ' + right + ';\n'
            ret[1] = 'Z3_mk_sub(ctx, 2, args);\n'
        elif op == '*':
            ret[0] = '  args[0] = '+ left + ';\n  args[1] = ' + right + ';\n'
            ret[1] = 'Z3_mk_mul(ctx, 2, args);\n'
        elif op == '/':
            ret[1] = 'Z3_mk_div(ctx,' + left + ',' + right + ');\n'
        elif op == '&':
            ret[0] = '  args[0] = ' + left + ';\n  args[1] = ' + right + ';\n'
            ret[1] = 'Z3_mk_and(ctx, 2, args);\n'
        elif op == '|':
            ret[0] = '  args[0] = '+ left + ';\n  args[1] = ' + right + ';\n'
            ret[1] = 'Z3_mk_or(ctx, 2, args);\n'
        elif op == '%':
            ret[1] = 'Z3_mk_rem(ctx,' + left + ',' + right + ');\n'
        # elif op == 'mod':
        #     ret[1] = 'Z3_mk_mod(ctx,'+ left + ',' + right + ');\n'
        elif op == '^':
            ret[1] = 'Z3_mk_pow(ctx,'+ left + ',' + right + ');\n'
        elif op == '>':
            ret[1] = 'Z3_mk_gt(ctx,'+ left + ',' + right + ');\n'
        elif op == '>=':
            ret[1] = 'Z3_mk_ge(ctx,' + left + ',' + right + ');\n'
        elif op == '<':
            ret[1] = 'Z3_mk_lt(ctx,' + left + ',' + right + ');\n'
        elif op == '<=':
            ret[1] = 'Z3_mk_le(ctx,' + left + ',' + right + ');\n'
        else:
            raise SyntaxError('Invalid operator in predicates!')
        return ret




