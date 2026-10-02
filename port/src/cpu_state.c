/*
 * cpu_state.c - lagrer og laster tilstanden til 68000 (Musashi).
 *
 * Bare dataene i starten av m68ki_cpu tas med, fram til tabellpekerne og
 * callbackene. De er adresser i programmet som kjorer og skal ikke lastes
 * fra en fil.
 */
#include "amiga.h"
#include "m68kcpu.h"

void cpu_state(StateIO *s)
{
    state_io(s, &m68ki_cpu, offsetof(m68ki_cpu_core, cyc_instruction));
}
