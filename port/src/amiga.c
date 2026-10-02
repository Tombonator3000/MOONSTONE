/*
 * amiga.c - minnekartet, CPU-en og tidsstyringen.
 *
 * Maskinen gaar linje for linje. Paa hver linje kjores 68000 i biter mellom
 * hendelsene: neste Copper-instruksjon, Blitteren blir ferdig, en CIA-tidtaker
 * gaar ut, bitplan-DMA starter (DDFSTRT) og linjeslutt. Skriver CPU-en noe som
 * flytter en hendelse (Blitter, Copper, CIA, avbrudd), avsluttes biten tidlig
 * med amiga_end_slice(), saa neste hendelse kommer i riktig tid.
 *
 * Bildet tegnes linje for linje i video.c, og lyden lages i paula.c.
 */
#include "amiga.h"
#include "m68k.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

uint8_t chip[CHIP_SIZE];
uint8_t fast[FAST_SIZE];
Machine M;
Input   IN;
const uint32_t *amiga_framebuffer = video_fb;

static bool     in_cpu;                    /* vi er inne i m68k_execute */
static uint64_t slice_start;               /* M.clk da biten startet */

int log_level = 1;
void logf_(int level, const char *fmt, ...)
{
    if (level > log_level) return;
    va_list ap;
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
}

/* ------------------------------------------------------------ tid */
uint64_t amiga_now(void)
{
    return in_cpu ? slice_start + (uint64_t)m68k_cycles_run() : M.clk;
}

int amiga_hpos(void)
{
    uint64_t t = amiga_now() - M.line_clk;
    int h = (int)(t / 2);
    return h > LINE_CCK - 1 ? LINE_CCK - 1 : h;
}

void amiga_end_slice(void)
{
    if (in_cpu) m68k_end_timeslice();
}

/* ------------------------------------------------------------ avbrudd */
void amiga_update_irq(void)
{
    int level = 0;
    if (C.intena & 0x4000) {
        uint16_t act = C.intena & C.intreq & 0x3fff;
        if (act & 0x2000) level = 6;
        else if (act & 0x1800) level = 5;
        else if (act & 0x0780) level = 4;
        else if (act & 0x0070) level = 3;
        else if (act & 0x0008) level = 2;
        else if (act & 0x0007) level = 1;
    }
    m68k_set_irq(level);
    /* Musashi ser bare etter avbrudd mellom bitene, saa vi gir fra oss
     * kontrollen naar et nytt avbrudd kan tas. */
    if (level) amiga_end_slice();
}

int ami_int_ack(int level)
{
    (void)level;
    return M68K_INT_ACK_AUTOVECTOR;
}

/* ------------------------------------------------------------ minne */
uint8_t *mem_ptr(uint32_t a, uint32_t len)
{
    a &= 0xffffff;
    if (a + len <= CHIP_SIZE) return chip + a;
    if (a >= FAST_BASE && a + len <= FAST_BASE + FAST_SIZE) return fast + (a - FAST_BASE);
    return NULL;
}

static uint32_t io_read8(uint32_t a)
{
    if ((a & 0xff0000) == 0xbf0000 || (a & 0xe00000) == 0xa00000) {
        int reg = (a >> 8) & 15;
        if (a & 1) { if (!(a & 0x1000)) return cia_read(&CIAA, reg); }
        else       { if (!(a & 0x2000)) return cia_read(&CIAB, reg); }
        return 0xff;
    }
    if ((a & 0xfff000) == 0xdff000) {
        uint16_t w = custom_read(a & 0x1fe);
        return (a & 1) ? (w & 0xff) : (w >> 8);
    }
    LOG2("les8 fra ukjent adresse %06x\n", a);
    return 0;
}

static void io_write8(uint32_t a, uint32_t v)
{
    if ((a & 0xff0000) == 0xbf0000 || (a & 0xe00000) == 0xa00000) {
        int reg = (a >> 8) & 15;
        if (a & 1) { if (!(a & 0x1000)) cia_write(&CIAA, reg, (uint8_t)v); }
        else       { if (!(a & 0x2000)) cia_write(&CIAB, reg, (uint8_t)v); }
        return;
    }
    if ((a & 0xfff000) == 0xdff000) {
        /* 68000 legger byten paa begge halvdelene av databussen */
        custom_write(a & 0x1fe, (uint16_t)((v & 0xff) << 8 | (v & 0xff)));
        return;
    }
    LOG2("skriv8 %02x til ukjent adresse %06x\n", v & 0xff, a);
}

