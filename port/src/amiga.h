/*
 * amiga.h - felles definisjoner for Moonstone-porten.
 *
 * Porten kjorer originalkoden til Moonstone (Mindscape 1991) paa en emulert
 * Amiga 500 (OCS, PAL): 68000 (Musashi), Agnus (Copper, Blitter, DMA), Denise
 * (bitplan og sprites), Paula (lyd og avbrudd) og to CIA 8520. Spillet startes
 * slik WHDLoad gjor det: slaven (Moonstone.Slave) lastes og kalles, og
 * resload-funksjonene den bruker er skrevet i C (whdload.c).
 *
 * Tid maales i CPU-sykluser (7,09 MHz PAL). En fargeklokke (CCK) er to
 * CPU-sykluser, en linje er 227 CCK, et bilde er 313 linjer (49,92 Hz).
 */
#ifndef AMIGA_H
#define AMIGA_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* ------------------------------------------------------------ klokker */
#define CPU_HZ        7093790
#define CCK_HZ        3546895
#define LINE_CCK      227
#define LINE_CYC      (LINE_CCK * 2)
#define FRAME_LINES   313
#define FRAME_CYC     ((uint64_t)LINE_CYC * FRAME_LINES)
#define ECLOCK_DIV    10                  /* CIA-ene teller E-klokken, CPU/10 */
#define AMIGA_HZ      ((double)CPU_HZ / FRAME_CYC)

/* ------------------------------------------------------------ minne */
#define CHIP_SIZE     0x100000            /* 1 MB chip-minne fra adresse 0 */
#define FAST_BASE     0x200000            /* 2 MB fast-minne: ExpMem, slaven, resload */
#define FAST_SIZE     0x200000
#define EXPMEM_BASE   0x200000
#define SLAVE_BASE    0x300000
#define RESLOAD_BASE  0x3f0000            /* hoppetabellen til resload (bare RTS) */
#define RESLOAD_SIZE  0x200
#define SSP_INIT      0x3fff00

extern uint8_t chip[CHIP_SIZE];
extern uint8_t fast[FAST_SIZE];

/* ------------------------------------------------------------ bildet */
/* Rammebufferet dekker hele det synlige PAL-omraadet i hires-piksler.
 * FB_X0 er forste lowres-piksel i DIW-koordinater, FB_Y0 forste linje. */
#define FB_W          720
#define FB_H          288
#define FB_X0         0x5e
#define FB_Y0         0x19

/* ------------------------------------------------------------ lyd */
#define AUDIO_RATE    48000
#define AUDIO_RING    16384               /* stereo-rammer i ringbufferet */

/* ------------------------------------------------------------ inndata */
/* Knapper for en joystick. Port 1 er venstre (JOY0DAT, mus), port 2 hoyre (JOY1DAT). */
enum {
    JOY_UP = 1, JOY_DOWN = 2, JOY_LEFT = 4, JOY_RIGHT = 8,
    JOY_FIRE = 16, JOY_FIRE2 = 32
};

typedef struct {
    uint8_t joy[2];                       /* [0] = port 1, [1] = port 2 */
    int16_t mouse_dx, mouse_dy;           /* port 1 som mus (ikke brukt av spillet) */
} Input;

/* ------------------------------------------------------------ custom-brikkene */
typedef struct {
    uint16_t dmacon, intena, intreq, adkcon;
    uint16_t copcon;
    uint32_t cop1lc, cop2lc, coppc;
    int      cop_state;                   /* COP_* */
    uint16_t cop_ir1, cop_ir2;
    uint64_t cop_time;                    /* naar Copper kan gjore neste ting */
    uint16_t diwstrt, diwstop, ddfstrt, ddfstop;
    uint16_t bplcon0, bplcon1, bplcon2, bplcon3;
    int16_t  bpl1mod, bpl2mod;
    uint32_t bplpt[6];
    uint16_t color[32];
    uint32_t sprpt[8];
    uint16_t sprpos[8], sprctl[8], sprdata[8], sprdatb[8];
    uint8_t  spr_armed[8];                /* sprite vises paa denne linjen */
    uint8_t  spr_dma[8];                  /* 0 venter paa kontrollord, 1 venter paa VSTART, 2 viser */
    uint16_t clxcon, clxdat;
    uint16_t potgo;
    uint16_t joy0dat, joy1dat;            /* musetellere (port 1 som mus) */
    uint16_t serper, serdat;
    uint16_t dsklen, dsksync;
    uint16_t beamcon0;
} Custom;

enum { COP_STOP, COP_FETCH, COP_WAIT };

