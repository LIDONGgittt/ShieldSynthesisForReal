typedef struct lin_reg
{
    float a;
    float b;
} lin_reg;

// global solver variables
Z3_context gctx;
Z3_solver gsolver;


//--------------------------------------------------------
// FUNCTION PROTOTYPES
//--------------------------------------------------------
// linear regression functions
float arithmetic_mean(float* data, int size);
float mean_of_products(float* data1, float* data2, int size);
float variance(float* data, int size);
void linear_regression(float* dependent, int size, lin_reg* lr);
float compute (float* dependent, int size);

//z3 api function
Z3_solver mk_solver(Z3_context ctx);
void del_solver(Z3_context ctx, Z3_solver s);
Z3_context mk_context();
Z3_ast mk_var(Z3_context ctx, const char * name, Z3_sort ty);
Z3_ast mk_bool_var(Z3_context ctx, const char * name);
Z3_ast mk_int_var(Z3_context ctx, const char * name);
Z3_ast mk_int(Z3_context ctx, int v);
Z3_ast mk_real_var(Z3_context ctx, const char * name);


bool equal(struct boolVar *var);
void still(struct realVar *rvar);
void real2bool(struct boolVar *bvar, struct realVar *rvar);
void updateHis(struct realVar *var, struct hist_t *hist);
int lp(struct boolVar *bvar, struct realVar *rvar);
void linearReg(struct realVar *rvar, struct hist_t *hist);
int shield( struct boolVar *var);
void realShield(struct realVar *var);

void exitf(const char* message)
{
  fprintf(stderr,"BUG: %s.\n", message);
  exit(1);
}

/**
   \brief exit if unreachable code was reached.
*/
void unreachable()
{
    exitf("unreachable code was reached");
}

/**
   \brief Simpler error handler.
 */
void error_handler(Z3_context c, Z3_error_code e)
{
    printf("Error code: %d\n", e);
    exitf("incorrect use of Z3");
}

static jmp_buf g_catch_buffer;
/**
   \brief Low tech exceptions.

   In high-level programming languages, an error handler can throw an exception.
*/
void throw_z3_error(Z3_context c, Z3_error_code e)
{
    longjmp(g_catch_buffer, e);
}

/**
   \brief Error handling that depends on checking an error code on the context.

*/

void nothrow_z3_error(Z3_context c, Z3_error_code e) {
    // no-op
}
/**
   \brief Create a logical context.

   Enable model construction. Other configuration parameters can be passed in the cfg variable.

   Also enable tracing to stderr and register custom error handler.
*/
Z3_context mk_context_custom(Z3_config cfg, Z3_error_handler err)
{
    Z3_context ctx;

    Z3_set_param_value(cfg, "model", "true");
    ctx = Z3_mk_context(cfg);
    Z3_set_error_handler(ctx, err);

    return ctx;
}

Z3_solver mk_solver(Z3_context ctx)
{
  Z3_solver s = Z3_mk_solver(ctx);
  Z3_solver_inc_ref(ctx, s);
  return s;
}

void del_solver(Z3_context ctx, Z3_solver s)
{
  Z3_solver_dec_ref(ctx, s);
}

/**
   \brief Create a logical context.

   Enable model construction only.

   Also enable tracing to stderr and register standard error handler.
*/
Z3_context mk_context()
{
    Z3_config  cfg;
    Z3_context ctx;
    cfg = Z3_mk_config();
    ctx = mk_context_custom(cfg, error_handler);
    Z3_del_config(cfg);
    return ctx;
}

/**
   \brief Create a variable using the given name and type.
*/
Z3_ast mk_var(Z3_context ctx, const char * name, Z3_sort ty)
{
    Z3_symbol   s  = Z3_mk_string_symbol(ctx, name);
    return Z3_mk_const(ctx, s, ty);
}

/**
   \brief Create a boolean variable using the given name.
*/
Z3_ast mk_bool_var(Z3_context ctx, const char * name)
{
    Z3_sort ty = Z3_mk_bool_sort(ctx);
    return mk_var(ctx, name, ty);
}

/**
   \brief Create an integer variable using the given name.
*/
Z3_ast mk_int_var(Z3_context ctx, const char * name)
{
    Z3_sort ty = Z3_mk_int_sort(ctx);
    return mk_var(ctx, name, ty);
}

/**
   \brief Create a Z3 integer node using a C int.
*/
Z3_ast mk_int(Z3_context ctx, int v)
{
    Z3_sort ty = Z3_mk_int_sort(ctx);
    return Z3_mk_int(ctx, v, ty);
}

/**
   \brief Create a real variable using the given name.
*/
Z3_ast mk_real_var(Z3_context ctx, const char * name)
{
    Z3_sort ty = Z3_mk_real_sort(ctx);
    return mk_var(ctx, name, ty);
}

float compute (float* dependent, int size)
{
    lin_reg lr;
    linear_regression(dependent, size, &lr);
    return lr.a * (float)size + lr.b;
}

// --------------------------------------------------------
// FUNCTION linear_regression
// --------------------------------------------------------
void linear_regression(float* dependent, int size, lin_reg* lr)
{
    float* independent = (float*)malloc(size * sizeof(float));
    for(int i = 0; i < size; i++)
    {
        independent[i] = i;
    }
    float independent_mean = arithmetic_mean(independent, size);
    float dependent_mean = arithmetic_mean(dependent, size);
    float products_mean = mean_of_products(independent, dependent, size);
    float independent_variance = variance(independent, size);

    lr->a = (products_mean - (independent_mean * dependent_mean) ) / independent_variance;

    lr->b = dependent_mean - (lr->a * independent_mean);
}

//--------------------------------------------------------
// FUNCTION arithmetic_mean
//--------------------------------------------------------
float arithmetic_mean(float* data, int size)
{
    float total = 0;

    // note that incrementing total is done within the for loop
    for(int i = 0; i < size; total += data[i], i++);

    return total / size;
}

//--------------------------------------------------------
// FUNCTION mean_of_products
//--------------------------------------------------------

float mean_of_products(float* data1, float* data2, int size)
{
    float total = 0;

    // note that incrementing total is done within the for loop
    for(int i = 0; i < size; total += (data1[i] * data2[i]), i++);

    return total / size;
}

//--------------------------------------------------------
// FUNCTION variance
//--------------------------------------------------------
float variance(float* data, int size)
{
    float squares[size];

    for(int i = 0; i < size; i++)
    {
        squares[i] = pow(data[i], 2);
    }

    float mean_of_squares = arithmetic_mean(squares, size);
    float mean = arithmetic_mean(data, size);
    float square_of_mean = pow(mean, 2);
    float variance = mean_of_squares - square_of_mean;

    return variance;
}


void realShield(struct realVar *var){
  static struct hist_t hist;
  struct boolVar bv;
  real2bool(&bv, var);

  shield(&bv);

  if(equal(&bv)){
    //printf("shield not interfere!\n");
    still(var);
    var->result = 3;
  }
  else{
    linearReg(var, &hist);
    //printf("after linearReg func\n");
    var->result = lp(&bv,var);
  }
  updateHis(var, &hist);
}
