/*
 * hver.c - flerspiller "Hver for seg": hver spiller har sitt eget spill.
 * Se docs/flerspiller.md.
 *
 * Hver maskin spiller et vanlig enspillerspill (ridder 1). Plassene 2-4, som
 * datamaskinen ellers styrer, brukes av de andre spillerne i rommet: de merkes
 * som fjerne, turen deres hoppes over, og posisjonen, livet, hvilken ridder det
 * er og navnet skrives inn fra nettet ved starten av hvert bilde. Spillet tegner
 * dem selv paa kartet ($0AAB0A), og de kan utfordres der de staar ($080F56).
 *
 * Turen til en fjern ridder hoppes over i starten ($0AAC14): trekktelleren
 * ($8E7A0) settes til maks ($8E7C2), som naar tasten E trykkes, og vi hopper
 * rett til slutten av turen ($0AAE62). Tilstanden er med i lagringen.
 *
 * Kartet: de andre ridderne tegnes inn i bakgrunnen ($8CDE8) naar en tur
 * starter ($0AAC54), og skjermen bygges paa nytt fra bakgrunnen hvert bilde
 * ($0AAF38). Saa de fjerne ridderne flytter seg mens du har turen, tar vi en
 * kopi av bakgrunnen rett foer de tegnes, og naar en av dem har flyttet seg,
 * legges kopien tilbake og ridderne tegnes paa nytt (en liten rutine i ledig
 * chip-minne, kalt fra toppen av lokka paa kartet, $0AAC8C).
 *
 * Hele ridderen: strukturen ($84 byte) og tingene ridderen har (+$60 peker paa
 * $18 byte) sendes ogsaa, saa en fjern ridder har sin egen styrke, sitt gull og
 * sine ting her (HVER_BLOB). Felt som hoerer til plassen her (port, figur,
 * rutene paa kartet, pekere og posisjon) skrives ikke over.
 *
 * Kamp ($080AB8, a1 = den som blir angrepet): kan spilleren naas over nettet
 * (HVER_DUELL), blir det en duell: frontenden faar HVER_EV_DUELL, stopper etter
 * bildet, og den andre spilleren faar hele maskinen og styrer sin ridder med
 * port 1 til kampen er over ($080BD8, HVER_EV_DUELL_SLUTT). Da tar den andre med
 * seg ridderen sin (HVER_MEG i sitt eget spill). Ellers, eller om den andre ikke
 * svarer (HVER_AI), styrer datamaskinen her den fjerne ridderen i kampen
 * (+$36 = +$0B = 4). I begge tilfeller skrives plassen ikke over fra nettet foer
 * kampen er slutt.
 */
#include "amiga.h"
#include "m68k.h"
#include <stdio.h>
#include <string.h>

#define RIDDERE    0x8d5b4
#define RSTR       0x84
#define AKTIV      0x8d9ac
#define TELLER     0x8e7a0
#define MAKS       0x8e7c2
#define NAVN_BASE  0xfc000                 /* navnene til de fjerne ridderne (ledig chip) */
#define RUTINE     0xfc080                 /* tegner de andre ridderne i bakgrunnen paa nytt */
#define BAK_PEKER  0x8cde8                 /* long: bakgrunnen */
#define PLAN       0x1f40
#define LOKKE      0x0aac8c                /* toppen av lokka paa kartet */
#define TING       0x18                    /* +$60 peker paa tingene til ridderen */
#define BLOB       (RSTR + TING)

static struct {
    uint8_t  fjern;                         /* bit k: plass k spilles paa en annen maskin */
    uint8_t  har[4];                        /* posisjonen er kjent */
    int16_t  x[4], y[4];
    int8_t   liv[4];
    uint8_t  figur[4];                      /* +$36: hvilken av de fire ridderne (0-3) */
    char     navn[4][16];
    uint8_t  kart;                          /* spillet er paa kartet (en tur har startet) */
    uint8_t  tatt;                          /* bit k: plassen er tatt over, originalen er lagret */
    uint32_t o36[4], o6c[4];                /* datamaskinens ridder, til plassen gis tilbake */
    uint8_t  o0b[4], o49[4];
    uint8_t  orig[4][BLOB];                 /* hele datamaskinens ridder (struktur og ting) */
    int16_t  tx[4], ty[4];                  /* slik de fjerne ridderne er tegnet i bakgrunnen */
    int8_t   tliv[4];
    uint8_t  tfigur[4], tvist;              /* tvist: bit k, plass k er tegnet */
    uint32_t sist_tegnet;                   /* bildet de sist ble tegnet paa nytt */
    uint8_t  kamp;                          /* bit k: plass k er i kamp her */
    uint8_t  blob[4][BLOB];                 /* hele ridderen fra nettet */
    uint8_t  har_blob;                      /* bit k */
    uint8_t  duell_mulig;                   /* bit k: spilleren paa plass k kan naas for en duell */
    uint8_t  duell;                         /* plass + 1 i en duell over nettet, 0 = ingen */
} H;

