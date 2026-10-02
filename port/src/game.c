/*
 * game.c - det vi vet om dataene til Moonstone i minnet.
 *
 * Adressene gjelder naar hovedspillet (mog) er lastet til $80000. Introen
 * (program) ligger paa de samme adressene med annet innhold, saa vi sjekker
 * forst at mog kjorer (navnet SIR BANNER paa $95EE6).
 *
 * Ridderne: fire strukturer paa $84 byte fra $8D5B4.
 *   +$0B byte  hvem som styrer: 1 = joystick i port 1, 2 = joystick i port 2, 4 = datamaskinen
 *   +$36 long  spillernummer 0-3, eller 4 for en ridder datamaskinen spiller
 *   +$6C long  peker til navnet (f.eks. "SIR_GODBER")
 * $8D9AC long  peker til ridderen som har turen (ogsaa naar datamaskinen spiller)
 * $8D9A0 ord   joystick i port 1 slik spillet leser den ($81F92), $8D9A2 port 2
 *
 * Paa kartet styres ridderen som har turen med joysticken i port 2. I kamp
 * mellom to riddere faar den andre ridderen port 1 (byte $0B = 1).
 */
#include "amiga.h"
#include <string.h>

#define KNIGHTS      0x8d5b4
#define KNIGHT_SIZE  0x84
#define CUR_KNIGHT   0x8d9ac
#define K_CTRL       0x0b
#define K_PLAYER     0x36
#define K_NAME       0x6c

bool game_mog_running(void)
{
    return memcmp(chip + 0x95ee6, "SIR BANNER", 10) == 0;
}

static uint32_t rd32(uint32_t a) { return (uint32_t)chip[a] << 24 | chip[a + 1] << 16 | chip[a + 2] << 8 | chip[a + 3]; }

static int knight_index(uint32_t p)
{
    if (p < KNIGHTS || p >= KNIGHTS + 4 * KNIGHT_SIZE) return -1;
    if ((p - KNIGHTS) % KNIGHT_SIZE) return -1;
    return (int)((p - KNIGHTS) / KNIGHT_SIZE);
}

/* Spillernummeret (0-3) som styrer porten akkurat naa, eller -1 hvis vi ikke vet
 * (menyer, intro) eller datamaskinen styrer. port: 0 = port 1, 1 = port 2. */
int game_port_player(int port)
{
    if (!game_mog_running()) return -1;
    if (port == 1) {
        int k = knight_index(rd32(CUR_KNIGHT));
        if (k < 0) return -1;
        uint32_t s = KNIGHTS + (uint32_t)k * KNIGHT_SIZE;
        uint32_t pl = rd32(s + K_PLAYER);
        if (pl > 3 || chip[s + K_CTRL] != 2) return -1;
        return (int)pl;
    }
    for (int k = 0; k < 4; k++) {
        uint32_t s = KNIGHTS + (uint32_t)k * KNIGHT_SIZE;
        uint32_t pl = rd32(s + K_PLAYER);
        if (chip[s + K_CTRL] == 1 && pl <= 3) return (int)pl;
    }
    return -1;
}

/* navnet til ridder k (0-3), eller "" */
const char *game_knight_name(int k)
{
    static char buf[24];
    buf[0] = 0;
    if (!game_mog_running() || k < 0 || k > 3) return buf;
    uint32_t p = rd32(KNIGHTS + (uint32_t)k * KNIGHT_SIZE + K_NAME);
    if (p < 0x80000 || p >= CHIP_SIZE - 24) return buf;
    int i = 0;
    for (; i < 23 && chip[p + i]; i++) buf[i] = chip[p + i] == '_' ? ' ' : (char)chip[p + i];
    buf[i] = 0;
    return buf;
}

/* spillernummeret til ridder k, 4 = datamaskinen, -1 = ukjent */
int game_knight_player(int k)
{
    if (!game_mog_running() || k < 0 || k > 3) return -1;
    return (int)rd32(KNIGHTS + (uint32_t)k * KNIGHT_SIZE + K_PLAYER);
}

