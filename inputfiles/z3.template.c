
/*++
Copyright (c) 2015 Microsoft Corporation

--*/

#include<stdio.h>
#include<stdlib.h>
#include<stdarg.h>
#include<memory.h>
#include<setjmp.h>
#include<z3.h>


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

/**
   \brief Create the unary function application: <tt>(f x)</tt>.
*/
Z3_ast mk_unary_app(Z3_context ctx, Z3_func_decl f, Z3_ast x)
{
    Z3_ast args[1] = {x};
    return Z3_mk_app(ctx, f, 1, args);
}

/**
   \brief Create the binary function application: <tt>(f x y)</tt>.
*/
Z3_ast mk_binary_app(Z3_context ctx, Z3_func_decl f, Z3_ast x, Z3_ast y)
{
    Z3_ast args[2] = {x, y};
    return Z3_mk_app(ctx, f, 2, args);
}

/**
   \brief Check whether the logical context is satisfiable, and compare the result with the expected result.
   If the context is satisfiable, then display the model.
*/
void check(Z3_context ctx, Z3_solver s, Z3_lbool expected_result)
{
    Z3_model m      = 0;
    Z3_lbool result = Z3_solver_check(ctx, s);
    switch (result) {
    case Z3_L_FALSE:
        printf("unsat\n");
        break;
    case Z3_L_UNDEF:
        printf("unknown\n");
	m = Z3_solver_get_model(ctx, s);
	if (m) Z3_model_inc_ref(ctx, m);
        printf("potential model:\n%s\n", Z3_model_to_string(ctx, m));
        break;
    case Z3_L_TRUE:
	m = Z3_solver_get_model(ctx, s);
	if (m) Z3_model_inc_ref(ctx, m);
        printf("sat\n%s\n", Z3_model_to_string(ctx, m));
        break;
    }
    if (result != expected_result) {
        exitf("unexpected result");
    }
    if (m) Z3_model_dec_ref(ctx, m);
}


/**
   \brief Display Z3 version in the standard output.
*/
void display_version()
{
    unsigned major, minor, build, revision;
    Z3_get_version(&major, &minor, &build, &revision);
    printf("Z3 %d.%d.%d.%d\n", major, minor, build, revision);
}
/*@}*/

/**
   @name Examples
*/
/*@{*/
/**
   \brief "Hello world" example: create a Z3 logical context, and delete it.
*/
void simple_example()
{
    Z3_context ctx;
    printf("\nsimple_example\n");

    ctx = mk_context();

    /* delete logical context */
    Z3_del_context(ctx);
}

/**
   \brief Find a model for <tt>x xor y</tt>.
*/
void find_model_example1()
{
    Z3_context ctx;
    Z3_ast x, y, x_xor_y;
    Z3_solver s;

    printf("\nfind_model_example1\n");

    ctx     = mk_context();
    s       = mk_solver(ctx);

    x       = mk_bool_var(ctx, "x");
    y       = mk_bool_var(ctx, "y");
    x_xor_y = Z3_mk_xor(ctx, x, y);

    Z3_solver_assert(ctx, s, x_xor_y);

    printf("model for: x xor y\n");
    check(ctx, s, Z3_L_TRUE);

    del_solver(ctx, s);
    Z3_del_context(ctx);
}

/**
   \brief Find a model for <tt>x < y + 1, x > 2</tt>.
   Then, assert <tt>not(x = y)</tt>, and find another model.
*/
void find_model_example2()
{
    Z3_context ctx;
    Z3_ast x, y, one, two, y_plus_one;
    Z3_ast x_eq_y;
    Z3_ast args[2];
    Z3_ast c1, c2, c3;
    Z3_solver s;

    printf("\nfind_model_example2\n");

    ctx        = mk_context();
    s          = mk_solver(ctx);
    x          = mk_int_var(ctx, "x");
    y          = mk_int_var(ctx, "y");
    one        = mk_int(ctx, 1);
    two        = mk_int(ctx, 2);

    args[0]    = y;
    args[1]    = one;
    y_plus_one = Z3_mk_add(ctx, 2, args);

    c1         = Z3_mk_lt(ctx, x, y_plus_one);
    c2         = Z3_mk_gt(ctx, x, two);

    Z3_solver_assert(ctx, s, c1);
    Z3_solver_assert(ctx, s, c2);

    printf("model for: x < y + 1, x > 2\n");
    check(ctx, s, Z3_L_TRUE);

    /* assert not(x = y) */
    x_eq_y     = Z3_mk_eq(ctx, x, y);
    c3         = Z3_mk_not(ctx, x_eq_y);
    Z3_solver_assert(ctx, s,c3);

    printf("model for: x < y + 1, x > 2, not(x = y)\n");
    check(ctx, s, Z3_L_TRUE);

    del_solver(ctx, s);
    Z3_del_context(ctx);
}


int main() {
    display_version();

    find_model_example1();
    find_model_example2();
    return 0;
}
