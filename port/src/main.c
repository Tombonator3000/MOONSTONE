/*
 * main.c - oppstart, valg paa kommandolinjen og kjoring uten vindu (testing).
 *
 *   moonstone                         start med vindu (frontend.c)
 *   moonstone --game sti              spillfilene: zip, ISO eller mappe
 *   moonstone --headless --frames N   kjor uten vindu, f.eks. med --shot-every
 *
 * Se --help for alle valgene.
 */
#include "amiga.h"
#include "frontend.h"
#include "m68k.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

bool png_write(const char *path, const uint32_t *rgba, int w, int h, int stride);
void decomp_register_all(void);

typedef struct { int frame, len; char what[32]; } Press;
typedef struct { int frame; char path[256]; } Dump;
static Dump dumps[64];
static int  n_dumps;
static Press presses[256];
static int   n_presses;

static const struct { const char *name; int code; } keynames[] = {
    {"esc",0x45},{"space",0x40},{"return",0x44},{"enter",0x43},{"tab",0x42},{"backspace",0x41},{"del",0x46},
    {"f1",0x50},{"f2",0x51},{"f3",0x52},{"f4",0x53},{"f5",0x54},{"f6",0x55},{"f7",0x56},{"f8",0x57},{"f9",0x58},{"f10",0x59},
    {"cup",0x4c},{"cdown",0x4d},{"cright",0x4e},{"cleft",0x4f},{"help",0x5f},{"lshift",0x60},{"rshift",0x61},
    {"ctrl",0x63},{"lalt",0x64},{"ralt",0x65},{"lamiga",0x66},{"ramiga",0x67},
};

int amiga_keycode(const char *name)
{
    for (size_t i = 0; i < sizeof keynames / sizeof keynames[0]; i++)
        if (!strcmp(keynames[i].name, name)) return keynames[i].code;
    if (strlen(name) == 1) {
        char c = (char)tolower((unsigned char)name[0]);
        const char *row1 = "1234567890", *rowq = "qwertyuiop", *rowa = "asdfghjkl", *rowz = "zxcvbnm";
        const char *p;
        if ((p = strchr(row1, c))) return 0x01 + (int)(p - row1);
        if ((p = strchr(rowq, c))) return 0x10 + (int)(p - rowq);
        if ((p = strchr(rowa, c))) return 0x20 + (int)(p - rowa);
        if ((p = strchr(rowz, c))) return 0x31 + (int)(p - rowz);
    }
    return -1;
}

/* "fire", "up", ... er joystick i port 2 (spiller 1). "p2-fire" osv. er port 1. */
static int joy_bit(const char *w, int *port)
{
    *port = 1;
    if (!strncmp(w, "p2-", 3)) { *port = 0; w += 3; }
    if (!strcmp(w, "up")) return JOY_UP;
    if (!strcmp(w, "down")) return JOY_DOWN;
    if (!strcmp(w, "left")) return JOY_LEFT;
    if (!strcmp(w, "right")) return JOY_RIGHT;
    if (!strcmp(w, "fire")) return JOY_FIRE;
    if (!strcmp(w, "fire2")) return JOY_FIRE2;
    return 0;
}

static void apply_presses(uint32_t frame)
{
    uint8_t joy[2] = { 0, 0 };
    for (int i = 0; i < n_presses; i++) {
        Press *p = &presses[i];
        int port, bit = joy_bit(p->what, &port);
        if (bit) {
            if (frame >= (uint32_t)p->frame && frame < (uint32_t)(p->frame + p->len)) joy[port] |= (uint8_t)bit;
        } else {
            int code = amiga_keycode(p->what);
            if (code < 0) continue;
            if (frame == (uint32_t)p->frame) amiga_key(code, true);
            if (frame == (uint32_t)(p->frame + p->len)) amiga_key(code, false);
        }
    }
    IN.joy[0] = joy[0];
    IN.joy[1] = joy[1];
}

static void usage(void)
{
    printf("Moonstone for PC, bygget paa originalkoden fra Amiga.\n\n"
           "  --game STI            spillfilene (Moonstonecd32-AMIGA.zip, ISO eller mappe)\n"
           "  --scale N             vindusstorrelse (standard 3)\n"
           "  --fullscreen          fullskjerm\n"
           "  --volume V            lydstyrke, 1.0 er normal\n"
           "  --buttonwait          vent paa fire for kamp (WHDLoad ButtonWait)\n"
           "  --nohooks             kjor bare originalkoden (ingen C-erstatninger)\n"
           "  --headless            uten vindu og lyd, for testing\n"
           "  --frames N            antall bilder (headless)\n"
           "  --shot-every N        lagre skjermbilde hvert N. bilde (PNG)\n"
           "  --shot-dir MAPPE      hvor skjermbildene lagres\n"
           "  --press F:HVA[:LENGDE] trykk knapp/tast i bilde F (fire, up, p2-fire, esc, f1, a ...)\n"
           "  --save-state F:FIL    lagre tilstand i bilde F\n"
           "  --load-state FIL      start fra en lagret tilstand\n"
           "  --dump F:FIL          skriv chip-minnet til fil i bilde F\n"
           "  --vis-tur             skriv hvilken spiller som styrer portene (nettspill)\n"
           "  --wav FIL             ta opp lyden\n"
           "  --log N               0 stille, 1 normal, 2 alt\n");
}