/* hendelser til frontenden (ikke i lagringen) */
static int hev[8], n_hev;
static void hendelse(int h, int arg) { if (n_hev < 8) hev[n_hev++] = h | arg << 8; }
int hver_hendelse(void)
{
    if (!n_hev) return 0;
    int h = hev[0];
    memmove(hev, hev + 1, sizeof hev[0] * (size_t)--n_hev);
    return h;
}

/* felt i strukturen som hoerer til plassen, ikke til ridderen */
static bool eget_felt(int i)
{
    return i == 0x0b || (i >= 0x36 && i < 0x3a) || (i >= 0x42 && i < 0x46) || i == 0x52 ||
           (i >= 0x60 && i < 0x68) || (i >= 0x6c && i < 0x70) || (i >= 0x7e && i < 0x82);
}

static uint32_t ting_adr(uint32_t r)
{
    uint32_t t = mem_read32(r + 0x60);
    return (t >= 0x80000 && t + TING <= CHIP_SIZE) ? t : 0;
}

/* hele ridderen inn paa plass k (uten feltene som hoerer til plassen) */
static void skriv_blob(int k, const uint8_t *b)
{
    uint32_t r = RIDDERE + (uint32_t)k * RSTR;
    for (int i = 0; i < RSTR; i++)
        if (!eget_felt(i)) mem_write8(r + (uint32_t)i, b[i]);
    uint32_t t = ting_adr(r);
    if (t) for (int i = 0; i < TING; i++) mem_write8(t + (uint32_t)i, b[RSTR + i]);
}

static void les_blob(int k, uint8_t *b)
{
    uint32_t r = RIDDERE + (uint32_t)(k & 3) * RSTR, t = ting_adr(r);
    for (int i = 0; i < BLOB; i++)
        b[i] = i < RSTR ? (uint8_t)mem_read8(r + (uint32_t)i) : t ? (uint8_t)mem_read8(t + (uint32_t)(i - RSTR)) : 0;
}

/* ridder k som heks (struktur og ting), til nettet */
const char *hver_blob(int k)
{
    static char ut[BLOB * 2 + 1];
    static const char *hx = "0123456789abcdef";
    uint8_t b[BLOB];
    les_blob(k, b);
    for (int i = 0; i < BLOB; i++) {
        ut[i * 2] = hx[b[i] >> 4];
        ut[i * 2 + 1] = hx[b[i] & 15];
    }
    ut[BLOB * 2] = 0;
    return ut;
}

static bool fra_heks(const char *text, uint8_t *b)
{
    if (strlen(text) < BLOB * 2) return false;
    for (int i = 0; i < BLOB * 2; i++) {
        char c = text[i];
        int v = c >= '0' && c <= '9' ? c - '0' : c >= 'a' && c <= 'f' ? c - 'a' + 10 : c >= 'A' && c <= 'F' ? c - 'A' + 10 : -1;
        if (v < 0) return false;
        if (i & 1) b[i / 2] |= (uint8_t)v; else b[i / 2] = (uint8_t)(v << 4);
    }
    return true;
}

/* bakgrunnen uten de andre ridderne, fra turen startet (ikke i lagringen: etter
 * lasting tegnes de foerst paa nytt neste tur) */
static uint8_t  kopi[5 * PLAN];
static uint32_t kopi_adr;
static bool     kopi_ok;

static uint32_t rd32(uint32_t a) { return mem_read32(a); }
static void gi_tilbake(void);

void hver_reset(void) { memset(&H, 0, sizeof H); kopi_ok = false; n_hev = 0; }
void hver_state(StateIO *s)
{
    STATE_VAR(s, H);
    if (!s->saving) { kopi_ok = false; n_hev = 0; }
}
bool hver_paa(void) { return H.fjern != 0; }
bool hver_kart(void) { return H.kart != 0; }

/* kommandoer fra frontenden, ved starten av et bilde:
 *   HVER_FJERN  arg = bitmaske med fjerne plasser (0 = av)
 *   HVER_RIDDER text = "plass x y liv figur NAVN" */
