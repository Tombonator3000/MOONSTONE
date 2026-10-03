/*
 * meny.c - nettspill i spillets egen tittelmeny.
 *
 * Tittelmenyen ($8188C) er en lenket liste med tekster som skriv_tekst tegner
 * (tegn_tittelmeny, $81A1A), en tabell med y for pilen, og en lokke ($81906)
 * som leser joysticken. Vi legger til en linje, "Options", og bruker den
 * samme motoren til egne sider (Host Game, Join Game ...): tegn_tittelmeny
 * faar en annen liste og en annen pil-tabell, og vi styrer valgene i C.
 * Slik tegnes nettspillmenyen med spillets font, pil og bakgrunn.
 *
 * Alt som endrer spillets minne skjer enten i hooks (naar CPU-en kommer til
 * en adresse) eller i kommandoer fra frontenden som brukes ved starten av et
 * bilde (meny_command).
 *
 * Linjen i tittelmenyen heter "Options" og gaar til en side med Online Game og
 * oppsettet av kontrollene (Keyboard, Gamepad). Selve tastene og knappene leses
 * av frontenden; den sender navnene paa dem (MENY_CMD_CONTROLS), og naar en
 * linje velges, kommer MENY_EV_BIND, og frontenden venter paa neste tast.
 *
 * I nettspill sender verten kommandoene med bildet, saa alle maskinene gjor
 * det samme. Hendelser (meny_take_event) gaar andre veien, til frontenden, og
 * endrer ingenting i spillet.
 *
 * Adresser (se disasm/symbols.txt):
 *   $81906 lokka: jsr les_joysticker     $8190E beq lokka (ingenting trykket)
 *   $81916 fire er trykket               $81942 tegn menyen paa nytt, tilbake til lokka
 *   $81968 tittelmeny_joystick           $819A8, $819B2 siste valg (3)
 *   $81A40 peker til pil-tabellen        $81ACC peker til tekstlisten
 *   $8F060 tekstlisten                   $8F2D2 valgt linje
 *   $8CDFC antall spillere               $8F2DC verdi fra $8F058 per antall spillere
 */
#include "amiga.h"
#include "m68k.h"
#include <string.h>
#include <stdio.h>

#define MENU_BASE    0xf8000
#define TITLE_ARROWS 0xf8000                /* 5 ord */
#define TITLE_NODE   0xf8010                /* "Online Game" i tittelmenyen */
#define TITLE_TEXT   0xf8020
#define PAGE_NODES   0xf8100                /* siden: 6 linjer a 14 byte */
#define PAGE_ARROWS  0xf8180
#define PAGE_TEXTS   0xf8200                /* 6 tekster a 48 byte */
#define TEXT_SIZE    48

#define LIST_HEAD    0x8f060
#define VALG         0x8f2d2
#define PLAYERS      0x8cdfc
#define JOY_PORT2    0x8d9a2
#define FONT_PTR     0x8ce94                /* +$A: fonten skriv_tekst bruker */
#define CHAR_TABLE   0x96210

/* sidene har seks linjer (fonten er 19 piksler hoy, logoen slutter paa y 64) */
#define ROWS 6
static const uint16_t row_y[ROWS] = { 0x50, 0x64, 0x78, 0x8c, 0xa0, 0xb4 };

enum { PAGE_TITLE, PAGE_ONLINE, PAGE_HOST, PAGE_JOIN, PAGE_MESSAGE, PAGE_OPTIONS, PAGE_KEYS, PAGE_PAD };
#define CTRL_N    8                        /* navnene paa tastene: 4 for tastaturet, 4 for spillkontrolleren */
#define CTRL_SIZE 16
enum { SESSION_NONE, SESSION_HOST, SESSION_GUEST };