static const char *find_game(void)
{
    static const char *cands[] = {
        "spill", "../spill", "../../spill",
        "Moonstonecd32-AMIGA.zip", "../Moonstonecd32-AMIGA.zip", "../../Moonstonecd32-AMIGA.zip",
        "Moonstone CD32.iso", "../Moonstone CD32.iso", NULL
    };
    for (int i = 0; cands[i]; i++) {
        FILE *f = fopen(cands[i], "rb");
        if (f) { fclose(f); return cands[i]; }
    }
    return NULL;
}

int main(int argc, char **argv)
{
    const char *game = NULL, *shot_dir = ".", *load_state = NULL, *save_state_file = NULL, *wav_path = NULL;
    bool headless = false, nohooks = false, show_turn = false;
    int frames = 0, shot_every = 0, save_state_frame = -1;
    FrontendOptions fo = { .scale = 3, .volume = 1.0f };

    for (int i = 1; i < argc; i++) {
        const char *a = argv[i];
        const char *v = i + 1 < argc ? argv[i + 1] : NULL;
        if (!strcmp(a, "--help") || !strcmp(a, "-h")) { usage(); return 0; }
        else if (!strcmp(a, "--game") && v) { game = v; i++; }
        else if (!strcmp(a, "--headless")) headless = true;
        else if (!strcmp(a, "--frames") && v) { frames = atoi(v); i++; }
        else if (!strcmp(a, "--shot-every") && v) { shot_every = atoi(v); i++; }
        else if (!strcmp(a, "--shot-dir") && v) { shot_dir = v; i++; }
        else if (!strcmp(a, "--scale") && v) { fo.scale = atoi(v); i++; }
        else if (!strcmp(a, "--fullscreen")) fo.fullscreen = true;
        else if (!strcmp(a, "--volume") && v) { fo.volume = (float)atof(v); i++; }
        else if (!strcmp(a, "--buttonwait")) whd_buttonwait = 1;
        else if (!strcmp(a, "--nohooks")) nohooks = true;
        else if (!strcmp(a, "--log") && v) { log_level = atoi(v); i++; }
        else if (!strcmp(a, "--wav") && v) { wav_path = v; i++; }
        else if (!strcmp(a, "--vis-tur")) show_turn = true;
        else if (!strcmp(a, "--dump") && v) {
            if (n_dumps < 64) {
                dumps[n_dumps].frame = atoi(v);
                const char *c = strchr(v, ':');
                snprintf(dumps[n_dumps].path, sizeof dumps[0].path, "%s", c ? c + 1 : "ram.bin");
                n_dumps++;
            }
            i++;
        }
        else if (!strcmp(a, "--load-state") && v) { load_state = v; i++; }
        else if (!strcmp(a, "--save-state") && v) {
            save_state_frame = atoi(v);
            const char *c = strchr(v, ':');
            save_state_file = c ? c + 1 : "moonstone.sav";
            i++;
        } else if (!strcmp(a, "--press") && v) {
            if (n_presses < 256) {
                Press *p = &presses[n_presses++];
                p->len = 5;
                char tmp[64];
                snprintf(tmp, sizeof tmp, "%s", v);
                char *c1 = strchr(tmp, ':');
                if (c1) {
                    *c1 = 0;
                    p->frame = atoi(tmp);
                    char *c2 = strchr(c1 + 1, ':');
                    if (c2) { *c2 = 0; p->len = atoi(c2 + 1); }
                    snprintf(p->what, sizeof p->what, "%s", c1 + 1);
                }
            }
            i++;
        } else {
            fprintf(stderr, "Ukjent valg: %s (se --help)\n", a);
            return 1;
        }
    }

    if (!game) game = find_game();
    if (!game) {
        fprintf(stderr, "Fant ikke spillfilene. Legg Moonstonecd32-AMIGA.zip i mappen spill/ eller bruk --game.\n");
        if (!headless) frontend_message("Fant ikke spillfilene.\n\nLegg Moonstonecd32-AMIGA.zip i mappen \"spill\" ved siden av programmet.");
        return 1;
    }
    if (!files_open(game)) {
        fprintf(stderr, "%s: %s\n", game, files_error);
        if (!headless) frontend_message(files_error);
        return 1;
    }
    hooks_disabled = nohooks;
    if (!nohooks) decomp_register_all();
    if (!amiga_init()) {
        fprintf(stderr, "Oppstart feilet: %s\n", files_error);
        return 1;
    }
    if (load_state && !state_load_file(load_state)) {
        fprintf(stderr, "Kunne ikke laste tilstanden %s\n", load_state);
        return 1;
    }

    if (!headless) return frontend_run(&fo);

    FILE *wav = wav_path ? fopen(wav_path, "wb") : NULL;
    uint32_t wav_frames = 0;
    if (wav) { uint8_t hdr[44] = {0}; fwrite(hdr, 1, 44, wav); }
    for (int f = 0; f < frames; f++) {
        apply_presses(M.frame);
        amiga_run_frame();
        int16_t tmp[4096];
        int n;
        while ((n = paula_take(tmp, 2048)) > 0) {
            if (wav) { fwrite(tmp, 4, (size_t)n, wav); wav_frames += (uint32_t)n; }
        }
        if (shot_every && (f + 1) % shot_every == 0) {
            char path[512];
            snprintf(path, sizeof path, "%s/shot_%05d.png", shot_dir, f + 1);
            png_write(path, video_fb, FB_W, FB_H, FB_W);
        }
        if (show_turn) {
            static int last = -99;
            int p2 = game_port_player(1), p1 = game_port_player(0);
            if (p2 * 10 + p1 != last) {
                last = p2 * 10 + p1;
                printf("bilde %u: port 2 = spiller %d, port 1 = spiller %d\n", M.frame, p2, p1);
            }
        }
        for (int d = 0; d < n_dumps; d++)
            if (dumps[d].frame == (int)M.frame) {
                FILE *df = fopen(dumps[d].path, "wb");
                if (df) { fwrite(chip, 1, CHIP_SIZE, df); fclose(df); }
            }
        if (save_state_frame == f + 1) {
            if (state_save_file(save_state_file)) printf("Tilstand lagret i %s\n", save_state_file);
        }
        if (M.aborted) {
            printf("Stoppet i bilde %d: %s\n", f + 1, M.abort_msg);
            break;
        }
    }
    if (wav) {
        uint32_t data = wav_frames * 4;
        uint8_t h[44];
        memcpy(h, "RIFF", 4); uint32_t v = 36 + data; memcpy(h + 4, &v, 4);
        memcpy(h + 8, "WAVEfmt ", 8); v = 16; memcpy(h + 16, &v, 4);
        uint16_t w = 1; memcpy(h + 20, &w, 2); w = 2; memcpy(h + 22, &w, 2);
        v = AUDIO_RATE; memcpy(h + 24, &v, 4); v = AUDIO_RATE * 4; memcpy(h + 28, &v, 4);
        w = 4; memcpy(h + 32, &w, 2); w = 16; memcpy(h + 34, &w, 2);
        memcpy(h + 36, "data", 4); memcpy(h + 40, &data, 4);
        fseek(wav, 0, SEEK_SET); fwrite(h, 1, 44, wav); fclose(wav);
    }
    printf("Ferdig etter %u bilder, PC=%06x SR=%04x\n", M.frame, m68k_get_reg(NULL, M68K_REG_PC), m68k_get_reg(NULL, M68K_REG_SR));
    if (log_level >= 2) {
        printf("INTENA=%04x INTREQ=%04x DMACON=%04x COP1LC=%06x BPLCON0=%04x DIW=%04x/%04x DDF=%04x/%04x\n",
               C.intena, C.intreq, C.dmacon, C.cop1lc, C.bplcon0, C.diwstrt, C.diwstop, C.ddfstrt, C.ddfstop);
        printf("vektorer:");
        for (int v = 0x64; v <= 0x7c; v += 4) printf(" %02x=%06x", v, mem_read32(v));
        printf("\nCIA-A: icr=%02x mask=%02x cra=%02x crb=%02x ta=%04x/%04x  CIA-B: icr=%02x mask=%02x cra=%02x crb=%02x ta=%04x/%04x\n",
               CIAA.icr, CIAA.imask, CIAA.cra, CIAA.crb, CIAA.ta, CIAA.ta_latch, CIAB.icr, CIAB.imask, CIAB.cra, CIAB.crb, CIAB.ta, CIAB.ta_latch);
    }
    return 0;
}