void hver_kommando(int k, int arg, const char *text)
{
    switch (k) {
    case HVER_FJERN:
        H.fjern = (uint8_t)(arg & 0x0e);    /* plass 0 er alltid den som spiller her */
        gi_tilbake();
        break;
    case HVER_BLOB: {                       /* arg = plass, text = heks */
        uint8_t b[BLOB];
        if (arg < 1 || arg > 3 || !fra_heks(text, b)) return;
        memcpy(H.blob[arg], b, BLOB);
        H.har_blob |= (uint8_t)(1 << arg);
        break;
    }
    case HVER_MEG: {                        /* ridderen min tilbake fra en duell: inn paa plass 0 */
        uint8_t b[BLOB];
        if (!whd_mog_loaded || !fra_heks(text, b)) return;
        skriv_blob(0, b);
        break;
    }
    case HVER_DUELL:                        /* arg = bitmaske: plassene der spilleren kan naas */
        H.duell_mulig = (uint8_t)(arg & 0x0e);
        break;
    case HVER_AI:                           /* den andre svarte ikke: datamaskinen styrer i kampen */
        if (arg < 1 || arg > 3 || !whd_mog_loaded) return;
        mem_write32(RIDDERE + (uint32_t)arg * RSTR + 0x36, 4);
        mem_write8(RIDDERE + (uint32_t)arg * RSTR + 0x0b, 4);
        if (H.duell == arg + 1) H.duell = 0;
        break;
    case HVER_RIDDER: {
        int p, x, y, liv, figur;
        char navn[16] = "";
        if (sscanf(text, "%d %d %d %d %d %15s", &p, &x, &y, &liv, &figur, navn) < 5) return;
        if (p < 1 || p > 3) return;
        H.har[p] = 1;
        H.x[p] = (int16_t)x;
        H.y[p] = (int16_t)y;
        H.liv[p] = (int8_t)liv;
        H.figur[p] = (uint8_t)(figur & 3);
        for (char *c = navn; *c; c++) if (*c == '_') *c = ' ';
        snprintf(H.navn[p], sizeof H.navn[p], "%s", navn[0] ? navn : "KNIGHT");
        break;
    }
    }
}

/* plasser som ikke lenger er fjerne, faar datamaskinens ridder tilbake (ellers
 * venter spillet paa en spiller som ikke finnes, siden +$36 ikke er 4) */
static void gi_tilbake(void)
{
    for (int k = 1; k < 4; k++) {
        if (!(H.tatt & (1 << k)) || (H.fjern & (1 << k))) continue;
        uint32_t r = RIDDERE + (uint32_t)k * RSTR;
        if (whd_mog_loaded) {
            skriv_blob(k, H.orig[k]);
            mem_write8(r + 0x52, H.orig[k][0x52]);
            mem_write32(r + 0x36, H.o36[k]);
            mem_write32(r + 0x6c, H.o6c[k]);
            mem_write8(r + 0x0b, H.o0b[k]);
            mem_write8(r + 0x49, H.o49[k]);
        }
        H.tatt &= (uint8_t)~(1 << k);
        H.kamp &= (uint8_t)~(1 << k);
        H.har_blob &= (uint8_t)~(1 << k);
        H.har[k] = 0;
    }
}

/* skriver de fjerne ridderne inn i spillet; kalles foer hvert bilde, men bare
 * paa kartet (paa tittelskjermen og under valg av ridder settes ridderne opp) */
