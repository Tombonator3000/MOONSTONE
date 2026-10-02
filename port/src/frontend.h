/* frontend.h - vindu, taster, joystick, spillkontrollere og lyd ut (SDL2). */
#ifndef FRONTEND_H
#define FRONTEND_H

#include <stdbool.h>

typedef struct {
    int   scale;
    bool  fullscreen;
    float volume;
} FrontendOptions;

int  frontend_run(const FrontendOptions *o);
void frontend_message(const char *msg);    /* feilmelding i et vindu (eller i terminalen) */

#endif
