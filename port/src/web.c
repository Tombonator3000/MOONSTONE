/*
 * web.c - grensesnittet mellom emulatorkjernen og nettleserversjonen (web/).
 *
 * Kompileres med emscripten sammen med resten av kjernen (make web). Alt som
 * har med bilde, lyd, taster og nettverk aa gjore ligger i JavaScript. Her er
 * bare funksjonene JavaScript kaller:
 *
 *   ms_open_mem(ptr, n)     spillfilene fra en zip eller ISO i minnet (kjernen tar over bufferet)
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
    amiga_run_frame();
    audio_frames = paula_take(audio, AUDIO_RING);
}

EMSCRIPTEN_KEEPALIVE uint32_t *ms_fb(void) { return video_fb; }
EMSCRIPTEN_KEEPALIVE int ms_fb_w(void) { return FB_W; }
EMSCRIPTEN_KEEPALIVE int ms_fb_h(void) { return FB_H; }
EMSCRIPTEN_KEEPALIVE int *ms_diw(void) { return video_diw; }
EMSCRIPTEN_KEEPALIVE int16_t *ms_audio(void) { return audio; }
EMSCRIPTEN_KEEPALIVE int ms_audio_frames(void) { return audio_frames; }
EMSCRIPTEN_KEEPALIVE void ms_volume(float v) { paula_volume = v; }
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

/* nettspill: hvem som styrer portene naa (se game.c) */
EMSCRIPTEN_KEEPALIVE int ms_port_player(int port) { return game_port_player(port); }
EMSCRIPTEN_KEEPALIVE const char *ms_knight_name(int k) { return game_knight_name(k); }
EMSCRIPTEN_KEEPALIVE int ms_knight_player(int k) { return game_knight_player(k); }