void hver_frame(void)
{
    if (!H.fjern || !whd_mog_loaded || !H.kart) return;
    for (int k = 1; k < 4; k++) {
        if (!(H.fjern & (1 << k)) || !H.har[k] || (H.kamp & (1 << k))) continue;
        uint32_t r = RIDDERE + (uint32_t)k * RSTR;
        if (!(H.tatt & (1 << k))) {
            if (mem_read32(r + 0x36) != 4) continue;   /* bare datamaskinens plasser (to kan spille paa en maskin) */
            H.o36[k] = mem_read32(r + 0x36);
            H.o6c[k] = mem_read32(r + 0x6c);
            H.o0b[k] = (uint8_t)mem_read8(r + 0x0b);
            H.o49[k] = (uint8_t)mem_read8(r + 0x49);
            les_blob(k, H.orig[k]);
            H.tatt |= (uint8_t)(1 << k);
        }
        if (H.har_blob & (1 << k)) skriv_blob(k, H.blob[k]);
        mem_write16(r + 0x7e, (uint16_t)H.x[k]);
        mem_write16(r + 0x80, (uint16_t)H.y[k]);
        mem_write8(r + 0x49, (uint8_t)H.liv[k]);
        mem_write32(r + 0x36, H.figur[k]);  /* ikke 4: da ville datamaskinen styrt den */
        mem_write8(r + 0x0b, 4);            /* som datamaskinens: i kamp er +$0B den som styrer (1 port 1, 2 port 2, 4 datamaskinen) */
        /* +$52 > 0: turen hoppes over ($0AAEEC). En doed ridder som ikke er datamaskinens,
         * teller ellers som en doed spiller, og spillet slutter ($0AAF08) */
        mem_write8(r + 0x52, H.liv[k] > 0 ? 0 : 1);
        uint32_t n = NAVN_BASE + (uint32_t)k * 16;
        for (int i = 0; i < 16; i++) mem_write8(n + (uint32_t)i, (uint8_t)H.navn[k][i]);
        mem_write32(r + 0x6c, n);
    }
}

/* ridder k slik den er i spillet her: x, y, liv, figur (til nettet) */
void hver_ridder(int k, int ut[4])
{
    uint32_t r = RIDDERE + (uint32_t)(k & 3) * RSTR;
    ut[0] = (int16_t)mem_read16(r + 0x7e);
    ut[1] = (int16_t)mem_read16(r + 0x80);
    ut[2] = (int8_t)mem_read8(r + 0x49);
    ut[3] = (int)rd32(r + 0x36);
}

/* tittelmenyen: et nytt spill begynner, ingen plasser er tatt over */
static bool hook_tittel(void)
{
    if (H.duell) hendelse(HVER_EV_DUELL_SLUTT, H.duell - 1);
    H.kart = 0;
    H.tatt = 0;
    H.kamp = 0;
    H.duell = 0;
    kopi_ok = false;
    return false;
}

/* plass k er tegnet slik den er naa */
static void merk_tegnet(int k)
{
    H.tx[k] = H.x[k];
    H.ty[k] = H.y[k];
    H.tliv[k] = H.liv[k];
    H.tfigur[k] = H.figur[k];
}

/* turen starter, bakgrunnen har kartet og stedene, men ikke ridderne ennaa */
static bool hook_foer_riddere(void)
{
    uint32_t bak = mem_read32(BAK_PEKER);
    kopi_ok = false;
    H.tvist = 0;
    if (!H.fjern || bak < 0x100 || bak + sizeof kopi > CHIP_SIZE) return false;
    memcpy(kopi, chip + bak, sizeof kopi);
    kopi_adr = bak;
    kopi_ok = true;
    for (int k = 1; k < 4; k++)
        if (H.tatt & (1 << k)) { merk_tegnet(k); H.tvist |= (uint8_t)(1 << k); }
    H.sist_tegnet = M.frame;
    return false;
}

/* rutinen i chip-minnet: ridderne inn i bakgrunnen, tegnemaalet som foer */
static const uint16_t rutine[] = {
    0x48e7, 0xfffe,                         /* movem.l d0-d7/a0-a6,-(a7) */
    0x2f39, 0x0009, 0xe202,                 /* move.l $9e202,-(a7) ... tegnemaalet (fem plan) */
    0x2f39, 0x0009, 0xe206,
    0x2f39, 0x0009, 0xe20a,
    0x2f39, 0x0009, 0xe20e,
    0x2f39, 0x0009, 0xe212,
    0x2039, 0x0008, 0xcde8,                 /* move.l $8cde8,d0 */
    0x4eb9, 0x0008, 0x8f42,                 /* jsr $88f42: tegn i bakgrunnen */
    0x4eb9, 0x000a, 0xab0a,                 /* jsr $aab0a: de andre ridderne */
    0x23df, 0x0009, 0xe212,                 /* move.l (a7)+,$9e212 ... */
    0x23df, 0x0009, 0xe20e,
    0x23df, 0x0009, 0xe20a,
    0x23df, 0x0009, 0xe206,
    0x23df, 0x0009, 0xe202,
    0x4cdf, 0x7fff,                         /* movem.l (a7)+,d0-d7/a0-a6 */
    0x4e75,                                 /* rts */
};