typedef struct {
    uint16_t con0, con1, afwm, alwm;
    uint32_t pt[4];                       /* A, B, C, D */
    int16_t  mod[4];
    uint16_t dat[4];
    bool     busy;
    bool     zero;
    uint64_t done_time;
    uint32_t blits;                       /* teller, for statistikk */
} Blitter;

typedef struct {
    uint32_t lc;
    uint16_t len, per, vol, dat;
    /* intern tilstand */
    int      state;                       /* 0 av, 1 DMA, 2 manuell */
    uint32_t pt;
    uint32_t lencnt;
    uint16_t buf;                         /* ordet som spilles */
    int      bytepos;                     /* 0 = hoy byte, 1 = lav byte */
    int32_t  percnt;                      /* 1/256 CCK igjen paa denne samplen */
    int8_t   sample;
    bool     manual_done;
} AudChan;

typedef struct {
    uint8_t  pra, prb, ddra, ddrb;
    uint16_t ta, tb, ta_latch, tb_latch;
    uint8_t  cra, crb;
    uint8_t  icr, imask;
    uint32_t tod, alarm, tod_latch;
    bool     tod_latched, tod_halt;
    uint8_t  sdr;
    bool     ta_load_pending, tb_load_pending;
} Cia;

/* ------------------------------------------------------------ hele maskinen */
typedef struct {
    uint64_t clk;                         /* CPU-sykluser siden start */
    uint64_t line_clk;                    /* starten paa denne linjen */
    int      vpos;                        /* 0..312 */
    uint32_t frame;                       /* antall ferdige bilder */
    bool     lof;                         /* lang ramme (alltid i PAL uten interlace) */
    uint64_t eclk_done;                   /* E-klokke-tikk CIA-ene har talt */
    uint64_t stall_until;                 /* resload_Delay venter til hit (0 = ingen) */
    bool     stall_button;                /* Delay kan avbrytes med fire */
    bool     aborted;                     /* resload_Abort er kalt */
    char     abort_msg[128];
    uint32_t kbd_wait;                    /* bilder til neste tast kan sendes */
    bool     kbd_ready;
    uint8_t  kbd_queue[32];
    int      kbd_head, kbd_tail;
    bool     kbd_handshake;
} Machine;

extern Machine  M;
extern Custom   C;
extern Blitter  B;
extern AudChan  AUD[4];
extern Cia      CIAA, CIAB;
extern Input    IN;

/* ------------------------------------------------------------ amiga.c */
bool     amiga_init(void);                /* krever at spillfilene er lastet (files.c) */
void     amiga_reset(void);
void     amiga_run_frame(void);           /* kjorer til neste bilde er ferdig */
uint64_t amiga_now(void);                 /* naa, i CPU-sykluser (ogsaa midt i en instruksjon) */
void     amiga_update_irq(void);
void     amiga_end_slice(void);           /* faar CPU-en til aa gi fra seg kontrollen snart */
int      amiga_hpos(void);                /* naavaerende CCK paa linjen */
void     amiga_key(int rawcode, bool down);
extern const uint32_t *amiga_framebuffer; /* FB_W x FB_H, byte R G B A */

uint32_t mem_read8(uint32_t a);
uint32_t mem_read16(uint32_t a);
uint32_t mem_read32(uint32_t a);
void     mem_write8(uint32_t a, uint32_t v);
void     mem_write16(uint32_t a, uint32_t v);
void     mem_write32(uint32_t a, uint32_t v);
/* direkte peker til minne (chip eller fast), eller NULL */
uint8_t *mem_ptr(uint32_t a, uint32_t len);

static inline uint16_t chip_r16(uint32_t a) { a &= CHIP_SIZE - 2; return (uint16_t)(chip[a] << 8 | chip[a + 1]); }
static inline void chip_w16(uint32_t a, uint16_t v) { a &= CHIP_SIZE - 2; chip[a] = (uint8_t)(v >> 8); chip[a + 1] = (uint8_t)v; }

/* ------------------------------------------------------------ custom.c */
void     custom_reset(void);
uint16_t custom_read(uint32_t reg);
void     custom_write(uint32_t reg, uint16_t v);
void     copper_vblank(void);
uint64_t copper_next_time(void);
void     copper_run(uint64_t until);
void     custom_line_start(void);
const char *custom_reg_name(unsigned reg);

/* ------------------------------------------------------------ blitter.c */
void     blitter_reset(void);
void     blitter_start(void);
void     blitter_finish(void);

/* ------------------------------------------------------------ video.c */
void     video_reset(void);
void     video_line_start(int vpos);
void     video_fetch(int vpos);           /* bitplan-DMA for linjen (ved DDFSTRT) */
void     video_line_end(int vpos);
void     video_reg_change(unsigned reg, uint16_t v);  /* logg til fargeskift midt paa linjen */
int      video_fetch_hpos(void);          /* CCK der bitplan-DMA starter paa denne linjen, -1 = ingen */
void     video_frame_done(void);
extern uint32_t video_fb[FB_W * FB_H];
extern int      video_diw[4];             /* x0, y0, x1, y1 av spillets vindu i rammebufferet */