/* alt som paavirker spillet, lagres i tilstanden */
static struct {
    uint8_t enabled;                        /* menyen er lappet inn i mog */
    uint8_t page;
    uint8_t redraw;                         /* tegn siden paa nytt neste gang lokka gaar */
    uint8_t wait_release;                   /* vent til fire slippes */
    uint8_t session;
    uint8_t players;                        /* i rommet, med verten */
    uint8_t knights;                        /* riddere rommet trenger: hoeyeste spillernummer + 1 (tilskuere teller ikke) */
    uint8_t public_room;
    uint8_t n_rooms;                        /* aapne rom (Join Game) */
    uint8_t rooms_known;                    /* listen er hentet (eller feilet) */
    uint8_t select;                         /* velg denne linjen ved neste tegning (0 = ingen) */
    uint8_t pick;                           /* klikket rad + 1, ogsaa i tittelmenyen (0 = ingen) */
    uint8_t pick_fire;                      /* gi spillet fire en gang naar menyen er tegnet */
    uint8_t spill;                          /* 0 = hver for seg (hver.c), 1 = tur for tur */
    uint8_t msg_title;                      /* Back paa meldingen gaar til tittelmenyen */
    uint8_t joy_prev;                       /* port 2 forrige bilde (meny_frame) */
    uint8_t fire_seen;                      /* fire trykket mens lokka ikke leste joysticken */
    uint32_t fire_frame;                    /* bildet det kom i */
    uint8_t dir_seen;                       /* JOY_UP eller JOY_DOWN, trykket mens menyen ble tegnet */
    uint32_t dir_frame;
    uint32_t pick_frame;                    /* bildet klikket kom i (M.frame) */
    uint8_t n_names;
    char    room[8];
    char    myname[TEXT_SIZE];              /* navnet til den som spiller her (Online Game) */
    char    names[4][TEXT_SIZE];            /* "1 Tom", i spillerrekkefolge */
    char    rooms[3][TEXT_SIZE];            /* navnet paa verten */
    char    room_counts[3][12];             /* "1 of 4" */
    char    message[2][TEXT_SIZE];
    char    rooms_error[TEXT_SIZE];
    char    ctrl[CTRL_N][CTRL_SIZE];        /* "Ctrl", "Arrows", ... (MENY_CMD_CONTROLS) */
} M2;

bool meny_online;                           /* frontenden kan nettspill (nettsiden) */
bool meny_title_seen;                       /* tittelmenyen er naadd siden mog ble lastet (nettsiden spoler dit) */
static bool in_menu;                        /* fra tittelmenyen starter til spillet forlater den */

/* ---------------------------------------------------------------- hendelser */
static int events[8], n_events;

static void emit(int ev, int arg)
{
    if (n_events < 8) events[n_events++] = ev | arg << 8;
}

int meny_take_event(void)
{
    if (!n_events) return 0;
    int e = events[0];
    memmove(events, events + 1, sizeof events[0] * (size_t)--n_events);
    return e;
}

/* ---------------------------------------------------------------- tekst */
static void wr16(uint32_t a, uint16_t v) { chip[a] = (uint8_t)(v >> 8); chip[a + 1] = (uint8_t)v; }
static void wr32(uint32_t a, uint32_t v) { wr16(a, (uint16_t)(v >> 16)); wr16(a + 2, (uint16_t)v); }
static uint32_t rd32(uint32_t a) { return (uint32_t)chip[a] << 24 | chip[a + 1] << 16 | chip[a + 2] << 8 | chip[a + 3]; }
static uint16_t rd16(uint32_t a) { return (uint16_t)(chip[a] << 8 | chip[a + 1]); }

/* bredden paa et tegn i fonten som ligger i minnet, eller -1 hvis fonten mangler det */
static int glyph_width(int c)
{
    if (c < 32 || c > 126) return -1;
    int g = chip[CHAR_TABLE + c - 32];
    if (g == 69 && c != ' ') return -1;    /* ubrukte tegn peker paa bilde 69 */
    uint32_t f = rd32(FONT_PTR + 0xa);      /* ligger i ExpMem ($200000-) */
    if (f < 0x1000 || g >= (int)(uint16_t)mem_read16(f)) return -1;
    return (uint16_t)mem_read16(f + 10 + 10 * (uint32_t)g + 4);
}

/* kopierer bare tegn fonten har, og stopper foer teksten blir bredere enn
 * maxw piksler. Hele linjer holdes under 250 (skriv_tekst gir bredden
 * tilbake i D0, se patch.c). */
static void fit_width(char *dst, const char *src, int maxw)
{
    int w = 0, n = 0;
    for (; *src && n < TEXT_SIZE - 1; src++) {
        int gw = glyph_width((unsigned char)*src);
        if (gw < 0) continue;
        if (w + gw > maxw) break;
        w += gw;
        dst[n++] = *src;
    }
    while (n && dst[n - 1] == ' ') n--;
    dst[n] = 0;
}

static void fit_text(char *dst, const char *src) { fit_width(dst, src, 250); }

static int text_width(const char *t)
{
    int w = 0;
    for (; *t; t++) { int gw = glyph_width((unsigned char)*t); if (gw > 0) w += gw; }
    return w;
}

/* Linjer man kan velge, holdes under 158 piksler som i originalmenyen, ellers
 * gaar teksten inn under pilen (x 50). Rom: "Tom  1 of 4", navnet kuttes. */
static void room_line(char *dst, int i)
{
    char name[TEXT_SIZE];
    const char *count = M2.room_counts[i];
    if (!count[0]) {                        /* en invitasjon: "Room ABC123", ellers bare koden */
        const char *t = M2.rooms[i], *sp = strchr(t, ' ');
        fit_width(dst, text_width(t) > 158 && sp ? sp + 1 : t, 158);
        return;
    }
    fit_width(name, M2.rooms[i], 158 - text_width(count) - 2 * text_width(" "));
    snprintf(dst, TEXT_SIZE, "%s  %s", name, count);
}