/* toppen av lokka paa kartet: har en fjern ridder flyttet seg, tegnes de paa nytt */
static bool hook_lokke(void)
{
    if ((!H.fjern && !H.tvist) || !kopi_ok || M.frame - H.sist_tegnet < 4) return false;   /* tvist: de som gikk, viskes ut */
    if (mem_read32(BAK_PEKER) != kopi_adr) { kopi_ok = false; return false; }
    bool endret = false;
    for (int k = 1; k < 4; k++) {
        bool vis = (H.tatt >> k) & 1;
        bool var = (H.tvist >> k) & 1;
        if (vis != var || (vis && (H.tx[k] != H.x[k] || H.ty[k] != H.y[k] || H.tliv[k] != H.liv[k] || H.tfigur[k] != H.figur[k])))
            endret = true;
    }
    if (!endret) return false;
    H.tvist = 0;
    for (int k = 1; k < 4; k++)
        if (H.tatt & (1 << k)) { merk_tegnet(k); H.tvist |= (uint8_t)(1 << k); }
    H.sist_tegnet = M.frame;
    memcpy(chip + kopi_adr, kopi, sizeof kopi);
    for (size_t i = 0; i < sizeof rutine / sizeof rutine[0]; i++) mem_write16(RUTINE + (uint32_t)i * 2, rutine[i]);
    uint32_t sp = m68k_get_reg(NULL, M68K_REG_SP) - 4;
    mem_write32(sp, LOKKE);                 /* rts i rutinen kommer tilbake hit, og da er ingenting endret */
    m68k_set_reg(M68K_REG_SP, sp);
    m68k_set_reg(M68K_REG_PC, RUTINE);
    return true;
}

/* turen til en fjern ridder: hopp over den */
static bool hook_turstart(void)
{
    H.kart = 1;
    if (!H.fjern) return false;
    uint32_t a = rd32(AKTIV);
    if (a < RIDDERE || a >= RIDDERE + 4 * RSTR || (a - RIDDERE) % RSTR) return false;
    int k = (int)((a - RIDDERE) / RSTR);
    if (!(H.tatt & (1 << k))) return false;
    mem_write16(TELLER, mem_read16(MAKS));
    m68k_set_reg(M68K_REG_PC, 0x0aae62);
    return true;
}

/* en ridder blir angrepet (a1): er det en fjern ridder, styrer datamaskinen den i kampen */
static bool hook_kamp(void)
{
    if (!H.fjern) return false;
    uint32_t a = m68k_get_reg(NULL, M68K_REG_A1);
    if (a < RIDDERE || a >= RIDDERE + 4 * RSTR || (a - RIDDERE) % RSTR) return false;
    int k = (int)((a - RIDDERE) / RSTR);
    if (!(H.tatt & (1 << k))) return false;
    H.kamp |= (uint8_t)(1 << k);
    /* duell bare naar ridderen din angriper (a0 = plass 0); angriper datamaskinens
     * ridder, blir det ingen kamp (begge er datamaskinens, $080B08) */
    uint32_t a0 = m68k_get_reg(NULL, M68K_REG_A0);
    if (a0 == RIDDERE && mem_read32(a0 + 0x36) != 4 && (H.duell_mulig & (1 << k)) && !H.duell) {
        /* duell: +$36 er figuren (ikke 4), saa spillet gir ridderen port 1 ($080B36) */
        H.duell = (uint8_t)(k + 1);
        hendelse(HVER_EV_DUELL, k);
        return false;
    }
    mem_write32(a + 0x36, 4);
    mem_write8(a + 0x0b, 4);
    return false;
}

/* kampen er over (eller ble ikke noe av) */
static bool hook_kamp_slutt(void)
{
    if (H.duell) {
        int k = H.duell - 1;
        hendelse(HVER_EV_DUELL_SLUTT, k);
        /* plassen skrives ikke over foer den andre har sendt ridderen sin paa nytt */
        H.har[k] = 0;
        H.har_blob &= (uint8_t)~(1 << k);
        H.duell = 0;
    }
    H.kamp = 0;
    return false;
}

void hver_register_hooks(void)
{
    hooks_register_patch(0x0aac14, hook_turstart, "turstart (hver for seg)");
    hooks_register_patch(0x08188c, hook_tittel, "tittelmeny (hver for seg)");
    hooks_register_patch(0x0aac54, hook_foer_riddere, "kartet foer ridderne (hver for seg)");
    hooks_register_patch(LOKKE, hook_lokke, "lokka paa kartet (hver for seg)");
    hooks_register_patch(0x080ab8, hook_kamp, "ridder mot ridder (hver for seg)");
    hooks_register_patch(0x080bd8, hook_kamp_slutt, "ridder mot ridder slutt (hver for seg)");
}
