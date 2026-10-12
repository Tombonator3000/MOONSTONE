/*
 * game.c - det vi vet om dataene til Moonstone i minnet.
 *
 * Adressene gjelder naar hovedspillet (mog) er lastet til $80000. Introen
 * (program) ligger paa de samme adressene med annet innhold, saa vi sjekker
 * forst at mog kjorer (navnet SIR BANNER paa $95EE6).
 *
 * Ridderne: fire strukturer paa $84 byte fra $8D5B4.
 *   +$0B byte  hvem som styrer: 1 = joystick i port 1, 2 = joystick i port 2, 4 = datamaskinen
 *   +$36 long  figuren som ble valgt i Select a Knight (0-3), eller 4 for en ridder datamaskinen spiller
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

/* ------------------------------------------------------------ hvem styrer portene (nettspill) */
/* Select a Knight (sub_081C82) gir ridderne plass for plass: $8F49C er plassen som
 * faar neste ridder ($8D5B4, saa + $84 for hver), $8F4A0 hvor mange som gjenstaar.
 * Den som velger forst, faar altsaa plass 0 osv. Ridderen faar +$36 = figuren som
 * ble valgt (0 GODBER, 1 RICHARD, 2 JEFFREY, 3 EDWARD, $081ECA), ikke rekkefolgen,
 * saa nettspillet bruker plassen: spiller 1 er den som velger forst.
 *
 * Et moete mellom to riddere ($080AB8 til $080BD8, alle veier ut gaar dit):
 * $8CE94 er den som angriper og $8CE98 den angrepne. Beskyttelsesrullen
 * ($080C52-$080C98) er den angrepnes: vent_paa_fire leser port 2, og pekeren i
 * inventaret ($08C3EA) leser porten til ridderen i $8CE94 (port 1 naar +$0B er 1,
 * ellers port 2), som da er den angrepne ($080C82). I kampen ($080B40) har
 * mennesket som angriper port 2 og et angrepet menneske port 1 (+$0B), og
 * angriper datamaskinen, faar mennesket port 2. Etter kampen byttes de to om
 * naar den angrepne vant ($080B94), og den som plyndrer ($080BA4, $8CE94) styrer
 * pekeren med sin egen port. Rullen og plyndringen gir derfor begge portene til
 * den som velger. */
#define VELG_IGJEN  0x8f4a0
#define VELG_PLASS  0x8f49c
#define MOETE_A     0x8ce94
#define MOETE_B     0x8ce98
enum { MOETE_INGEN, MOETE_FOER, MOETE_RULLE, MOETE_KAMP, MOETE_PLYNDRING };

static uint32_t velg_bilde = 0xffffffffu;   /* sist lokka i Select a Knight leste joysticken */
static uint32_t navn_bilde = 0xffffffffu;   /* sist lokka for navnet leste tastene */
static uint8_t moete;                       /* MOETE_*, i lagringen */
static uint8_t ridder_klikk = 0xff;         /* 0-3 venter, 0xfe brukt, 0xff ingen */
static uint8_t kart_paa, kart_maal = 0xff;
static int16_t kart_x, kart_y, kart_fra_x, kart_fra_y, kart_sist_x, kart_sist_y;
static uint16_t kart_stille;

static uint16_t rd16(uint32_t a) { return (uint16_t)(chip[a] << 8 | chip[a + 1]); }

static bool menneske(int k)
{
    return k >= 0 && rd32(KNIGHTS + (uint32_t)k * KNIGHT_SIZE + K_PLAYER) <= 3;
}

static int styres_med(int k) { return chip[KNIGHTS + (uint32_t)k * KNIGHT_SIZE + K_CTRL]; }

/* Select a Knight eller navnet etterpaa er paa skjermen */
bool game_velger_ridder(void)
{
    if (!game_mog_running() || meny_in_menu()) return false;
    uint16_t igjen = rd16(VELG_IGJEN);
    if (igjen < 1 || igjen > 4 || knight_index(rd32(VELG_PLASS)) < 0) return false;
    return M.frame - velg_bilde <= 50 || M.frame - navn_bilde <= 50;
}

