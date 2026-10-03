/*
 * web.c - grensesnittet mellom emulatorkjernen og nettleserversjonen (web/).
 *
 * Kompileres med emscripten sammen med resten av kjernen (make web). Alt som
 * har med bilde, lyd, taster og nettverk aa gjore ligger i JavaScript. Her er
 * bare funksjonene JavaScript kaller:
 *
 *   ms_open_embedded()      spillfila som er bygget inn (ms_has_embedded() sier om den finnes)
 *   ms_open_mem(ptr, n)     andre spillfiler fra en zip eller ISO i minnet (kjernen tar over bufferet)
 *   ms_start(buttonwait)    start maskinen
 *   ms_input(j0, j1)        joystickene for neste bilde (port 1 og port 2)
 *   ms_key(kode, ned)       en tast paa Amiga-tastaturet
 *   ms_frame()              kjor et bilde; bildet ligger i ms_fb(), lyden i ms_audio()
 *   ms_state_save/load      hele tilstanden til/fra minnet (lagring og nettspill)
 *   ms_hash()               sjekksum av tilstanden (nettspill: er alle i takt?)
 *   ms_guest()              gjest i nettspill: ingen egne spillfiler, faar dem fra verten
 */
#include "amiga.h"
#include <emscripten.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void decomp_register_all(void);

static int16_t  audio[AUDIO_RING * 2];
static int      audio_frames;
static uint8_t *state_buf;
static size_t   state_size;
static size_t   file_size;

EMSCRIPTEN_KEEPALIVE int ms_open_mem(uint8_t *data, int size)
{
    return files_open_mem(data, (size_t)size, "spill") ? 1 : 0;
}

/* spillfila som er bygget inn i kjernen (port/bin2c.py) */
EMSCRIPTEN_KEEPALIVE int ms_has_embedded(void) { return spill_innebygd_storrelse > 0; }
EMSCRIPTEN_KEEPALIVE int ms_open_embedded(void) { return files_open_embedded() ? 1 : 0; }

EMSCRIPTEN_KEEPALIVE const char *ms_error(void) { return files_error; }

EMSCRIPTEN_KEEPALIVE void ms_guest(void)
{
    files_empty();
    state_any_game = true;
}

EMSCRIPTEN_KEEPALIVE int ms_start(int buttonwait)
{
    whd_buttonwait = buttonwait;
    hooks_clear();
    decomp_register_all();
    return amiga_init() ? 1 : 0;
}

/* gjesten starter maskinen uten slave; tilstanden fra verten lastes etterpaa */
EMSCRIPTEN_KEEPALIVE void ms_start_empty(void)
{
    hooks_clear();
    decomp_register_all();
    amiga_reset();
}

EMSCRIPTEN_KEEPALIVE void ms_input(int j0, int j1)
{
    IN.joy[0] = (uint8_t)j0;
    IN.joy[1] = (uint8_t)j1;
}

EMSCRIPTEN_KEEPALIVE void ms_key(int code, int down) { amiga_key(code, down != 0); }

EMSCRIPTEN_KEEPALIVE void ms_frame(void)
{
    hver_frame();
    meny_frame();
    amiga_run_frame();
    audio_frames = paula_take(audio, AUDIO_RING);
    if (lag_paa) lag_bygg();
}

/* lagene (lag.c): bakgrunn og forgrunn hver for seg, 320 x 200 RGBA */
EMSCRIPTEN_KEEPALIVE void ms_lag_paa(int on) { lag_paa = on != 0; if (!lag_paa) lag_gyldig = false; }
EMSCRIPTEN_KEEPALIVE int ms_lag_gyldig(void) { return lag_gyldig ? 1 : 0; }
EMSCRIPTEN_KEEPALIVE void ms_lag_bygg(void) { lag_bygg(); }     /* lag paa nytt fra siste bilde */
EMSCRIPTEN_KEEPALIVE uint32_t *ms_lag_bak(void) { return lag_bak; }
EMSCRIPTEN_KEEPALIVE uint32_t *ms_lag_for(void) { return lag_for; }
EMSCRIPTEN_KEEPALIVE uint8_t *ms_lag_for_idx(void) { return lag_for_idx; }
EMSCRIPTEN_KEEPALIVE uint32_t ms_lag_hash(void) { return lag_bak_hash; }
EMSCRIPTEN_KEEPALIVE uint32_t ms_lag_lys(void) { return lag_bak_lys; }

