
#define rank_ 3

typedef struct lin_reg
{
    float a;
    float b;
} lin_reg;

//--------------------------------------------------------
// FUNCTION PROTOTYPES
//--------------------------------------------------------
// linear regression functions
float compute (float* data, int size);

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

// Jingbo: Assuming y = a0 + a1 * x + a2 * x^2 + a3 * x^3;
// Refer to the Gaussian Elimination https://en.wikipedia.org/wiki/Gaussian_elimination

float compute(float *y, int size)
{
    float x[size];
    for(int i = 0; i < size; i++)
    {
        x[i] = i;
    }
    float x_poly[2 * (rank_ + 1)] = {0}, b[rank_ + 1] = {0}, a[rank_ + 1][rank_ + 1];
    int i, j, k;

    for(i = 0; i < size; i++){  //
        x_poly[1] += x[i];
        x_poly[2] += pow(x[i], 2);
        x_poly[3] += pow(x[i], 3);
        x_poly[4] += pow(x[i], 4);
        x_poly[5] += pow(x[i], 5);
        x_poly[6] += pow(x[i], 6);
        b[0] += y[i];
        b[1] += x[i] * y[i];
        b[2] += pow(x[i], 2) * y[i];
        b[3] += pow(x[i], 3) * y[i];
    }

    x_poly[0] = size;

    for(i = 0; i < rank_ + 1; i++){  // build coefficient parameter matrix
        k = i;
        for(j = 0; j < rank_ + 1; j++)  a[i][j] = x_poly[k++];
    }

    // Gaussian elimination to calculate the result of a matrix
    for(k = 0; k < rank_ + 1 - 1; k++){  //n - 1 column
        int column = k;
        float mainelement = a[k][k];

        for(i = k; i < rank_ + 1; i++)  //
            if(fabs(a[i][k]) > mainelement){
                mainelement = fabs(a[i][k]);
                column = i;
            }
        for(j = k; j < rank_ + 1; j++){  // swap two rows
            float x_poly = a[k][j];
            a[k][j] = a[column][j];
            a[column][j] = x_poly;
        }
        float btemp = b[k];
        b[k] = b[column];
        b[column] = btemp;

        for(i = k + 1; i < rank_ + 1; i++){  // eleminating the unknown element
            float Mik = a[i][k] / a[k][k];
            for(j = k; j < rank_ + 1; j++)  a[i][j] -= Mik * a[k][j];
            b[i] -= Mik * b[k];
        }
    }

    b[rank_ + 1 - 1] /= a[rank_ + 1 - 1][rank_ + 1 - 1];  //
    for(i = rank_ + 1 - 2; i >= 0; i--){
        float sum = 0;
        for(j = i + 1; j < rank_ + 1; j++)  sum += a[i][j] * b[j];
        b[i] = (b[i] - sum) / a[i][i];
    }
    // printf("P(x) = %f%+fx%+fx^2%+fx^3\n\n", b[0], b[1], b[2], b[3]);

    float result = b[0] + b[1] * (float)size + b[2] * (float)(size ^ 2) + b[3] * (float)(size ^ 3);

    return result;
}


void realShield(struct realVar *var){
  static struct hist_t hist;
  struct boolVar bv;
  real2bool(&bv, var);

  shield(&bv);

  if(equal(&bv)){
    printf("shield not interfere!\n");
    still(var);
  }
  else{
    linearReg(var, &hist);
    printf("after linearReg func\n");
    lp(&bv,var);
  }
  updateHis(var, &hist);
}