/* Plassen (0-3, rekkefolgen ridderne ble valgt i) til mennesket som styrer porten
 * akkurat naa, eller -1 naar alle kan styre (menyer, intro) eller datamaskinen
 * styrer. port: 0 = port 1, 1 = port 2. */
int game_port_player(int port)
{
    if (!game_mog_running() || meny_in_menu()) return -1;
    if (game_velger_ridder()) return port == 1 ? knight_index(rd32(VELG_PLASS)) : -1;
    int a = knight_index(rd32(MOETE_A)), b = knight_index(rd32(MOETE_B));
    switch (moete) {
    case MOETE_RULLE:
        return menneske(b) ? b : -1;
    case MOETE_KAMP:
        if (menneske(a) && styres_med(a) == (port == 1 ? 2 : 1)) return a;
        if (menneske(b) && styres_med(b) == (port == 1 ? 2 : 1)) return b;
        return -1;
    case MOETE_PLYNDRING:
        return menneske(a) ? a : -1;
    }
    if (port != 1) return -1;
    int k = knight_index(rd32(CUR_KNIGHT));
    return menneske(k) && styres_med(k) == 2 ? k : -1;
}

static bool observe_velg(void)
{
    velg_bilde = M.frame;
    if (ridder_klikk == 0xfe) ridder_klikk = 0xff;
    return false;
}
static bool observe_moete(void) { moete = MOETE_FOER; return false; }
static bool observe_rulle(void) { if (moete) moete = MOETE_RULLE; return false; }
static bool observe_rulle_slutt(void) { if (moete) moete = MOETE_FOER; return false; }
static bool observe_kamp(void) { if (moete) moete = MOETE_KAMP; return false; }
static bool observe_plyndring(void) { if (moete) moete = MOETE_PLYNDRING; return false; }
static bool observe_moete_slutt(void) { moete = MOETE_INGEN; return false; }

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

