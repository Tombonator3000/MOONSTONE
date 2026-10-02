/*
 * hooks.c - kalles foer hver 68000-instruksjon.
 *
 * Her fanges kall til resload-tabellen (whdload.c), og her kan funksjoner i
 * spillet byttes ut med C, en og en (decomp). En C-funksjon registreres med
 * hooks_register(adresse, funksjon, navn). Naar CPU-en kommer til adressen,
 * kjores C-funksjonen. Returnerer den true, har den gjort jobben og kalt
 * hook_return() (som RTS). Returnerer den false, kjores originalkoden.
 */
#include "amiga.h"
#include "m68k.h"
#include <string.h>

#define HOOK_SPACE 0x100000                /* hooks bare i chip-minnet (spillet ligger der) */
static uint8_t hook_bits[HOOK_SPACE / 16];
#define MAX_HOOKS 512
static struct { uint32_t addr; hook_fn fn; const char *name; uint32_t calls; } table[MAX_HOOKS];
static int n_hooks;
bool hooks_disabled;
void (*hook_trace)(uint32_t pc);

void hooks_clear(void)
{
    memset(hook_bits, 0, sizeof hook_bits);
    n_hooks = 0;
}

void hooks_register(uint32_t addr, hook_fn fn, const char *name)
{
    if (addr >= HOOK_SPACE || (addr & 1) || n_hooks >= MAX_HOOKS) return;
    table[n_hooks].addr = addr;
    table[n_hooks].fn = fn;
    table[n_hooks].name = name;
    table[n_hooks].calls = 0;
    n_hooks++;
    hook_bits[addr >> 4] |= (uint8_t)(1 << ((addr >> 1) & 7));
}

void hook_return(void)
{
    uint32_t sp = m68k_get_reg(NULL, M68K_REG_SP);
    m68k_set_reg(M68K_REG_PC, mem_read32(sp));
    m68k_set_reg(M68K_REG_SP, sp + 4);
}

void ami_instr_hook(unsigned pc)
{
    if (pc - RESLOAD_BASE < 0x100) {
        whd_call(pc - RESLOAD_BASE);
        return;
    }
    if (hook_trace) hook_trace(pc);
    if (pc < HOOK_SPACE && (hook_bits[pc >> 4] & (1 << ((pc >> 1) & 7))) && !hooks_disabled) {
        for (int i = 0; i < n_hooks; i++)
            if (table[i].addr == pc) {
                if (table[i].fn()) table[i].calls++;
                return;
            }
    }
}
