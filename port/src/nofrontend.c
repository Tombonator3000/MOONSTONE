/* nofrontend.c - brukes naar porten bygges uten SDL (bare --headless). */
#include "frontend.h"
#include <stdio.h>

int frontend_run(const FrontendOptions *o)
{
    (void)o;
    fprintf(stderr, "Bygget uten vindu. Bruk --headless.\n");
    return 1;
}

void frontend_message(const char *msg) { fprintf(stderr, "%s\n", msg); }