uint32_t mem_read8(uint32_t a)
{
    a &= 0xffffff;
    if (a < CHIP_SIZE) return chip[a];
    if (a - FAST_BASE < FAST_SIZE) return fast[a - FAST_BASE];
    return io_read8(a);
}

uint32_t mem_read16(uint32_t a)
{
    a &= 0xffffff;
    if (a < CHIP_SIZE) return (uint32_t)chip[a] << 8 | chip[a + 1];
    if (a - FAST_BASE < FAST_SIZE) { uint8_t *p = fast + (a - FAST_BASE); return (uint32_t)p[0] << 8 | p[1]; }
    if ((a & 0xfff000) == 0xdff000) return custom_read(a & 0x1fe);
    return io_read8(a) << 8 | io_read8(a + 1);
}

uint32_t mem_read32(uint32_t a)
{
    return mem_read16(a) << 16 | mem_read16(a + 2);
}

void mem_write8(uint32_t a, uint32_t v)
{
    a &= 0xffffff;
    if (a < CHIP_SIZE) { chip[a] = (uint8_t)v; return; }
    if (a - FAST_BASE < FAST_SIZE) { fast[a - FAST_BASE] = (uint8_t)v; return; }
    io_write8(a, v);
}

void mem_write16(uint32_t a, uint32_t v)
{
    a &= 0xffffff;
    if (a < CHIP_SIZE) { chip[a] = (uint8_t)(v >> 8); chip[a + 1] = (uint8_t)v; return; }
    if (a - FAST_BASE < FAST_SIZE) { uint8_t *p = fast + (a - FAST_BASE); p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v; return; }
    if ((a & 0xfff000) == 0xdff000) { custom_write(a & 0x1fe, (uint16_t)v); return; }
    if ((a & 0xff0000) == 0xbf0000) { io_write8(a, v >> 8); io_write8(a + 1, v & 0xff); return; }
    LOG2("skriv16 %04x til ukjent adresse %06x\n", v & 0xffff, a);
}

void mem_write32(uint32_t a, uint32_t v)
{
    mem_write16(a, v >> 16);
    mem_write16(a + 2, v & 0xffff);
}

/* Musashi */
unsigned int m68k_read_memory_8(unsigned int a)  { return mem_read8(a); }
unsigned int m68k_read_memory_16(unsigned int a) { return mem_read16(a); }
unsigned int m68k_read_memory_32(unsigned int a) { return mem_read32(a); }
void m68k_write_memory_8(unsigned int a, unsigned int v)  { mem_write8(a, v); }
void m68k_write_memory_16(unsigned int a, unsigned int v) { mem_write16(a, v); }
void m68k_write_memory_32(unsigned int a, unsigned int v) { mem_write32(a, v); }
unsigned int m68k_read_disassembler_8(unsigned int a)  { a &= 0xffffff; uint8_t *p = mem_ptr(a, 1); return p ? p[0] : 0; }
unsigned int m68k_read_disassembler_16(unsigned int a) { return m68k_read_disassembler_8(a) << 8 | m68k_read_disassembler_8(a + 1); }
unsigned int m68k_read_disassembler_32(unsigned int a) { return m68k_read_disassembler_16(a) << 16 | m68k_read_disassembler_16(a + 2); }

/* ------------------------------------------------------------ tastatur */
/* Tastaturet sender en byte om gangen gjennom CIA-A sin serieport. Neste byte
 * sendes naar spillet har kvittert (handshake paa KDAT, CRA bit 6) eller
 * etter en stund uten kvittering. */
void amiga_key(int rawcode, bool down)
{
    int next = (M.kbd_tail + 1) % (int)sizeof M.kbd_queue;
    if (next == M.kbd_head) return;
    M.kbd_queue[M.kbd_tail] = (uint8_t)((rawcode & 0x7f) | (down ? 0 : 0x80));
    M.kbd_tail = next;
}