static bool observe_draw_at(uint32_t target_pointer)
{
    if (game_n_draws >= GAME_MAX_DRAWS) return false;
    uint32_t a0 = m68k_get_reg(NULL, M68K_REG_A0);
    GameDraw *d = &game_draws[game_n_draws++];
    d->cel = -1;
    for (int i = 0; i < n_cels; i++) if (cels[i].addr == a0) { d->cel = i; break; }
    d->frame = (int16_t)m68k_get_reg(NULL, M68K_REG_D0);
    d->x = (int16_t)m68k_get_reg(NULL, M68K_REG_D1);
    d->y = (int16_t)m68k_get_reg(NULL, M68K_REG_D2);
    d->target = rd32(target_pointer);     /* figurbuffer: hvor figuren tegnes */
    d->caller = mem_read32(m68k_get_reg(NULL, M68K_REG_A7));   /* returadressen: hvem som tegner */
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

static bool observe_draw(void) { return observe_draw_at(0x9e87e); }

/* program (intro og slutt) har sin egen IMAGEXCEL-rutine paa $08c214.
 * $086c02 setter fem maalplan fra $08c72a. Samme CEL-tabell/registerkontrakt
 * som mog. Dette er en lesende front-end-observator, aldri en CPU-erstatning.
 * Originalopkodene vernes saa en annen/modifisert programfil ikke feiltolkes. */
void game_program_pc(uint32_t pc)
{
    if (whd_mog_loaded || pc != 0x08c214 || mem_read16(pc) != 0x4a79 ||
        mem_read32(pc + 2) != 0x08cfce || mem_read16(0x08c22a) != 0x4a40) return;
    observe_draw_at(0x08c72a);
}

const char *game_cel_name(int i) { return i >= 0 && i < n_cels ? cels[i].name : ""; }
const char *game_background(void) { return background; }

/* ------------------------------------------------------------ valgene paa kartet */
/* Fire paa kartet ($0AADEE, sub_0ABB76): har stedet flere valg, tegnes de i en
 * brun boks («SIR GODBER may ...», «1 Enter Village», «2 Battle with KARI»), og
 * lokka paa $0ABBBA venter paa tastene 1-9. Valgene ligger paa $8EEEC, 8 byte
 * hver: long maal, long type (1 = kamp mot ridderen i maal, 2 = «Enter Lair»,
 * ellers teksten paa $96386 + (type - $15) * 4). Tom tabell slutter med maal 0.
 * Nettsiden viser valgene som knapper (mobil og spillkontroller) og trykker
 * tasten. Dette bare observerer; spillet kjorer som for. */
#define VALG_TABELL 0x8eeec
static uint32_t valg_bilde = 0xffffffffu;  /* sist lokka gikk (ikke i lagringen; nullstilles ved lasting) */

static bool observe_valg(void) { valg_bilde = M.frame; kart_paa = 0; kart_maal = 0xff; return false; }

/* long fra minnet, eller 0 utenfor chip-minnet (pekere fra spillets data) */
static uint32_t rd32_trygg(uint32_t a) { return a < CHIP_SIZE - 3 ? rd32(a) : 0; }

/* streng fra minnet, '_' blir mellomrom (riddernavnene) */
static void les_tekst(uint32_t a, char *ut, int n, int pos)
{
    if (a < 0x80000 || a >= CHIP_SIZE - 64) return;
    for (int i = 0; pos < n - 1; i++) {
        uint8_t c = chip[a + (uint32_t)i];
        if (c < 32 || c > 126) break;
        ut[pos++] = c == '_' ? ' ' : (char)c;
    }
    ut[pos] = 0;
}

static void trim(char *t)
{
    size_t n = strlen(t);
    while (n && t[n - 1] == ' ') t[--n] = 0;
}

/* antall valg (0 = spillet venter ikke), tekstene og overskriften */
int game_valg(char tekst[9][GAME_VALG_LEN], char *tittel)
{
    tittel[0] = 0;
    if (!game_mog_running() || M.frame - valg_bilde > 2) return 0;
    int n = 0;
    for (; n < 9; n++) {
        uint32_t e = VALG_TABELL + (uint32_t)n * 8, maal = rd32(e), type = rd32(e + 4);
        char *t = tekst[n];
        t[0] = 0;
        if (!maal) break;
        /* tekstene slaas opp gjennom lea-ene i sub_0ABD6E, som patch.c peker om naar
         * tekster.txt flytter en tekst (lea dat_096330 paa $0ABD78 osv.) */
        if (type == 2) les_tekst(rd32(0x0abd7a), t, GAME_VALG_LEN, 0);
        else if (type == 1) {
            les_tekst(rd32(0x0abd8e), t, GAME_VALG_LEN, 0);
            les_tekst(rd32_trygg(maal + K_NAME), t, GAME_VALG_LEN, (int)strlen(t));
        } else if (type >= 0x15 && type < 0x15 + 32) les_tekst(rd32_trygg(rd32(0x0abdac) + (type - 0x15) * 4), t, GAME_VALG_LEN, 0);
        trim(t);
    }
    les_tekst(rd32_trygg(rd32(CUR_KNIGHT) + K_NAME), tittel, GAME_VALG_LEN, 0);
    les_tekst(rd32(0x0abcb6), tittel, GAME_VALG_LEN, (int)strlen(tittel));    /* " may ... " ($0ABCB4) */
    trim(tittel);
    return n;
}

/* ------------------------------------------------------------ navnet til ridderen */
/* Etter Select a Knight skrives navnet (sub_081B26, lokka paa $081B7C): tastene
 * skriver, Return ($1C) eller fire godtar, Backspace ($0E) sletter. Bufferen er
 * pekeren paa $8F0B4, lengden ordet $8CE32 (maks 13). Ordet $8CE34 er 1 saa lenge
 * navnet skrives ($081B32 til $081C74), ogsaa mens det tegnes paa nytt etter en
 * tast (6-7 bilder, og da leser lokka ikke tastene). Nettsiden tilbyr et tekstfelt
 * paa mobil og sender en tast om gangen, naar lokka leser igjen (game_navn_klar). */
static bool observe_navn(void) { navn_bilde = M.frame; return false; }

/* Klikk bruker samme originale valg-/navneflyt som fire. Vent til joysticken
 * er lest, saa valget ikke forsvinner under tegning eller godtar navnet ogsaa. */
bool game_velg_ridder(int k)
{
    if (!game_velger_ridder() || game_navn() != NULL || ridder_klikk == 0xfe) return false;
    if (k == -1) k = rd16(0x8f51e);
    if (k < 0 || k > 3 || !(chip[0x8f4a2] & (1 << k))) return false;
    ridder_klikk = (uint8_t)k;
    return true;
}

static bool klikk_ridder(void)
{
    int k = ridder_klikk;
    if (k > 3) return false;
    ridder_klikk = 0xff;
    if (!(chip[0x8f4a2] & (1 << k)) || game_navn() != NULL) return false;
    ridder_klikk = 0xfe;                    /* dobbeltklikk skal ikke velge for neste spiller */
    chip[0x8f51e] = 0;
    chip[0x8f51f] = (uint8_t)k;
    m68k_set_reg(M68K_REG_D1, m68k_get_reg(NULL, M68K_REG_D1) | JOY_FIRE);
    /* btst er allerede kjoert. Z=0 velger fire-grenen, ogsaa med C-joysticken. */
    m68k_set_reg(M68K_REG_SR, m68k_get_reg(NULL, M68K_REG_SR) & ~4u);
    return false;
}

bool game_navn_klar(void) { return game_navn() != NULL && M.frame - navn_bilde <= 1; }

/* navnet saa langt, eller NULL naar spillet ikke venter paa navnet */
const char *game_navn(void)
{
    static char buf[GAME_VALG_LEN];
    if (!game_mog_running() || !(chip[0x8ce34] << 8 | chip[0x8ce35])) return NULL;
    uint32_t p = rd32(0x8f0b4);
    int n = (int)(uint16_t)(chip[0x8ce32] << 8 | chip[0x8ce33]);
    buf[0] = 0;
    if (p < 0x80000 || p >= CHIP_SIZE - 32 || n < 0 || n > 20) return buf;
    for (int i = 0; i < n; i++) buf[i] = chip[p + (uint32_t)i] == '_' ? ' ' : (char)chip[p + (uint32_t)i];
    buf[n] = 0;
    return buf;
}

/* ------------------------------------------------------------ klikkreise paa kartet
 * Bare maal og retning legges til. Originalen flytter ridderen en kartpiksel,
 * sjekker grenser, bruker terrengforsinkelsen og trekker fra turens budsjett.
 * Kartikonets fotpunkt er x + bredde/2, y + hoyde ($0AB79A). */
bool game_kart_aktiv(void)
{
    int k = knight_index(rd32(CUR_KNIGHT));
    return kart_paa && game_mog_running() && !meny_in_menu() && !game_peker_aktiv() &&
           menneske(k) && styres_med(k) == 2;
}

void game_kart_maal(int x, int y)
{
    if (x == -1 && y == -1) { kart_maal = 0xff; return; }
    if (!game_kart_aktiv() || x < 0 || x >= 320 || y < 0 || y >= 200) return;
    uint32_t r = rd32(CUR_KNIGHT), cel = rd32(0x8e7be);
    if (cel < 0x100 || cel >= CHIP_SIZE - 18) return;
    x -= rd16(cel + 14) / 2;
    y -= rd16(cel + 16);
    if (x < 0) x = 0;
    if (x > 310) x = 310;
    if (y < 0) y = 0;
    if (y > 190) y = 190;
    kart_x = (int16_t)x; kart_y = (int16_t)y;
    kart_fra_x = kart_sist_x = (int16_t)rd16(r + 0x7e);
    kart_fra_y = kart_sist_y = (int16_t)rd16(r + 0x80);
    kart_stille = 0;
    kart_maal = (uint8_t)knight_index(r);
}

static bool observe_kart(void)
{
    kart_paa = 1;
    if (kart_maal != 0xff && kart_maal != knight_index(rd32(CUR_KNIGHT))) kart_maal = 0xff;
    return false;
}

static bool kart_slutt(void) { kart_paa = 0; kart_maal = 0xff; return false; }

/* Etter move.w d1,$8E7A2, ikke paa returadressen rett etter les_joysticker.
 * Samme patch kjores med og uten C-krokene. En ny, fysisk joystick vinner. */
static bool kart_retning(void)
{
    if (kart_maal == 0xff) return false;
    if (!game_kart_aktiv() || kart_maal != knight_index(rd32(CUR_KNIGHT)) || rd16(0x8e7a2)) {
        kart_maal = 0xff; return false;
    }
    uint32_t r = rd32(CUR_KNIGHT);
    int x = (int16_t)rd16(r + 0x7e), y = (int16_t)rd16(r + 0x80);
    int endret_x = x - kart_sist_x, endret_y = y - kart_sist_y;
    if (endret_x < -1 || endret_x > 1 || endret_y < -1 || endret_y > 1) {
        kart_maal = 0xff; return false;    /* original teleport eller endret lagring */
    }
    if (x == kart_x && y == kart_y) { kart_maal = 0xff; return false; }
    if (x == kart_sist_x && y == kart_sist_y) {
        if (++kart_stille > 200) { kart_maal = 0xff; return false; }
    } else { kart_stille = 0; kart_sist_x = (int16_t)x; kart_sist_y = (int16_t)y; }
    int dx = kart_x - kart_fra_x, dy = kart_y - kart_fra_y;
    int ax = dx < 0 ? -dx : dx, ay = dy < 0 ? -dy : dy;
    int nx = x, ny = y;
    /* En rett, heltallsbasert rute. Feilen beregnes fra faktisk posisjon,
     * saa terrengets ventebilder ikke flytter maal eller spiser rutesteg. */
    if (ax >= ay && x != kart_x && ax) {
        nx += dx < 0 ? -1 : 1;
        int steg = nx - kart_fra_x; if (steg < 0) steg = -steg;
        ny = kart_fra_y + (dy < 0 ? -1 : 1) * ((steg * ay + ax / 2) / ax);
    } else if (y != kart_y && ay) {
        ny += dy < 0 ? -1 : 1;
        int steg = ny - kart_fra_y; if (steg < 0) steg = -steg;
        nx = kart_fra_x + (dx < 0 ? -1 : 1) * ((steg * ax + ay / 2) / ay);
    } else {
        kart_maal = 0xff; return false;    /* ingen gyldig ruteretning */
    }
    uint16_t b = (nx > x ? 1 : nx < x ? 2 : 0) | (ny > y ? 4 : ny < y ? 8 : 0);
    mem_write16(0x8e7a2, b);
    m68k_set_reg(M68K_REG_D1, b);
    return false;
}

/* ------------------------------------------------------------ maanereglene fra manualen (valg)
 * docs/undersokelser/maane.md. Originalen skifter maanefase hvert fjerde doegn, og
 * ingen monsterkode leser maanen. Manualen sier hvert tredje doegn, og at Ratmen
 * blir sterkere med maanen. Med valget paa:
 *  - fasen skifter hvert tredje doegn (dagtelleren $08CEA8 i sub_08064a)
 *  - skaden fra Ratmen (+$4D = $24) gaar fra x1 ved nymaane (bilde $2D) til x2 ved
 *    fullmaane ($31): i Ratmens slaghandler og paa slutten av skaderutinen sub_085ae0
 *  - feil M1 rettes: nytt spill nullstiller ogsaa faseindeksen $08F152
 * Valget er en del av spillet: det lagres (state.c, delen MAAN), saa en gjest i
 * nettspill og en lastet lagring faar det samme som verten eller lagringen hadde. */
int game_maaneregler;

static bool maane_dag(void)
{
    if (!game_maaneregler || !game_mog_running()) return false;
    if (rd16(0x8cea8) >= 3) mem_write16(0x8cea8, 4);     /* cmpi #3 / ble tar skiftet naa */
    return false;
}

static bool maane_nytt_spill(void)
{
    if (game_maaneregler && game_mog_running()) mem_write16(0x8f152, 0);
    return false;
}

/* Ratmen har slaghandleren dat_0855ce (tabellen $08D8DE etter +$4D = $24): angrep
 * type 4 trekker tabell[4] og smitter, type 8 trekker tabell[8], begge med
 * sub.w d0,$50(a1). Andre angrep gaar via dat_0858A8 og skaderutinen sub_085ae0. */
static bool ratmen_angriper(void)
{
    return game_maaneregler && game_mog_running() && mem_read8(m68k_get_reg(NULL, M68K_REG_A0) + 0x4d) == 0x24;
}

static void maane_skaler_d0(void)
{
    int bilde = (int16_t)rd16(0x8cea6) - 0x2d;
    if (bilde < 0 || bilde > 4) return;
    uint32_t d0 = m68k_get_reg(NULL, M68K_REG_D0);
    uint32_t skade = (d0 & 0xffff) * (uint32_t)(4 + bilde) / 4;
    if (skade > 0x7fff) skade = 0x7fff;
    m68k_set_reg(M68K_REG_D0, (d0 & 0xffff0000u) | skade);
}

static bool maane_skade(void)
{
    if (ratmen_angriper()) maane_skaler_d0();
    return false;
}

void game_state_maane(StateIO *s) { STATE_VAR(s, game_maaneregler); }
void game_maane_standard(void) { game_maaneregler = 0; }

/* Observatorene inne i lokker registreres som lapper: de endrer ingenting, og som
 * vanlige kroker ville --hook-cycles tatt dem for funksjoner og maalt feil. */
void game_register_hooks(void)
{
    valg_bilde = navn_bilde = velg_bilde = 0xffffffffu;
    moete = MOETE_INGEN;
    hooks_register(0x9dcec, observe_draw, "tegn_figur (observer)");
    hooks_register_patch(0x0abbba, observe_valg, "valgene paa kartet (observer)");
    hooks_register_patch(0x081b7c, observe_navn, "navnet til ridderen (observer)");
    hooks_register_patch(0x081cfa, observe_velg, "Select a Knight (observer)");
    hooks_register_patch(0x081d04, klikk_ridder, "Select a Knight (klikk)");
    hooks_register_patch(0x080ab8, observe_moete, "moete mellom riddere (observer)");
    hooks_register_patch(0x080c52, observe_rulle, "beskyttelsesrullen (observer)");
    hooks_register_patch(0x080c98, observe_rulle_slutt, "beskyttelsesrullen slutt (observer)");
    hooks_register_patch(0x080b40, observe_kamp, "kampen i moetet (observer)");
    hooks_register_patch(0x080ba4, observe_plyndring, "plyndringen (observer)");
    hooks_register_patch(0x080bd8, observe_moete_slutt, "moetet slutt (observer)");
    hooks_register_patch(0x0aac8c, observe_kart, "kartet (observer)");
    hooks_register_patch(0x0aad00, kart_retning, "kartet (klikkreise)");
    hooks_register_patch(0x0ab010, kart_slutt, "kartet slutt (klikkreise)");
    hooks_register_patch(0x08188c, kart_slutt, "tittel (klikkreise)");
    hooks_register_patch(0x080664, maane_dag, "maanereglene: fase hvert tredje doegn");
    hooks_register_patch(0x084c7e, maane_nytt_spill, "maanereglene: nytt spill nullstiller fasen (M1)");
    hooks_register_patch(0x0855de, maane_skade, "maanereglene: Ratmen sterkere med maanen (type 4)");
    hooks_register_patch(0x085608, maane_skade, "maanereglene: Ratmen sterkere med maanen (type 8)");
    hooks_register_patch(0x085b76, maane_skade, "maanereglene: Ratmen sterkere med maanen (skaderutinen)");
}

/* ny maskin (amiga_reset): ingen lokker sett, intet moete */
void game_reset(void)
{
    valg_bilde = navn_bilde = velg_bilde = 0xffffffffu;
    moete = MOETE_INGEN;
    game_peker_standard();
}

/* lagring uten (passende) tegneliste: tom liste, saa HD-laget viser originalgrafikken
 * til spillet pakker ut filene paa nytt, i stedet for navn fra et annet spill */
void game_standard(void)
{
    valg_bilde = navn_bilde = velg_bilde = 0xffffffffu;
    memset(cels, 0, sizeof cels);
    n_cels = 0;
    background[0] = 0;
}

/* moetefasen styrer hvem som har joysticken (rullen, kampen, plyndringen) og maa
 * passe med minnet; den lagres for seg (state.c, delen MOET), ikke med tegnelisten */
void game_state_moete(StateIO *s)
{
    STATE_VAR(s, moete);
}

void game_state(StateIO *s)
{
    STATE_VAR(s, cels);
    STATE_VAR(s, n_cels);
    STATE_VAR(s, background);
    if (!s->saving) valg_bilde = navn_bilde = velg_bilde = 0xffffffffu;    /* et annet bilde enn da lokka gikk */
}

/* ------------------------------------------------------------ pekeren (inventar, by, butikker)
 * Spillets peker ($098092/$098094, lowres-piksler fra oeverst til venstre i vinduet,
 * spissen) flyttes med joysticken av VBL-rutinen $08C3EA, som leser porten til ridderen
 * i $8E8B6. Fire maa komme paa porten: byen ($081242/$0813B2) og tavernaen leser port 2
 * selv, og tavernaen ser etter fire bare hvert 14. bilde. Et klikk paa nettsiden blir
 * derfor kommandoen MENY_CMD_PEKER: pekeren settes dit, og fire holdes i 16 bilder paa
 * begge portene (game_frame). Det skjer ved starten av et bilde hos alle i nettspill. */
#define PEKER_PAA  0x98088
#define PEKER_X    0x98092
#define PEKER_Y    0x98094
#define PEKER_EIER 0x8e8b6
static uint8_t peker_fire;
bool game_peker_aktiv(void) { return game_mog_running() && rd16(PEKER_PAA) != 0; }
/* porten som styrer pekeren (0 = port 1, 1 = port 2): eierens i inventaret, ellers port 2 */
int game_peker_port(void)
{
    int k = knight_index(rd32(PEKER_EIER));
    return (k >= 0 && styres_med(k) == 1) ? 0 : 1;
}
void game_peker(int x, int y)
{
    if (!game_peker_aktiv()) return;
    if (x < 0) x = 0;
    if (x > 0x13a) x = 0x13a;
    if (y < 0) y = 0;
    if (y > 0xc3) y = 0xc3;
    chip[PEKER_X] = (uint8_t)(x >> 8); chip[PEKER_X + 1] = (uint8_t)x;
    chip[PEKER_Y] = (uint8_t)(y >> 8); chip[PEKER_Y + 1] = (uint8_t)y;
    peker_fire = 16;
}
/* etter at inndataene for bildet er satt, foer amiga_run_frame */
void game_frame(void)
{
    if (IN.joy[1] || !game_kart_aktiv()) kart_maal = 0xff;
    if (!peker_fire) return;
    if (!game_peker_aktiv()) { peker_fire = 0; return; }
    IN.joy[0] |= JOY_FIRE;
    IN.joy[1] |= JOY_FIRE;
    peker_fire--;
}
void game_state_peker(StateIO *s)
{
    STATE_VAR(s, peker_fire); STATE_VAR(s, ridder_klikk);
    STATE_VAR(s, kart_paa); STATE_VAR(s, kart_maal);
    STATE_VAR(s, kart_x); STATE_VAR(s, kart_y); STATE_VAR(s, kart_fra_x); STATE_VAR(s, kart_fra_y);
    STATE_VAR(s, kart_sist_x); STATE_VAR(s, kart_sist_y); STATE_VAR(s, kart_stille);
}
void game_peker_standard(void)
{
    peker_fire = 0; ridder_klikk = 0xff; kart_paa = 0; kart_maal = 0xff;
    kart_x = kart_y = kart_fra_x = kart_fra_y = kart_sist_x = kart_sist_y = 0;
    kart_stille = 0;
}
