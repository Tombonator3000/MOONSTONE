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
