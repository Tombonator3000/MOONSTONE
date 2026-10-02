/*
 * state.c - lagring og lasting av hele maskinens tilstand.
 *
 * Hver del har en *_state(StateIO *)-funksjon som skriver eller leser alle
 * variablene sine i samme rekkefolge. Hodet sier hvilken versjon av porten og
 * hvilke spillfiler tilstanden er laget med. Ved lasting tas en kopi forst,
 * og gaar noe galt, legges kopien tilbake.
 *
 * Det samme brukes i nettspill: verten sender tilstanden til gjestene naar de
 * kobler seg til, og state_ram_hash() brukes til aa sjekke at alle er i takt.
 */
#include "amiga.h"
#include "unzip.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STATE_MAGIC   "MOONSTAT"
#define STATE_VERSION 1

void state_io(StateIO *s, void *p, size_t n)
{
    if (s->error) return;
    if (s->saving) {
        if (s->pos + n > s->cap) {
            size_t cap = s->cap ? s->cap * 2 : 1 << 22;
            while (cap < s->pos + n) cap *= 2;
            uint8_t *nb = realloc(s->buf, cap);
            if (!nb) { s->error = true; return; }
            s->buf = nb;
            s->cap = cap;
        }
        memcpy(s->buf + s->pos, p, n);
        s->pos += n;
        if (s->pos > s->size) s->size = s->pos;
    } else {
        if (s->pos + n > s->size) { s->error = true; return; }
        memcpy(p, s->buf + s->pos, n);
        s->pos += n;
    }
}

static uint32_t layout_id(void)
{
    return (uint32_t)(sizeof(Machine) * 7919u + sizeof(Custom) * 104729u + sizeof(Blitter) * 31u
                      + sizeof(AudChan) * 131u + sizeof(Cia) * 17u + sizeof(void *));
}

static void all_parts(StateIO *s)
{
    char magic[8];
    uint32_t ver = STATE_VERSION, lay = layout_id(), game = files_game_crc();
    memcpy(magic, STATE_MAGIC, 8);
    state_io(s, magic, 8);
    STATE_VAR(s, ver);
    STATE_VAR(s, lay);
    STATE_VAR(s, game);
    if (!s->saving) {
        if (memcmp(magic, STATE_MAGIC, 8) || ver != STATE_VERSION || lay != layout_id() || game != files_game_crc()) {
            s->error = true;
            return;
        }
    }
    amiga_state(s);
    paula_state(s);
    video_state(s);
    whd_state(s);
    {
        extern unsigned blit_w, blit_h;
        STATE_VAR(s, blit_w);
        STATE_VAR(s, blit_h);
    }
}

bool state_save_mem(uint8_t **buf, size_t *size)
{
    StateIO s = { .saving = true };
    all_parts(&s);
    if (s.error) { free(s.buf); return false; }
    *buf = s.buf;
    *size = s.size;
    return true;
}

bool state_load_mem(const uint8_t *buf, size_t size)
{
    uint8_t *backup;
    size_t bsize;
    if (!state_save_mem(&backup, &bsize)) return false;
    StateIO s = { .saving = false, .buf = (uint8_t *)buf, .size = size };
    all_parts(&s);
    if (s.error) {
        StateIO r = { .saving = false, .buf = backup, .size = bsize };
        all_parts(&r);
        free(backup);
        return false;
    }
    free(backup);
    return true;
}

bool state_save_file(const char *path)
{
    uint8_t *buf;
    size_t size;
    if (!state_save_mem(&buf, &size)) return false;
    FILE *f = fopen(path, "wb");
    bool ok = f && fwrite(buf, 1, size, f) == size;
    if (f) fclose(f);
    free(buf);
    return ok;
}

bool state_load_file(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) return false;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *buf = n > 0 ? malloc((size_t)n) : NULL;
    bool ok = buf && fread(buf, 1, (size_t)n, f) == (size_t)n;
    fclose(f);
    if (ok) ok = state_load_mem(buf, (size_t)n);
    free(buf);
    return ok;
}

uint32_t state_ram_hash(void)
{
    uint32_t h = crc32_calc(chip, CHIP_SIZE);
    h ^= crc32_calc(fast, 0x80000) * 3u;
    h ^= crc32_calc((const uint8_t *)&C, sizeof C) * 5u;
    return h;
}