/* "Fire  Ctrl" paa sidene med kontroller. Pilen staar til venstre for linjer
 * opp til ca 196 piksler, saa her tillates 190. Faar ikke verdien plass med to
 * mellomrom, brukes ett ("Inventory Start"), og saa kuttes den. En verdi som
 * begynner med '*' vises alene paa linjen ("Press a Key"). */
static void label_value(char *dst, const char *label, const char *value)
{
    char v[TEXT_SIZE];
    if (value[0] == '*') { fit_width(dst, value + 1, 190); return; }
    int rest = 190 - text_width(label);
    const char *sep = text_width(value) <= rest - 2 * text_width(" ") ? "  " : " ";
    fit_width(v, value, rest - text_width(sep));
    snprintf(dst, TEXT_SIZE, "%s%s%s", label, sep, v);
}

/* et navn som maa kuttes, kuttes ved siste mellomrom ("3 Ola Nordmann" -> "3 Ola") */
static void fit_name(char *dst, const char *src, int maxw)
{
    char all[TEXT_SIZE];
    fit_width(all, src, 10000);
    fit_width(dst, src, maxw);
    if (strcmp(dst, all) && all[strlen(dst)] != ' ') {
        char *sp = strrchr(dst, ' ');
        if (sp && sp > strchr(dst, ' ')) *sp = 0;   /* behold nummeret og minst ett ord */
    }
}

/* to navn paa en linje: "1 Tom   2 Kari" */
static void name_pair(char *dst, int a, int b)
{
    char x[TEXT_SIZE], y[TEXT_SIZE];
    fit_name(x, a < M2.n_names ? M2.names[a] : "", 112);
    fit_name(y, b < M2.n_names ? M2.names[b] : "", 112);
    snprintf(dst, TEXT_SIZE, "%s%s%s", x, y[0] ? "   " : "", y);
}

/* ---------------------------------------------------------------- sidene */
typedef struct { const char *text; bool selectable; } Row;

static void page_rows(Row r[ROWS])
{
    static char buf[ROWS][TEXT_SIZE];
    for (int i = 0; i < ROWS; i++) { r[i].text = ""; r[i].selectable = false; }
    switch (M2.page) {
    case PAGE_ONLINE: {
        r[0].text = "Online Game";
        r[1] = (Row){ "Host Game", true };
        r[2] = (Row){ "Join Game", true };
        char name[TEXT_SIZE];
        fit_name(name, M2.myname, 158 - text_width("Name  "));
        if (name[0]) snprintf(buf[3], TEXT_SIZE, "Name  %s", name);
        else snprintf(buf[3], TEXT_SIZE, "Choose Name");
        r[3] = (Row){ buf[3], true };
        r[4] = (Row){ M2.spill ? "Mode  Turns" : "Mode  Separate", true };
        r[5] = (Row){ "Back", true };
        break;
    }
    case PAGE_HOST:
        snprintf(buf[0], TEXT_SIZE, "Room %s", M2.room);
        r[0].text = buf[0];
        if (!M2.n_names) {
            snprintf(buf[1], TEXT_SIZE, "%d of 4 Players", M2.players ? M2.players : 1);
            r[1].text = buf[1];
        } else {
            name_pair(buf[1], 0, 1);
            r[1].text = buf[1];
            if (M2.n_names > 2) { name_pair(buf[2], 2, 3); r[2].text = buf[2]; }
            else if (M2.n_names == 1) r[2].text = "Waiting for Players";
        }
        r[3] = (Row){ "Copy Link", true };
        r[4] = (Row){ M2.public_room ? "Public  On" : "Public  Off", true };
        r[5] = (Row){ "Back", true };
        break;
    case PAGE_JOIN:
        r[0].text = "Join Game";
        if (!M2.rooms_known) r[1].text = "Looking for Rooms";
        else if (M2.rooms_error[0]) r[1].text = M2.rooms_error;
        else if (!M2.n_rooms) r[1].text = "No Open Rooms";
        for (int i = 0; i < M2.n_rooms && i < 3; i++) {
            room_line(buf[1 + i], i);
            r[1 + i] = (Row){ buf[1 + i], true };
        }
        r[4] = (Row){ "Enter Code", true };
        r[5] = (Row){ "Back", true };
        break;
    case PAGE_MESSAGE:
        r[0].text = "Online Game";
        r[1].text = M2.message[0];
        r[2].text = M2.message[1];
        r[3] = (Row){ "Back", true };
        break;
    case PAGE_OPTIONS:
        r[0].text = "Options";
        r[1] = (Row){ "Online Game", true };
        r[2] = (Row){ "Keyboard", true };
        r[3] = (Row){ "Gamepad", true };
        r[4] = (Row){ "Default Controls", true };
        r[5] = (Row){ "Back", true };
        break;
    case PAGE_KEYS:
    case PAGE_PAD: {
        /* fire og bevegelse for spiller 1 og 2, eller knappene paa spillkontrolleren */
        static const char *const navn[2][4] = {
            { "Fire", "Move", "Fire 2", "Move 2" },
            { "Fire", "Inventory", "Pass", "Escape" },     /* Pass: E, avslutter turen */
        };
        int s = M2.page == PAGE_PAD;
        r[0].text = s ? "Gamepad" : "Keyboard";
        for (int i = 0; i < 4; i++) {
            label_value(buf[1 + i], navn[s][i], M2.ctrl[s * 4 + i]);
            r[1 + i] = (Row){ buf[1 + i], true };
        }
        r[5] = (Row){ "Back", true };
        break;
    }
    }
}

