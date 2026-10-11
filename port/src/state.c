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

/*
 * Formatet (MOONSAV2): magi, formatversjon, CRC for spillfilene, og saa delene.
 * Hver del er merke (4 tegn), versjon, lengde og innhold. Ved lasting maa en del
 * ha samme versjon og nøyaktig samme lengde. Deler porten selv har lagt til og som
 * trygt kan begynne paa nytt (nettspillmenyen, det meste av Hver for seg, tegnelisten,
 * Blitter-storrelsen) faar standardverdier hvis de mangler eller er endret, saa en
 * lagring fra en eldre utgave fortsatt kan brukes. Amigaen (minne, CPU, brikkene,
 * lyden) og originalene til ridderne som er tatt over i Hver for seg, maa passe.
 *
 * Strukturene har bare tall og tegn (ingen pekere), og er like store paa PC
 * (64 bit), Windows og i nettleseren (32 bit), saa lagringene kan flyttes mellom dem.
 *
 * Endrer en del betydning uten aa endre lengde, oekes versjonen i tabellen under.
 */
#define SAVE_MAGIC    "MOONSAV2"
#define SAVE_FORMAT   1u
#define OLD_MAGIC     "MOONSTAT"           /* formatet foer 2026-10-11 (bare versjon 13 kan leses) */
#define OLD_VERSION   13u

bool state_any_game;
const char *state_feil = "";

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

static void mem_state(StateIO *s)  { state_io(s, chip, sizeof chip); state_io(s, fast, sizeof fast); }
static void mach_state(StateIO *s) { STATE_VAR(s, M); STATE_VAR(s, IN); }
static void cust_state(StateIO *s) { STATE_VAR(s, C); STATE_VAR(s, B); }
static void cia_state(StateIO *s)  { STATE_VAR(s, CIAA); STATE_VAR(s, CIAB); }
void cpu_state(StateIO *s);         /* cpu_state.c */
static void blit_state(StateIO *s)
{
    extern unsigned blit_w, blit_h;
    STATE_VAR(s, blit_w);
    STATE_VAR(s, blit_h);
}
static void blit_standard(void) { extern unsigned blit_w, blit_h; blit_w = blit_h = 0; }

typedef struct {
    char tag[5];
    uint32_t ver;
    void (*io)(StateIO *);
    void (*standard)(void);                /* NULL = maa finnes og passe */
    const char *navn;                      /* til meldingen */
} Del;

/* rekkefolgen er den samme som foer: Amigaen forst, saa lappene */
static const Del deler[] = {
    { "MEM ", 1, mem_state,   NULL,           "minnet" },
    { "MACH", 1, mach_state,  NULL,           "maskinen" },
    { "CUST", 1, cust_state,  NULL,           "brikkene" },
    { "CIA ", 1, cia_state,   NULL,           "CIA-brikkene" },
    { "CPU ", 1, cpu_state,   NULL,           "68000" },
    { "AUD ", 1, paula_state, NULL,           "lyden" },
    { "WHD ", 1, whd_state,   NULL,           "WHDLoad" },
    { "MOET", 1, game_state_moete, NULL,      "moetet mellom to riddere" },
    { "GAME", 1, game_state,  game_standard,  "tegnelisten" },
    { "PTCH", 1, patch_state, NULL,           "tekstene" },
    { "MENY", 1, meny_state,  meny_standard,  "nettspillmenyen" },
    { "HVT ", 1, hver_state_tatt, NULL,       "ridderne som er tatt over" },
    { "HVER", 1, hver_state,  hver_standard,  "Hver for seg" },
    { "BLIT", 1, blit_state,  blit_standard,  "Blitteren" },
};
#define N_DELER (sizeof deler / sizeof deler[0])

static void put32(StateIO *s, uint32_t v) { STATE_VAR(s, v); }

static bool save_all(StateIO *s)
{
    char magic[8];
    memcpy(magic, SAVE_MAGIC, 8);
    state_io(s, magic, 8);
    put32(s, SAVE_FORMAT);
    put32(s, files_game_crc());
    put32(s, (uint32_t)N_DELER);
    for (size_t i = 0; i < N_DELER; i++) {
        state_io(s, (void *)deler[i].tag, 4);
        put32(s, deler[i].ver);
        size_t lpos = s->pos;
        put32(s, 0);
        size_t start = s->pos;
        deler[i].io(s);
        if (s->error) return false;
        uint32_t len = (uint32_t)(s->pos - start);
        memcpy(s->buf + lpos, &len, 4);
    }
    return !s->error;
}

static uint32_t les32(const uint8_t *p) { uint32_t v; memcpy(&v, p, 4); return v; }

/* Finner delene i bufferet (sjekker bare rammene, endrer ingenting) */
typedef struct { const uint8_t *data; uint32_t ver, len; bool finnes; } Funnet;

