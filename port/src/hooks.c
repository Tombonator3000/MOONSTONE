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
#include <stdio.h>

#define HOOK_SPACE 0x100000                /* hooks bare i chip-minnet (spillet ligger der) */
static uint8_t hook_bits[HOOK_SPACE / 16];
#define MAX_HOOKS 512
static struct {
    uint32_t addr; hook_fn fn; const char *name; uint32_t calls;
    uint64_t cyc_sum; uint32_t cyc_n, cyc_min, cyc_max;     /* --hook-cycles: originalen */
} table[MAX_HOOKS];
bool hooks_measure;                         /* --hook-cycles: kjor originalen og mal syklusene */
extern int m68ki_remaining_cycles;          /* Musashi */

/* aapne kall som males: returadresse, stakk og tid ved inngang */
static struct { uint32_t ret, sp; uint64_t t; int h; } open_calls[64];
static int n_open;
static int n_hooks;
bool hooks_disabled;
void (*hook_trace)(uint32_t pc);
uint8_t *hook_coverage;                     /* --coverage: en bit per partallsadresse i chip-minnet */

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

/* C-funksjonen bruker like mange sykluser som originalen */
void hook_cycles(int n)
{
    m68ki_remaining_cycles -= n;
}

void hooks_report(void)
{
    for (int i = 0; i < n_hooks; i++) {
        if (hooks_measure && table[i].cyc_n)
            printf("%06x %-24s kall %-7u sykluser snitt %.1f, min %u, maks %u\n", table[i].addr, table[i].name,
                   table[i].cyc_n, (double)table[i].cyc_sum / table[i].cyc_n, table[i].cyc_min, table[i].cyc_max);
        else if (!hooks_measure)
            printf("%06x %-24s kjort i C %u ganger\n", table[i].addr, table[i].name, table[i].calls);
    }
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
    if (pc - SLAVE_BASE < 0x800) game_slave_pc(pc);
    if (n_open) {
        uint32_t sp = m68k_get_reg(NULL, M68K_REG_SP);
        int k = n_open - 1;
        if (pc == open_calls[k].ret && sp == open_calls[k].sp + 4) {
            uint32_t c = (uint32_t)(amiga_now() - open_calls[k].t);
            int h = open_calls[k].h;
            table[h].cyc_sum += c;
            if (!table[h].cyc_n || c < table[h].cyc_min) table[h].cyc_min = c;
            if (c > table[h].cyc_max) table[h].cyc_max = c;
            table[h].cyc_n++;
            n_open--;
        }
    }
    if (hook_coverage && pc < CHIP_SIZE && whd_mog_loaded) hook_coverage[pc >> 4] |= (uint8_t)(1 << ((pc >> 1) & 7));
    if (hook_trace) hook_trace(pc);
    if (pc < HOOK_SPACE && (hook_bits[pc >> 4] & (1 << ((pc >> 1) & 7))) && whd_mog_loaded) {
        for (int i = 0; i < n_hooks; i++)
            if (table[i].addr == pc) {
                if (hooks_measure) {
                    if (n_open < 64) {
                        uint32_t sp = m68k_get_reg(NULL, M68K_REG_SP);
                        open_calls[n_open].ret = mem_read32(sp);
                        open_calls[n_open].sp = sp;
                        open_calls[n_open].t = amiga_now();
                        open_calls[n_open].h = i;
                        n_open++;
                    }
                    return;
                }
                if (hooks_disabled) return;
                if (table[i].fn()) table[i].calls++;
                return;
            }
    }
}