/* skriver siden inn i minnet og peker tegn_tittelmeny paa den */
static void build_page(void)
{
    if (!M2.enabled) return;
    if (M2.page == PAGE_TITLE) {
        wr32(0x81acc, LIST_HEAD);
        wr32(0x81a40, TITLE_ARROWS);
        return;
    }
    Row r[ROWS];
    page_rows(r);
    uint32_t prev = 0;
    for (int i = 0; i < ROWS; i++) {
        uint32_t node = PAGE_NODES + (uint32_t)i * 14, text = PAGE_TEXTS + (uint32_t)i * TEXT_SIZE;
        char t[TEXT_SIZE];
        fit_text(t, r[i].text);
        memset(chip + text, 0, TEXT_SIZE);
        memcpy(chip + text, t, strlen(t));
        wr32(node, text);
        wr16(node + 4, 0);                  /* x: sentrert */
        wr16(node + 6, row_y[i]);
        wr16(node + 8, 3);                  /* sentrert, og bakgrunnen settes tilbake */
        wr32(node + 10, 0);
        if (prev) wr32(prev + 10, node);
        prev = node;
        wr16(PAGE_ARROWS + (uint32_t)i * 2, (uint16_t)(row_y[i] + (row_y[i] <= 0x6c ? 2 : -2)));
    }
    wr32(0x81acc, PAGE_NODES);
    wr32(0x81a40, PAGE_ARROWS);
    /* valget maa staa paa en linje som kan velges */
    int v = rd16(VALG);
    if (v >= ROWS || !r[v].selectable) {
        for (v = 0; v < ROWS && !r[v].selectable; v++) ;
        wr16(VALG, (uint16_t)(v < ROWS ? v : 0));
    }
}

static void show_page(int page)
{
    M2.page = (uint8_t)page;
    wr16(VALG, page == PAGE_TITLE ? 4 : 0);
    build_page();
}

/* ---------------------------------------------------------------- lapper i mog */
bool meny_mog_ready(void)
{
    M2.enabled = meny_online;
    meny_title_seen = false;
    M2.page = PAGE_TITLE;
    M2.redraw = M2.wait_release = 0;
    if (!M2.enabled) return false;
    /* Practice og Select Knight litt opp, saa en femte linje faar plass */
    wr16(0x8f082, 0x88);
    wr16(0x8f090, 0x9c);
    /* ny linje etter Select Knight: "Options" (Online Game og kontrollene) */
    memcpy(chip + TITLE_TEXT, "Options", 8);
    wr32(TITLE_NODE, TITLE_TEXT);
    wr16(TITLE_NODE + 4, 0);
    wr16(TITLE_NODE + 6, 0xb0);
    wr16(TITLE_NODE + 8, 3);
    wr32(TITLE_NODE + 10, rd32(0x8f094));   /* det Select Knight pekte paa ("1"-linjen) */
    wr32(0x8f094, TITLE_NODE);
    /* pilen: Players, Gore, Practice, Select Knight, Options */
    static const uint16_t arrows[5] = { 0x55, 0x6e, 0x86, 0x9a, 0xae };
    for (int i = 0; i < 5; i++) wr16(TITLE_ARROWS + (uint32_t)i * 2, arrows[i]);
    wr32(0x81a40, TITLE_ARROWS);
    /* fem valg (0-4) i stedet for fire */
    wr16(0x819a8, 4);
    wr16(0x819b2, 4);
    return true;
}

/* ---------------------------------------------------------------- hooks */
/* hooks kjores bare naar mog er lastet (hooks.c), saa tilstanden er nok */
static bool active(void) { return M2.enabled; }

static void goto_redraw(void)
{
    M2.wait_release = 1;
    M2.fire_seen = 0;                       /* trykket som ga valget, er brukt */
    m68k_set_reg(M68K_REG_PC, 0x81942);    /* bsr tegn_tittelmeny; bra lokka */
}