/* ------------------------------------------------------------ tegneliste (HD-grafikk) */
/* Slaven laster figurfiler (CEL) med rutinen paa slave+$58E: A0 = filnavnet,
 * A1 = hvor filen legges i minnet. tegn_figur ($9DCEC) faar A0 = filen i minnet,
 * D0 = bildenummer, D1 = x og D2 = y. Med de to kan vi si hvilket bilde fra
 * hvilken fil som tegnes hvor, som er det en HD-pakke trenger (docs/hd-grafikk.md).
 * Dette bare observerer; spillet kjorer som for. */
#include "m68k.h"

#define MAX_CELS 96
typedef struct { uint32_t addr; char name[28]; } CelInfo;
static CelInfo cels[MAX_CELS];
static int     n_cels;
static char    background[28];
GameDraw game_draws[GAME_MAX_DRAWS];
int      game_n_draws;

static void read_str(uint32_t a, char *out, int n)
{
    int i = 0;
    for (; i < n - 1; i++) {
        uint8_t c = (uint8_t)mem_read8(a + (uint32_t)i);
        if (c < 32 || c > 126) break;
        out[i] = (char)c;
    }
    out[i] = 0;
}

void game_slave_pc(uint32_t pc)
{
    uint32_t off = pc - SLAVE_BASE;
    if (off == 0x58e) {
        uint32_t dest = m68k_get_reg(NULL, M68K_REG_A1);
        char name[28];
        read_str(m68k_get_reg(NULL, M68K_REG_A0), name, sizeof name);
        int i;
        for (i = 0; i < n_cels; i++) if (cels[i].addr == dest) break;
        if (i == n_cels) {
            if (n_cels == MAX_CELS) { memmove(cels, cels + 1, sizeof cels[0] * (MAX_CELS - 1)); n_cels--; i = n_cels; }
            n_cels++;
        }
        cels[i].addr = dest;
        memcpy(cels[i].name, name, sizeof cels[i].name);
    } else if (off == 0x5f2) {
        read_str(m68k_get_reg(NULL, M68K_REG_A0), background, sizeof background);
    }
}

static bool observe_draw(void)
{
    if (game_n_draws >= GAME_MAX_DRAWS) return false;
    uint32_t a0 = m68k_get_reg(NULL, M68K_REG_A0);
    GameDraw *d = &game_draws[game_n_draws++];
    d->cel = -1;
    for (int i = 0; i < n_cels; i++) if (cels[i].addr == a0) { d->cel = i; break; }
    d->frame = (int16_t)m68k_get_reg(NULL, M68K_REG_D0);
    d->x = (int16_t)m68k_get_reg(NULL, M68K_REG_D1);
    d->y = (int16_t)m68k_get_reg(NULL, M68K_REG_D2);
    d->target = rd32(0x9e87e);             /* figurbuffer: hvor figuren tegnes */
    /* Bredde og hoyde fra bildetabellen i filen (+10, 10 byte per bilde).
     * Byte +8 er 1 for et vanlig bilde. speil_figur ($9DB16) snur et bilde der
     * det ligger: radene snus innenfor bredden rundet opp til 16, og byte +8
     * blir (utfyllingen << 4) med bit 0 slettet. tegn_figur trekker den ovre
     * halvdelen fra x, saa et speilvendt bilde havner paa samme sted som det
     * vanlige. Et vanlig bilde med noe i ovre halvdel flyttes til venstre. */
    d->w = d->h = d->xoff = d->flip = 0;
    if (d->frame >= 0 && (uint16_t)d->frame < (uint16_t)mem_read16(a0)) {
        uint32_t e = a0 + 10 + (uint32_t)d->frame * 10;
        uint8_t fl = (uint8_t)mem_read8(e + 8);
        d->w = (int16_t)mem_read16(e + 4);
        d->h = (int16_t)mem_read16(e + 6);
        d->flip = !(fl & 1);
        d->xoff = d->flip ? 0 : (int16_t)(fl >> 4);
    }
    return false;                          /* originalen tegner som vanlig */
}

const char *game_cel_name(int i) { return i >= 0 && i < n_cels ? cels[i].name : ""; }
const char *game_background(void) { return background; }

void game_register_hooks(void)
{
    hooks_register(0x9dcec, observe_draw, "tegn_figur (observer)");
}

void game_state(StateIO *s)
{
    STATE_VAR(s, cels);
    STATE_VAR(s, n_cels);
    STATE_VAR(s, background);
}