/* lag.c: bildet delt i bakgrunn og forgrunn (HD-grafikk og effekter) */
#define LAG_W 320
#define LAG_H 200
extern bool     lag_paa, lag_gyldig;
extern uint32_t lag_bak[LAG_H * LAG_W], lag_for[LAG_H * LAG_W];
extern uint32_t lag_bak_hash, lag_bak_lys;
extern int      lag_for_antall;
void     lag_bygg(void);

/* ------------------------------------------------------------ paula.c */
void     paula_reset(void);
void     paula_write(unsigned reg, uint16_t v);
void     paula_dma_change(uint16_t old_dmacon, uint16_t new_dmacon);
void     paula_run(int cck);              /* gaar fram cck fargeklokker */
int      paula_take(int16_t *out, int max_frames);  /* henter ferdige samples (stereo) */
extern float paula_volume;
extern bool  paula_filter_led;

/* ------------------------------------------------------------ cia.c */
void     cia_reset(void);
uint8_t  cia_read(Cia *c, int reg);
void     cia_write(Cia *c, int reg, uint8_t v);
void     cia_tick(uint32_t eticks);       /* E-klokke-tikk siden sist */
void     cia_sync(void);                  /* teller tidtakerne fram til naa */
uint32_t cia_next_event(void);            /* E-tikk til neste underflyt, 0xffffffff = ingen */
void     cia_tod_vsync(void);
void     cia_tod_hsync(void);
void     cia_serial_in(uint8_t byte);     /* tastatur -> SDR paa CIA-A */
void     cia_update_irq(void);

/* ------------------------------------------------------------ whdload.c */
bool     whd_boot(void);                  /* laster slaven og setter CPU-en klar */
void     whd_call(unsigned offset);       /* CPU-en kaller resload + offset */
void     whd_delay_check(void);           /* avslutter resload_Delay naar tiden er ute */
extern int whd_buttonwait;
extern bool whd_mog_loaded;
extern int  whd_keyexit;
extern void (*whd_log)(const char *msg);

/* ------------------------------------------------------------ files.c */
/* Spillfilene: slaven og datamappen. Kan komme fra en zip med ISO-en, ISO-en
 * selv, en zip med Moonstone-mappen eller en vanlig mappe. */
bool     files_open(const char *path);
bool     files_open_mem(uint8_t *data, size_t size, const char *name); /* tar over data */
bool     files_open_embedded(void);       /* spillfila som er bygget inn (spilldata.c), false uten */
extern const unsigned char spill_innebygd[];
extern const size_t spill_innebygd_storrelse;
void     files_close(void);
/* Leser en fil fra spillmappen (Moonstone/...). Store og smaa bokstaver er likegyldig. */
uint8_t *files_read(const char *name, size_t *size);
bool     files_exists(const char *name, size_t *size);
extern char files_error[256];
/* Filer spillet lagrer (resload_SaveFile) ligger i minnet her; frontend kan skrive dem ut. */
bool     files_save(const char *name, const uint8_t *data, size_t size, size_t offset);
int      files_saved_count(void);
const char *files_saved_name(int i, const uint8_t **data, size_t *size);
uint32_t files_game_crc(void);
/* nettspill: filer spillet har brukt siden sist, og filer fra verten */
int      files_accessed_count(void);
const char *files_accessed_name(int i);
void     files_accessed_clear(void);
const uint8_t *files_peek(const char *path, size_t *size);
void     files_inject(const char *path, const uint8_t *data, size_t size);
void     files_empty(void);
int      files_add_overlay(const char *dir);   /* --mod: egne filer over data/ */

/* ------------------------------------------------------------ decrunch.c */
/* RNC ProPack metode 1 og 2. Returnerer utpakket lengde, 0 hvis ikke RNC, -1 ved feil. */
long     rnc_unpacked_size(const uint8_t *src, size_t len);
long     rnc_unpack(const uint8_t *src, size_t len, uint8_t *dst, size_t dstlen);
/* Spillets egen LZ-pakking (PIV, CEL, .t og andre). Returnerer utpakket lengde. */
size_t   ms_unpack(const uint8_t *src, size_t srclen, uint8_t *dst, size_t dstmax);

/* ------------------------------------------------------------ game.c */
/* Det vi vet om spillets data i minnet (se game.c). */
bool     game_mog_running(void);
int      game_port_player(int port);      /* spiller 0-3 som styrer port 0/1 naa, -1 = ukjent */
const char *game_knight_name(int k);
int      game_knight_player(int k);
/* tegnelisten: figurene spillet tegnet i siste bilde (game.c). Venstre kant er
 * x - xoff, flip = 1 naar figuren er speilvendt. */