/* lokka: en kommando har endret siden. Siden bygges her, ikke i kommandoen,
 * saa vi aldri skriver om listen mens skriv_tekst holder paa med den. */
static bool hook_loop(void)
{
    if (!active()) return false;
    meny_title_seen = true;
    in_menu = true;
    if (!M2.redraw) return false;
    M2.redraw = 0;
    if (M2.select) { wr16(VALG, M2.select); M2.select = 0; }
    if (M2.pick) { wr16(VALG, (uint16_t)(M2.pick - 1)); M2.pick = 0; }
    build_page();
    m68k_set_reg(M68K_REG_PC, 0x81942);
    return true;
}

/* beq.b lokka (etter tst.w d1): husk naar fire er sluppet. Ikke paa $8190C:
 * det er returadressen fra les_joysticker, som er i C, og der kalles ikke
 * hooks (se hooks.c). */
static bool hook_input(void)
{
    if (!active()) return false;
    uint32_t d1 = m68k_get_reg(NULL, M68K_REG_D1);
    if (d1 & 0x0c) M2.dir_seen = 0;        /* spillet ser retningen selv */
    if (d1 & 0x10) {
        /* et nytt trykk etter valget (fire ble sluppet og trykket igjen mens menyen
         * ble tegnet), ikke det samme som fortsatt holdes */
        if (M2.wait_release && M2.fire_seen) M2.wait_release = 0;
        M2.fire_seen = 0;                   /* spillet ser trykket selv */
    } else M2.wait_release = 0;
    /* Et klikk eller Enter: fire en gang, etter at menyen er tegnet paa nytt. Lokka leser
     * joysticken hele tiden, men aa tegne menyen tar flere bilder, saa et kort fire fra
     * frontenden kunne komme mens den tegnet. Her ser spillet det som fra joysticken. */
    if (M2.pick_fire && !M2.redraw) {
        M2.pick_fire = 0;
        if (M.frame - M2.pick_frame > 25) return false;     /* menyen var ikke framme */
        m68k_set_reg(M68K_REG_D1, d1 | 0x10);
        m68k_set_reg(M68K_REG_PC, 0x81910);                 /* forbi beq.b lokka: btst #4,d1 */
        return true;
    }
    /* et kort opp eller ned mens menyen ble tegnet: pilen flyttes naa. Lokka og
     * tittelmeny_joystick ($81968, hook_joystick paa sidene) leser $8D9A2, saa den
     * settes som les_joysticker ville gjort (opp = 8, ned = 4). Retningen gis foer
     * et fire som ogsaa venter (ned og saa fire). */
    if (M2.dir_seen && M.frame - M2.dir_frame > 30) M2.dir_seen = 0;
    if (M2.dir_seen && !M2.redraw && !(d1 & 0x1f)) {
        uint16_t b = (M2.dir_seen & JOY_UP) ? 8 : 4;
        M2.dir_seen = 0;
        wr16(JOY_PORT2, b);
        m68k_set_reg(M68K_REG_D1, (d1 & 0xffff0000u) | b);
        m68k_set_reg(M68K_REG_PC, 0x81910);                 /* ikke fire: til tittelmeny_joystick */
        return true;
    }
    /* et kort fire mens menyen ble tegnet (meny_frame): gis naa, som fra joysticken.
     * Holdes en retning, flyttes pilen foerst (ned og saa fire), og et trykk som er
     * mer enn et halvt sekund gammelt, glemmes. */
    if (M2.fire_seen && M.frame - M2.fire_frame > 30) M2.fire_seen = 0;
    if (M2.fire_seen && !M2.redraw && !(d1 & 0x0f)) {
        M2.fire_seen = 0;
        m68k_set_reg(M68K_REG_D1, d1 | 0x10);
        m68k_set_reg(M68K_REG_PC, 0x81910);
        return true;
    }
    return false;
}

/* foer hvert bilde. Etter et flytt bruker spillet ca 15 bilder paa aa tegne
 * menyen, og lokka leser ikke joysticken saa lenge. Et fire (eller opp og ned)
 * som trykkes og slippes i den tiden, ville blitt borte; det huskes her og gis i
 * hook_input. Korte trykk paa styrekorset paa mobil er typisk slik.
 * Bare nye trykk teller, saa et fire som holdes inne etter et valg, ikke gir
 * et valg til. Spillet ser joysticken et bilde senere enn IN, saa wait_release
 * slippes fortsatt bare i hook_input. Inndataene er de samme paa alle
 * maskinene i et nettspill. */