EMSCRIPTEN_KEEPALIVE uint32_t *ms_fb(void) { return video_fb; }
EMSCRIPTEN_KEEPALIVE int ms_fb_w(void) { return FB_W; }
EMSCRIPTEN_KEEPALIVE int ms_fb_h(void) { return FB_H; }
EMSCRIPTEN_KEEPALIVE int *ms_diw(void) { return video_diw; }
EMSCRIPTEN_KEEPALIVE int16_t *ms_audio(void) { return audio; }
EMSCRIPTEN_KEEPALIVE int ms_audio_frames(void) { return audio_frames; }
/* hoyst 1: over det klipper int16-utgangen; nettsiden forsterker resten i lydtraaden */
EMSCRIPTEN_KEEPALIVE void ms_volume(float v) { paula_volume = v < 0 ? 0 : v > 1 ? 1 : v; }
EMSCRIPTEN_KEEPALIVE uint32_t ms_frame_no(void) { return M.frame; }
EMSCRIPTEN_KEEPALIVE double ms_hz(void) { return AMIGA_HZ; }
EMSCRIPTEN_KEEPALIVE int ms_aborted(void) { return M.aborted ? 1 : 0; }
EMSCRIPTEN_KEEPALIVE const char *ms_abort_msg(void) { return M.abort_msg; }
EMSCRIPTEN_KEEPALIVE uint32_t ms_hash(void) { return state_ram_hash(); }
EMSCRIPTEN_KEEPALIVE uint32_t ms_game_crc(void) { return files_game_crc(); }
EMSCRIPTEN_KEEPALIVE int ms_peek8(int a) { return (int)mem_read8((uint32_t)a); }
EMSCRIPTEN_KEEPALIVE int ms_peek16(int a) { return (int)mem_read16((uint32_t)a); }
EMSCRIPTEN_KEEPALIVE uint8_t *ms_chip(void) { return chip; }

EMSCRIPTEN_KEEPALIVE int ms_state_save(void)
{
    free(state_buf);
    state_buf = NULL;
    state_size = 0;
    if (!state_save_mem(&state_buf, &state_size)) return 0;
    return (int)state_size;
}

EMSCRIPTEN_KEEPALIVE uint8_t *ms_state_buf(void) { return state_buf; }

EMSCRIPTEN_KEEPALIVE int ms_state_load(const uint8_t *buf, int size)
{
    return state_load_mem(buf, (size_t)size) ? 1 : 0;
}

/* filer spillet har brukt (verten sender dem til gjestene) */
EMSCRIPTEN_KEEPALIVE int ms_accessed_count(void) { return files_accessed_count(); }
EMSCRIPTEN_KEEPALIVE const char *ms_accessed_name(int i) { return files_accessed_name(i); }
EMSCRIPTEN_KEEPALIVE void ms_accessed_clear(void) { files_accessed_clear(); }
EMSCRIPTEN_KEEPALIVE const uint8_t *ms_file_peek(const char *path)
{
    file_size = 0;
    return files_peek(path, &file_size);
}
EMSCRIPTEN_KEEPALIVE int ms_file_size(void) { return (int)file_size; }
EMSCRIPTEN_KEEPALIVE void ms_file_inject(const char *path, const uint8_t *data, int size)
{
    files_inject(path, data, (size_t)size);
}
EMSCRIPTEN_KEEPALIVE void ms_file_remove(const char *path) { files_remove(path); }

