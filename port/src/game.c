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

static bool observe_velg(void) { velg_bilde = M.frame; return false; }
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

static bool observe_valg(void) { valg_bilde = M.frame; return false; }

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
    hooks_register_patch(0x080ab8, observe_moete, "moete mellom riddere (observer)");
    hooks_register_patch(0x080c52, observe_rulle, "beskyttelsesrullen (observer)");
    hooks_register_patch(0x080c98, observe_rulle_slutt, "beskyttelsesrullen slutt (observer)");
    hooks_register_patch(0x080b40, observe_kamp, "kampen i moetet (observer)");
    hooks_register_patch(0x080ba4, observe_plyndring, "plyndringen (observer)");
    hooks_register_patch(0x080bd8, observe_moete_slutt, "moetet slutt (observer)");
}

/* ny maskin (amiga_reset): ingen lokker sett, intet moete */
void game_reset(void)
{
    valg_bilde = navn_bilde = velg_bilde = 0xffffffffu;
    moete = MOETE_INGEN;
}

void game_state(StateIO *s)
{
    STATE_VAR(s, cels);
    STATE_VAR(s, n_cels);
    STATE_VAR(s, background);
    STATE_VAR(s, moete);
    if (!s->saving) valg_bilde = navn_bilde = velg_bilde = 0xffffffffu;    /* et annet bilde enn da lokka gikk */
}