void meny_frame(void)
{
    if (!M2.enabled) return;
    uint8_t j = IN.joy[1], ny = (uint8_t)(j & ~M2.joy_prev);
    if (ny & JOY_FIRE) { M2.fire_seen = 1; M2.fire_frame = M.frame; }
    if (ny & (JOY_UP | JOY_DOWN)) { M2.dir_seen = ny & (JOY_UP | JOY_DOWN); M2.dir_frame = M.frame; }
    M2.joy_prev = j;
}

static void set_players(int n)
{
    if (n < 1) n = 1;
    if (n > 4) n = 4;
    wr16(PLAYERS, (uint16_t)n);
    wr16(0x8f2dc, rd16(0x8f058 + (uint32_t)(n - 1) * 2));    /* som endre_antall_spillere */
}

/* fire er trykket */
static bool hook_fire(void)
{
    if (!active()) return false;
    int v = rd16(VALG);
    if (M2.wait_release) { m68k_set_reg(M68K_REG_PC, 0x81906); return true; }
    switch (M2.page) {
    case PAGE_TITLE:
        if (v != 4) return false;          /* originalen: Practice, Select Knight osv. */
        show_page(PAGE_OPTIONS);
        break;
    case PAGE_OPTIONS:
        if (v == 1) show_page(M2.session == SESSION_HOST ? PAGE_HOST : PAGE_ONLINE);
        else if (v == 2) show_page(PAGE_KEYS);
        else if (v == 3) show_page(PAGE_PAD);
        else if (v == 4) emit(MENY_EV_BIND, 0);         /* standardoppsettet */
        else show_page(PAGE_TITLE);
        break;
    case PAGE_KEYS:
    case PAGE_PAD:
        if (v >= 1 && v <= 4) emit(MENY_EV_BIND, (M2.page == PAGE_PAD ? 4 : 0) + v);   /* 1-4 tastatur, 5-8 spillkontroller */
        else show_page(PAGE_OPTIONS);
        break;
    case PAGE_ONLINE:
        if (v == 1) {
            snprintf(M2.message[0], TEXT_SIZE, "Creating Room...");
            M2.message[1][0] = 0;
            M2.msg_title = 0;
            show_page(PAGE_MESSAGE);
            emit(MENY_EV_HOST, M2.spill);
        } else if (v == 2) {
            M2.rooms_known = 0; M2.n_rooms = 0; M2.rooms_error[0] = 0;
            show_page(PAGE_JOIN);
            emit(MENY_EV_JOIN_PAGE, 0);
        } else if (v == 3) emit(MENY_EV_NAME, 0);
        else if (v == 4) { M2.spill ^= 1; build_page(); emit(MENY_EV_SPILL, M2.spill); }
        else show_page(PAGE_OPTIONS);
        break;
    case PAGE_HOST:
        if (v == 3) emit(MENY_EV_COPY, 0);
        else if (v == 4) emit(MENY_EV_PUBLIC, !M2.public_room);
        else if (v == 5) {
            if (M2.spill && M2.knights >= 2) set_players(M2.knights);   /* tur for tur: en ridder til hver spiller i rommet */
            show_page(PAGE_TITLE);
            emit(MENY_EV_BACK, 0);
        }
        break;
    case PAGE_JOIN:
        if (v >= 1 && v <= 3) emit(MENY_EV_JOIN_ROOM, v - 1);
        else if (v == 4) emit(MENY_EV_ENTER_CODE, 0);
        else if (v == 5) { show_page(PAGE_ONLINE); emit(MENY_EV_LEAVE_JOIN, 0); }
        break;
    case PAGE_MESSAGE:
        show_page(M2.msg_title ? PAGE_TITLE : M2.session == SESSION_HOST ? PAGE_HOST : PAGE_ONLINE);
        break;
    }
    goto_redraw();
    return true;
}

/* opp/ned paa sidene (tittelmenyen selv bruker originalen) */
static bool hook_joystick(void)
{
    if (!active() || M2.page == PAGE_TITLE) return false;
    Row r[ROWS];
    page_rows(r);
    int v = rd16(VALG), j = rd16(JOY_PORT2), nv = v;
    if (j & 8) { for (int i = v - 1; i >= 0; i--) if (r[i].selectable) { nv = i; break; } }
    else if (j & 4) { for (int i = v + 1; i < ROWS; i++) if (r[i].selectable) { nv = i; break; } }
    wr16(VALG, (uint16_t)nv);
    m68k_set_reg(M68K_REG_D0, nv != v);
    hook_return();
    return true;
}

/* tittelmenyen starter: alltid paa forsiden */
static bool hook_title(void)
{
    if (!active()) return false;
    M2.page = PAGE_TITLE;
    M2.redraw = 0;
    M2.pick = M2.pick_fire = 0;
    M2.fire_seen = M2.dir_seen = 0;         /* trykk fra spillet foer menyen */
    in_menu = true;
    build_page();
    return false;
}