static void keyboard_line(void)
{
    if (M.kbd_wait) { M.kbd_wait--; return; }
    if (M.kbd_head == M.kbd_tail) return;
    uint8_t code = M.kbd_queue[M.kbd_head];
    M.kbd_head = (M.kbd_head + 1) % (int)sizeof M.kbd_queue;
    /* WHDLoad avslutter naar QuitKey trykkes (F10 for Moonstone) */
    if (code == whd_keyexit && !M.aborted) {
        snprintf(M.abort_msg, sizeof M.abort_msg, "Spillet er avsluttet (F10).");
        M.aborted = true;
        return;
    }
    /* bitene sendes rotert ett steg til venstre og invertert */
    uint8_t sdr = (uint8_t)~((code << 1) | (code >> 7));
    cia_serial_in(sdr);
    M.kbd_handshake = false;
    M.kbd_wait = 40;                      /* linjer til neste (ca. 2,5 ms) */
}

/* ------------------------------------------------------------ CPU-kjoring */
static void run_cpu_until(uint64_t target)
{
    if (target <= M.clk) return;
    if (M.aborted) {
        M.clk = target;
        return;
    }
    int cycles = (int)(target - M.clk);
    in_cpu = true;
    slice_start = M.clk;
    int used = m68k_execute(cycles);
    in_cpu = false;
    M.clk = slice_start + (uint64_t)(used > 0 ? used : cycles);
}

static void run_line(void)
{
    uint64_t line_end = M.line_clk + LINE_CYC;
    while (M.clk < line_end) {
        uint64_t target = line_end;
        uint64_t t = copper_next_time();
        if (t < target) target = t;
        if (B.busy && B.done_time < target) target = B.done_time;
        int fh = video_fetch_hpos();
        uint64_t ft = fh >= 0 ? M.line_clk + (uint64_t)fh * 2 : UINT64_MAX;
        if (ft < target) target = ft;
        uint32_t ce = cia_next_event();
        if (ce != 0xffffffff) {
            uint64_t et = (M.eclk_done + ce) * ECLOCK_DIV;
            if (et < target) target = et;
        }
        if (target > M.clk) run_cpu_until(target);
        cia_sync();
        if (B.busy && M.clk >= B.done_time) blitter_finish();
        if (fh >= 0 && M.clk >= ft) video_fetch(M.vpos);
        copper_run(M.clk);
        whd_delay_check();
    }
    video_fetch(M.vpos);
}

void amiga_run_frame(void)
{
    uint32_t start_frame = M.frame;
    game_n_draws = 0;                      /* tegnelisten gjelder ett bilde */
    while (M.frame == start_frame) {
        M.line_clk = M.clk;
        if (M.vpos == 0) {
            /* vertikal blanking: avbrudd, Copper starter paa nytt, TOD paa CIA-A */
            C.intreq |= 0x0020;
            amiga_update_irq();
            copper_vblank();
            cia_tod_vsync();
        }
        cia_tod_hsync();
        custom_line_start();
        video_line_start(M.vpos);
        run_line();
        video_line_end(M.vpos);
        paula_run(LINE_CCK);
        keyboard_line();
        M.vpos++;
        if (M.vpos >= FRAME_LINES) {
            M.vpos = 0;
            M.frame++;
            video_frame_done();
        }
    }
}

/* ------------------------------------------------------------ oppstart */
static bool cpu_inited;

void amiga_reset(void)
{
    memset(chip, 0, sizeof chip);
    memset(fast, 0, sizeof fast);
    memset(&M, 0, sizeof M);
    patch_reset();
    M.lof = true;
    M.kbd_ready = true;
    custom_reset();
    blitter_reset();
    video_reset();
    paula_reset();
    cia_reset();
    if (!cpu_inited) {
        m68k_init();
        m68k_set_cpu_type(M68K_CPU_TYPE_68000);
        cpu_inited = true;
    }
    /* Resetvektorene peker inn i fast-minnet; whd_boot setter PC og stakk. */
    mem_write32(0, SSP_INIT);
    mem_write32(4, RESLOAD_BASE);
    m68k_pulse_reset();
}

bool amiga_init(void)
{
    amiga_reset();
    if (!whd_boot()) return false;
    return true;
}

/* ------------------------------------------------------------ tilstand */
void cpu_state(StateIO *s);   /* cpu_state.c */

void amiga_state(StateIO *s)
{
    state_io(s, chip, sizeof chip);
    state_io(s, fast, sizeof fast);
    STATE_VAR(s, M);
    STATE_VAR(s, C);
    STATE_VAR(s, B);
    STATE_VAR(s, CIAA);
    STATE_VAR(s, CIAB);
    STATE_VAR(s, IN);
    cpu_state(s);
}