static bool finn_deler(const uint8_t *buf, size_t size, Funnet *f)
{
    if (size < 20) { state_feil = "Lagringen er skadet (for kort)."; return false; }
    uint32_t format = les32(buf + 8), game = les32(buf + 12), n = les32(buf + 16);
    if (format > SAVE_FORMAT) { state_feil = "Lagringen er laget med en nyere utgave av Moonstone."; return false; }
    if (!state_any_game && game != files_game_crc()) { state_feil = "Lagringen er laget med andre spillfiler."; return false; }
    size_t pos = 20;
    memset(f, 0, sizeof(Funnet) * N_DELER);
    for (uint32_t k = 0; k < n; k++) {
        if (pos + 12 > size) { state_feil = "Lagringen er skadet (slutter for tidlig)."; return false; }
        const uint8_t *h = buf + pos;
        uint32_t ver = les32(h + 4), len = les32(h + 8);
        if (len > size - pos - 12) { state_feil = "Lagringen er skadet (slutter for tidlig)."; return false; }
        for (size_t i = 0; i < N_DELER; i++)
            if (!memcmp(h, deler[i].tag, 4)) { f[i] = (Funnet){ h + 12, ver, len, true }; break; }
        pos += 12 + (size_t)len;          /* ukjente deler hoppes over */
    }
    return true;
}

/* Lengden en del faar naar den lagres naa (for aa sjekke at den passer) */
static size_t lengde_naa(size_t i)
{
    StateIO s = { .saving = true };
    deler[i].io(&s);
    size_t n = s.error ? (size_t)-1 : s.size;
    free(s.buf);
    return n;
}

/* Kjennetegn paa formatet (delenes merke, versjon og lengde). Nettspill sammenligner
 * det, saa en gjest med en eldre side ikke blir staaende og vente paa en tilstand den
 * ikke kan lese. */
uint32_t state_format_id(void)
{
    uint32_t h = SAVE_FORMAT;
    for (size_t i = 0; i < N_DELER; i++) {
        uint32_t v[2] = { deler[i].ver, (uint32_t)lengde_naa(i) };
        h = h * 31u + crc32_calc((const uint8_t *)deler[i].tag, 4);
        h = h * 31u + crc32_calc((const uint8_t *)v, sizeof v);
    }
    return h;
}

static char feiltekst[160];

static bool load_new(const uint8_t *buf, size_t size)
{
    Funnet f[N_DELER];
    if (!finn_deler(buf, size, f)) return false;
    bool passer[N_DELER];
    for (size_t i = 0; i < N_DELER; i++) {
        passer[i] = f[i].finnes && f[i].ver == deler[i].ver && f[i].len == lengde_naa(i);
        if (!passer[i] && !deler[i].standard) {
            snprintf(feiltekst, sizeof feiltekst, "Lagringen er fra en utgave der %s er lagret annerledes, og kan ikke brukes.", deler[i].navn);
            state_feil = feiltekst;
            return false;
        }
    }
    for (size_t i = 0; i < N_DELER; i++) {
        if (passer[i]) {
            StateIO s = { .saving = false, .buf = (uint8_t *)f[i].data, .size = f[i].len };
            deler[i].io(&s);
            if (s.error) { state_feil = "Lagringen er skadet."; return false; }
        } else {
            deler[i].standard();
        }
    }
    /* en lagring fra et spill som var stoppet (F10 eller en feil) skal kunne spilles videre */
    M.aborted = false;
    M.abort_msg[0] = 0;
    return true;
}

/* Formatet foer 2026-10-11: alt etter hverandre, uten deler */
static uint32_t old_layout_id(void)
{
    return (uint32_t)(sizeof(Machine) * 7919u + sizeof(Custom) * 104729u + sizeof(Blitter) * 31u
                      + sizeof(AudChan) * 131u + sizeof(Cia) * 17u + sizeof(void *));
}

static bool load_old(const uint8_t *buf, size_t size)
{
    if (size < 20) { state_feil = "Lagringen er skadet (for kort)."; return false; }
    uint32_t ver = les32(buf + 8), lay = les32(buf + 12), game = les32(buf + 16);
    if (ver != OLD_VERSION) {
        snprintf(feiltekst, sizeof feiltekst, "Lagringen er fra en eldre utgave (versjon %u) som ikke kan leses.", ver);
        state_feil = feiltekst;
        return false;
    }
    if (lay != old_layout_id()) { state_feil = "Lagringen er laget paa en annen maskintype (PC eller nett) med en eldre utgave."; return false; }
    if (!state_any_game && game != files_game_crc()) { state_feil = "Lagringen er laget med andre spillfiler."; return false; }
    StateIO s = { .saving = false, .buf = (uint8_t *)buf + 20, .size = size - 20 };
    amiga_state(&s);
    paula_state(&s);
    video_state(&s);
    whd_state(&s);
    game_state(&s);
    game_state_moete(&s);
    patch_state(&s);
    meny_state(&s);
    hver_state_gammel(&s);
    blit_state(&s);
    if (s.error) { state_feil = "Lagringen er skadet."; return false; }
    M.aborted = false;
    M.abort_msg[0] = 0;
    return true;
}