typedef struct { int16_t cel, frame, x, y, w, h, xoff, flip; uint32_t target; } GameDraw;
#define GAME_MAX_DRAWS 256
extern GameDraw game_draws[GAME_MAX_DRAWS];
extern int      game_n_draws;
void     game_slave_pc(uint32_t pc);
void     game_register_hooks(void);
const char *game_cel_name(int i);
const char *game_background(void);

/* ------------------------------------------------------------ patch.c, meny.c */
extern uint32_t *whd_relocs;              /* langordene siste resload_Relocate rettet */
extern int       whd_n_relocs;
void     game_mog_ready(void);            /* mog er lastet og lappet: tekster.txt og menyen */
bool     meny_mog_ready(void);            /* true naar menyen er lappet */
void     patch_register_hooks(void);      /* lappene; de sjekker selv tilstanden */
void     patch_reset(void);               /* ny maskin: lappene av (kalles fra amiga_reset) */
void     meny_reset(void);
void     meny_register_hooks(void);
extern bool meny_online;                  /* frontenden kan nettspill: "Online Game" i tittelmenyen */
extern bool meny_title_seen;              /* tittelmenyen er naadd (oppstart rett til menyen) */
/* hendelser fra menyen til frontenden: kode | argument << 8 */
enum { MENY_EV_HOST = 1, MENY_EV_JOIN_PAGE, MENY_EV_JOIN_ROOM, MENY_EV_ENTER_CODE, MENY_EV_COPY,
       MENY_EV_PUBLIC, MENY_EV_LEAVE_JOIN, MENY_EV_BACK, MENY_EV_NAME };
/* kommandoer fra frontenden, brukes ved starten av et bilde (i nettspill hos alle) */
enum { MENY_CMD_HOSTING = 1, MENY_CMD_PLAYERS, MENY_CMD_PUBLIC, MENY_CMD_ROOMS, MENY_CMD_MESSAGE,
       MENY_CMD_SESSION_END, MENY_CMD_NAMES, MENY_CMD_MYNAME, MENY_CMD_PAGE, MENY_CMD_SELECT };
enum { MENY_PAGE_ONLINE = 1, MENY_PAGE_JOIN = 3 };   /* for MENY_CMD_PAGE */
int      meny_take_event(void);           /* 0 = ingen */
bool     meny_in_menu(void);              /* tittelmenyen (eller en nettspillside) er paa skjermen */
int      meny_row_at(int y);              /* raden et klikk paa linje y treffer, -1/-2 = ingen */
void     meny_command(int cmd, int arg, const char *text);

/* ------------------------------------------------------------ hooks.c */
typedef bool (*hook_fn)(void);
void     hooks_register(uint32_t addr, hook_fn fn, const char *name);
void     hooks_register_patch(uint32_t addr, hook_fn fn, const char *name);
void     hooks_clear(void);
void     hook_return(void);
void     hook_cycles(int n);              /* C-funksjonen bruker n sykluser, som originalen */
void     hooks_report(void);
extern bool hooks_disabled;
extern bool hooks_measure;
extern void (*hook_trace)(uint32_t pc);

/* ------------------------------------------------------------ state.c */
typedef struct {
    bool     saving;
    uint8_t *buf;
    size_t   pos, size, cap;
    bool     error;
} StateIO;
void     state_io(StateIO *s, void *p, size_t n);
#define  STATE_VAR(s, v) state_io((s), &(v), sizeof(v))
void     amiga_state(StateIO *s);
void     paula_state(StateIO *s);
void     video_state(StateIO *s);
void     whd_state(StateIO *s);
void     game_state(StateIO *s);
void     patch_state(StateIO *s);
void     meny_state(StateIO *s);
/* hele tilstanden til/fra minnet; kalleren frigjor buf med free() */
bool     state_save_mem(uint8_t **buf, size_t *size);
bool     state_load_mem(const uint8_t *buf, size_t size);
bool     state_save_file(const char *path);
bool     state_load_file(const char *path);
uint32_t state_ram_hash(void);            /* sjekksum av RAM og registre, for nettspill */
extern bool state_any_game;               /* gjest uten spillfiler: ikke sjekk hvilke filer tilstanden er laget med */

/* ------------------------------------------------------------ logg */
extern int  log_level;                    /* 0 stille, 1 viktig, 2 mye */
void        logf_(int level, const char *fmt, ...);
#define LOG(...)  logf_(1, __VA_ARGS__)
#define LOG2(...) logf_(2, __VA_ARGS__)

#endif