/* nettspill: hvem som styrer portene naa (se game.c) */
EMSCRIPTEN_KEEPALIVE int ms_port_player(int port) { return game_port_player(port); }
EMSCRIPTEN_KEEPALIVE const char *ms_knight_name(int k) { return game_knight_name(k); }

/* valgene paa kartet (game_valg): antallet fyller tekstene, som hentes etterpaa */
static char valg_tekst[9][GAME_VALG_LEN], valg_tittel[GAME_VALG_LEN];
EMSCRIPTEN_KEEPALIVE int ms_valg_antall(void) { return game_valg(valg_tekst, valg_tittel); }
EMSCRIPTEN_KEEPALIVE const char *ms_valg_tekst(int i) { return i >= 0 && i < 9 ? valg_tekst[i] : ""; }
EMSCRIPTEN_KEEPALIVE const char *ms_valg_tittel(void) { return valg_tittel; }
EMSCRIPTEN_KEEPALIVE const char *ms_navn(void) { const char *n = game_navn(); return n ? n : ""; }
EMSCRIPTEN_KEEPALIVE int ms_navn_aktiv(void) { return game_navn() != NULL; }
EMSCRIPTEN_KEEPALIVE int ms_navn_klar(void) { return game_navn_klar() ? 1 : 0; }
EMSCRIPTEN_KEEPALIVE int ms_knight_player(int k) { return game_knight_player(k); }

/* tegnelisten for HD-grafikk (se game.c og docs/hd-grafikk.md) */
EMSCRIPTEN_KEEPALIVE int ms_draw_count(void) { return game_n_draws; }
EMSCRIPTEN_KEEPALIVE const GameDraw *ms_draws(void) { return game_draws; }
EMSCRIPTEN_KEEPALIVE int ms_draw_size(void) { return (int)sizeof(GameDraw); }
EMSCRIPTEN_KEEPALIVE const char *ms_cel_name(int i) { return game_cel_name(i); }

/* nettspill i tittelmenyen (meny.c): slaas paa foer spillet starter */
EMSCRIPTEN_KEEPALIVE void ms_menu_enable(int on) { meny_online = on != 0; }
EMSCRIPTEN_KEEPALIVE int ms_menu_event(void) { return meny_take_event(); }
EMSCRIPTEN_KEEPALIVE void ms_menu_cmd(int cmd, int arg, const char *text) { meny_command(cmd, arg, text); }

/* "Hver for seg" (hver.c): kommandoer, og ridderne slik de er i spillet her */
EMSCRIPTEN_KEEPALIVE void ms_hver_cmd(int cmd, int arg, const char *text) { hver_kommando(cmd, arg, text); }
static int  ridder_ut[4];
static char ridder_navn[32];
EMSCRIPTEN_KEEPALIVE int ms_hver_kart(void) { return hver_kart() ? 1 : 0; }
EMSCRIPTEN_KEEPALIVE int *ms_hver_ridder(int k) { hver_ridder(k, ridder_ut); return ridder_ut; }
EMSCRIPTEN_KEEPALIVE int ms_hver_hendelse(void) { return hver_hendelse(); }
EMSCRIPTEN_KEEPALIVE const char *ms_hver_blob(int k) { return hver_blob(k); }
EMSCRIPTEN_KEEPALIVE const char *ms_hver_navn(int k) { snprintf(ridder_navn, sizeof ridder_navn, "%s", game_knight_name(k)); return ridder_navn; }
EMSCRIPTEN_KEEPALIVE int ms_menu_ready(void) { return meny_title_seen ? 1 : 0; }
/* klikk og Enter i menyen: er menyen framme, og hvilken rad ligger paa linje y */
EMSCRIPTEN_KEEPALIVE int ms_in_menu(void) { return meny_in_menu() ? 1 : 0; }
EMSCRIPTEN_KEEPALIVE int ms_menu_row(int y) { return meny_row_at(y); }
/* introen (program) gaar; den hoppes over med Esc */
EMSCRIPTEN_KEEPALIVE int ms_in_intro(void) { return whd_mog_loaded ? 0 : 1; }