bool state_save_mem(uint8_t **buf, size_t *size)
{
    StateIO s = { .saving = true };
    if (!save_all(&s)) { free(s.buf); return false; }
    *buf = s.buf;
    *size = s.size;
    return true;
}

bool state_load_mem(const uint8_t *buf, size_t size)
{
    state_feil = "";
    bool ny = size >= 8 && !memcmp(buf, SAVE_MAGIC, 8);
    bool gammel = size >= 8 && !memcmp(buf, OLD_MAGIC, 8);
    if (!ny && !gammel) { state_feil = "Filen er ikke en lagring fra Moonstone."; return false; }
    uint8_t *backup;
    size_t bsize;
    if (!state_save_mem(&backup, &bsize)) { state_feil = "Ikke nok minne til aa laste."; return false; }
    if (ny ? load_new(buf, size) : load_old(buf, size)) { free(backup); return true; }
    const char *grunn = state_feil;
    load_new(backup, bsize);               /* legg tilbake det som var */
    state_feil = grunn;
    free(backup);
    return false;
}

/* Filer: stiene er UTF-8 (SDL_GetPrefPath gir det). Windows sin fopen bruker
 * tegntabellen, saa et brukernavn med ae, oe eller aa ville gi feil; der brukes _wfopen. */
#ifdef _WIN32
#include <windows.h>
static FILE *aapne_fil(const char *path, const wchar_t *mode)
{
    wchar_t w[1024];
    if (!MultiByteToWideChar(CP_UTF8, 0, path, -1, w, 1024)) return NULL;
    return _wfopen(w, mode);
}
#define FIL_SKRIV L"wb"
#define FIL_LES   L"rb"
static bool bytt_navn(const char *fra, const char *til)
{
    wchar_t a[1024], b[1024];
    if (!MultiByteToWideChar(CP_UTF8, 0, fra, -1, a, 1024) || !MultiByteToWideChar(CP_UTF8, 0, til, -1, b, 1024)) return false;
    return MoveFileExW(a, b, MOVEFILE_REPLACE_EXISTING) != 0;
}
#else
static FILE *aapne_fil(const char *path, const char *mode) { return fopen(path, mode); }
#define FIL_SKRIV "wb"
#define FIL_LES   "rb"
static bool bytt_navn(const char *fra, const char *til) { return rename(fra, til) == 0; }
#endif

/* Skriver til STI.tmp og bytter navn til slutt, saa en god lagring aldri blir
 * halvveis overskrevet (full disk, krasj midt i skrivingen). */
bool state_save_file(const char *path)
{
    uint8_t *buf;
    size_t size;
    if (!state_save_mem(&buf, &size)) return false;
    char tmp[1100];
    snprintf(tmp, sizeof tmp, "%s.tmp", path);
    FILE *f = aapne_fil(tmp, FIL_SKRIV);
    bool ok = f && fwrite(buf, 1, size, f) == size;
    if (f && fclose(f) != 0) ok = false;
    free(buf);
    if (ok) ok = bytt_navn(tmp, path);
    if (!ok) remove(tmp);
    return ok;
}

bool state_load_file(const char *path)
{
    state_feil = "";
    FILE *f = aapne_fil(path, FIL_LES);
    if (!f) { state_feil = "Fant ikke filen."; return false; }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (n <= 0) { fclose(f); state_feil = "Filen er tom."; return false; }
    uint8_t *buf = malloc((size_t)n);
    bool ok = buf && fread(buf, 1, (size_t)n, f) == (size_t)n;
    fclose(f);
    if (!ok) state_feil = buf ? "Kunne ikke lese filen." : "Ikke nok minne til aa laste.";
    if (ok) ok = state_load_mem(buf, (size_t)n);
    free(buf);
    return ok;
}

bool state_file_rename(const char *fra, const char *til) { return bytt_navn(fra, til); }

/* finnes filen (for meldingene paa PC) */
bool state_file_exists(const char *path)
{
    FILE *f = aapne_fil(path, FIL_LES);
    if (f) fclose(f);
    return f != NULL;
}

uint32_t state_ram_hash(void)
{
    uint32_t h = crc32_calc(chip, CHIP_SIZE);
    h ^= crc32_calc(fast, 0x80000) * 3u;
    h ^= crc32_calc((const uint8_t *)&C, sizeof C) * 5u;
    return h;
}