/* Practice ($8194A) og Select Knight ($81952): spillet forlater tittelmenyen */
static bool hook_leave(void)
{
    in_menu = false;
    return false;
}

/* Select Knight i et rom tur for tur: alle som spiller i rommet, skal faa en ridder.
 * Kom noen inn etter at verten gikk tilbake til tittelmenyen (Back setter antallet),
 * staar Players fortsatt paa det gamle, og den nye ville bare sett paa. Antallet
 * settes opp (aldri ned) til M2.knights foer $81958 leser det. Tilskuere og to som
 * deler et spillernummer, gir ingen ekstra ridder. */
static bool hook_leave_knight(void)
{
    in_menu = false;
    if (active() && M2.spill && M2.session == SESSION_HOST && M2.knights > rd16(PLAYERS)) set_players(M2.knights);
    return false;
}

void meny_register_hooks(void)
{
    hooks_register_patch(0x8188c, hook_title, "tittelmeny (nettspill)");
    hooks_register_patch(0x81906, hook_loop, "tittelmeny lokke (nettspill)");
    hooks_register_patch(0x8190e, hook_input, "tittelmeny fire sluppet");
    hooks_register_patch(0x81916, hook_fire, "tittelmeny fire (nettspill)");
    hooks_register_patch(0x81968, hook_joystick, "tittelmeny joystick (nettspill)");
    hooks_register_patch(0x8194a, hook_leave, "tittelmeny forlates (Practice)");
    hooks_register_patch(0x81952, hook_leave_knight, "tittelmeny forlates (Select Knight)");
}

/* ---------------------------------------------------------------- kommandoer */
/* Kommandoene kan komme foer mog er lastet (verten lager rommet fra
 * startsiden); da husker vi bare rommet til menyen finnes. */
void meny_command(int cmd, int arg, const char *text)
{
    text = text ? text : "";
    switch (cmd) {
    case MENY_CMD_HOSTING:
        M2.session = SESSION_HOST;
        snprintf(M2.room, sizeof M2.room, "%s", text);
        if (M2.players < 1) M2.players = 1;
        if (M2.page == PAGE_MESSAGE || M2.page == PAGE_ONLINE) {
            M2.page = PAGE_HOST;
            M2.select = 3;                  /* Copy Link */
        }
        break;
    case MENY_CMD_PLAYERS:
        M2.players = (uint8_t)(arg < 1 ? 1 : arg > 4 ? 4 : arg);
        break;
    case MENY_CMD_KNIGHTS:                  /* hoeyeste spillernummer + 1 i rommet; vises ikke */
        M2.knights = (uint8_t)(arg < 0 ? 0 : arg > 4 ? 4 : arg);
        return;
    case MENY_CMD_PUBLIC:
        M2.public_room = arg != 0;
        break;
    case MENY_CMD_ROOMS: {
        int before = M2.n_rooms;
        M2.rooms_known = 1;
        M2.n_rooms = 0;
        M2.rooms_error[0] = 0;
        if (arg < 0) { snprintf(M2.rooms_error, TEXT_SIZE, "%s", text); break; }
        const char *p = text;
        while (*p && M2.n_rooms < 3) {
            const char *nl = strchr(p, '\n');
            size_t n = nl ? (size_t)(nl - p) : strlen(p);
            char line[TEXT_SIZE];
            if (n >= sizeof line) n = sizeof line - 1;
            memcpy(line, p, n);
            line[n] = 0;
            /* "navn<tab>1 of 4" */
            char *tab = strchr(line, '\t');
            if (tab) *tab = 0;
            snprintf(M2.rooms[M2.n_rooms], TEXT_SIZE, "%s", line);
            snprintf(M2.room_counts[M2.n_rooms], sizeof M2.room_counts[0], "%s", tab ? tab + 1 : "");
            M2.n_rooms++;
            p = nl ? nl + 1 : p + strlen(p);
        }
        /* siden aapnet uten rom, saa pilen sto paa Enter Code: flytt den til det
         * forste rommet naar det kommer */
        if (M2.page == PAGE_JOIN && !before && M2.n_rooms && rd16(VALG) == 4) M2.select = 1;
        break;
    }
    case MENY_CMD_MESSAGE: {
        const char *nl = strchr(text, '\n');
        size_t n = nl ? (size_t)(nl - text) : strlen(text);
        if (n >= TEXT_SIZE) n = TEXT_SIZE - 1;
        memcpy(M2.message[0], text, n);
        M2.message[0][n] = 0;
        snprintf(M2.message[1], TEXT_SIZE, "%s", nl ? nl + 1 : "");
        M2.msg_title = arg == 1;            /* med i et rom hver for seg: rett til Select Knight */
        if (M2.page != PAGE_TITLE) M2.page = PAGE_MESSAGE;
        break;
    }
    case MENY_CMD_NAMES: {
        M2.n_names = 0;
        const char *p = text;
        while (*p && M2.n_names < 4) {
            const char *nl = strchr(p, '\n');
            size_t n = nl ? (size_t)(nl - p) : strlen(p);
            if (n >= TEXT_SIZE) n = TEXT_SIZE - 1;
            memcpy(M2.names[M2.n_names], p, n);
            M2.names[M2.n_names++][n] = 0;
            p = nl ? nl + 1 : p + strlen(p);
        }
        break;
    }
    case MENY_CMD_MYNAME:
        snprintf(M2.myname, TEXT_SIZE, "%s", text);
        break;
    case MENY_CMD_PAGE:                     /* f.eks. Join Game naar siden er aapnet med en invitasjon */
        if (!M2.enabled || (arg != PAGE_JOIN && arg != PAGE_ONLINE)) return;
        M2.page = (uint8_t)arg;
        if (arg == PAGE_JOIN) { M2.rooms_known = 0; M2.n_rooms = 0; M2.rooms_error[0] = 0; }
        M2.select = 1;
        break;
    case MENY_CMD_SPILL:                    /* hver for seg (0) eller tur for tur (1), lagret paa nettsiden */
        M2.spill = (uint8_t)(arg & 1);
        break;
    case MENY_CMD_CONTROLS: {               /* navnene paa tastene, en linje hver (se PAGE_KEYS/PAGE_PAD) */
        const char *p = text;
        for (int i = 0; i < CTRL_N; i++) {
            const char *nl = strchr(p, '\n');
            size_t n = nl ? (size_t)(nl - p) : strlen(p);
            if (n >= CTRL_SIZE) n = CTRL_SIZE - 1;
            memcpy(M2.ctrl[i], p, n);
            M2.ctrl[i][n] = 0;
            p = nl ? nl + 1 : p + strlen(p);
        }
        if (M2.page != PAGE_KEYS && M2.page != PAGE_PAD) return;   /* vises ikke naa */
        break;
    }
    case MENY_CMD_SELECT:                   /* klikk paa en rad (arg), eller Enter (-1): pilen dit og fire */
        if (!M2.enabled || arg < -1 || arg >= ROWS) return;
        if (arg >= 0) { M2.pick = (uint8_t)(arg + 1); M2.redraw = 1; }
        M2.pick_fire = 1;
        M2.pick_frame = M.frame;
        return;
    case MENY_CMD_SESSION_END:
        M2.session = SESSION_NONE;
        M2.n_names = 0;
        M2.players = 0;
        M2.knights = 0;
        M2.public_room = 0;
        if (M2.page == PAGE_HOST) M2.page = PAGE_ONLINE;
        break;
    default:
        return;
    }
    if (M2.enabled && M2.page != PAGE_TITLE) M2.redraw = 1;
}

/* ny maskin (amiga_reset): ingen side, intet rom. Frontenden sender navnet paa nytt. */
void meny_reset(void)
{
    memset(&M2, 0, sizeof M2);
    meny_title_seen = false;
    in_menu = false;
    n_events = 0;
}

/* Er tittelmenyen (eller en nettspillside) paa skjermen? Ogsaa mens den tegnes paa
 * nytt, som tar opp mot et sekund. Bare for frontenden; lagres ikke. */
bool meny_in_menu(void)
{
    return M2.enabled && in_menu;
}

/* Siden som vises (PAGE_*), eller -1 utenfor menyen. Bare for frontenden. */
int meny_side(void)
{
    return meny_in_menu() ? M2.page : -1;
}

/* Raden paa linje y (spillets skjerm, 0 = overst) som kan velges med et klikk.
 * -1: ikke i menyen, -2: i menyen, men ingen rad der. Leser bare, endrer ingenting. */
int meny_row_at(int y)
{
    if (!meny_in_menu()) return -1;
    if (M2.page == PAGE_TITLE) {
        /* Players, Gore, Practice, Select Knight, Online Game (meny_mog_ready) */
        static const int ty[5] = { 0x53, 0x6c, 0x88, 0x9c, 0xb0 };
        for (int i = 0; i < 5; i++) if (y >= ty[i] - 3 && y < ty[i] + 21) return i;
        return -2;
    }
    Row r[ROWS];
    page_rows(r);
    for (int i = 0; i < ROWS; i++) if (r[i].selectable && y >= row_y[i] - 1 && y < row_y[i] + 19) return i;
    return -2;
}

void meny_state(StateIO *s)
{
    STATE_VAR(s, M2);
    /* in_menu er bare for frontenden og ikke med i tilstanden: lastes et spill fra
     * kartet mens tittelmenyen vises, ville den staatt paa (hook_loop setter den igjen
     * i neste bilde hvis menyen er framme) */
    if (!s->saving) in_menu = false;
}
