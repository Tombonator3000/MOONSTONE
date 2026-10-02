/*
 * frontend.c - vinduet du spiller i: bilde, lyd, tastatur, joystick og spillkontrollere.
 *
 * Bildet fra emulatoren er hele PAL-omraadet (720 x 288 hires-piksler). Vi viser
 * bare spillets vindu (DIW, i Moonstone 320 x 200 lowres), med "skarpe" piksler:
 * forst heltallsskalering uten utjevning, saa jevn skalering til vinduet.
 *
 * Takt: Amigaen gaar paa 49,92 Hz (PAL). Vi kjorer de bildene som er forfalt
 * for hvert bilde skjermen viser, og justerer farten litt etter lydkoen.
 *
 * Taster: tastaturet sendes til Amigaen som det er, unntatt tastene som brukes
 * som joystick:
 *   spiller 1 (port 2): piltastene og Ctrl (fire)
 *   spiller 2 (port 1): talltastaturet 8 2 4 6 (7 9 1 3 skraatt) og 0 (fire)
 * F10 avslutter (som i WHDLoad), F11 fullskjerm, F12 skjermbilde, Pause pause,
 * Page Up / Page Down lagre / laste tilstand, End bytter plass, Home (hold) spoler.
 */
#include "amiga.h"
#include "frontend.h"
#include <SDL.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

bool png_write(const char *path, const uint32_t *rgba, int w, int h, int stride);

#define MAX_PADS 4
#define AUDIO_TARGET (AUDIO_RATE / 15)
#define AUDIO_MAX    (AUDIO_RATE / 3)

static SDL_Window *win;
static SDL_Renderer *ren;
static SDL_Texture *tex, *scaled;
static int scaled_w, scaled_h;
static SDL_AudioDeviceID adev;
static SDL_GameController *pads[MAX_PADS];
static bool running, paused, fullscreen;
static int filter = 0;                     /* 0 skarp, 1 myk, 2 piksel */
static bool aspect43;                      /* false = PAL-piksler (nesten kvadratiske) */
static int slot = 1;
static uint32_t msg_until;
static SDL_Rect crop = { (0x81 - FB_X0) * 2, 0x2c - FB_Y0, 640, 200 };
static int crop_stable;

static void show(const char *fmt, ...)
{
    char msg[160], title[200];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(msg, sizeof msg, fmt, ap);
    va_end(ap);
    snprintf(title, sizeof title, "Moonstone - %s", msg);
    if (win) SDL_SetWindowTitle(win, title);
    msg_until = SDL_GetTicks() + 2500;
    printf("%s\n", msg);
}

void frontend_message(const char *msg)
{
    if (SDL_ShowSimpleMessageBox(SDL_MESSAGEBOX_ERROR, "Moonstone", msg, NULL) != 0)
        fprintf(stderr, "%s\n", msg);
}

/* ------------------------------------------------------------ taster */
static int amiga_raw(SDL_Scancode s)
{
    if (s >= SDL_SCANCODE_1 && s <= SDL_SCANCODE_9) return 0x01 + (s - SDL_SCANCODE_1);
    if (s >= SDL_SCANCODE_F1 && s <= SDL_SCANCODE_F10) return 0x50 + (s - SDL_SCANCODE_F1);
    static const struct { SDL_Scancode s; int c; } map[] = {
        {SDL_SCANCODE_GRAVE,0x00},{SDL_SCANCODE_0,0x0a},{SDL_SCANCODE_MINUS,0x0b},{SDL_SCANCODE_EQUALS,0x0c},
        {SDL_SCANCODE_BACKSLASH,0x0d},{SDL_SCANCODE_Q,0x10},{SDL_SCANCODE_W,0x11},{SDL_SCANCODE_E,0x12},
        {SDL_SCANCODE_R,0x13},{SDL_SCANCODE_T,0x14},{SDL_SCANCODE_Y,0x15},{SDL_SCANCODE_U,0x16},
        {SDL_SCANCODE_I,0x17},{SDL_SCANCODE_O,0x18},{SDL_SCANCODE_P,0x19},{SDL_SCANCODE_LEFTBRACKET,0x1a},
        {SDL_SCANCODE_RIGHTBRACKET,0x1b},{SDL_SCANCODE_A,0x20},{SDL_SCANCODE_S,0x21},{SDL_SCANCODE_D,0x22},
        {SDL_SCANCODE_F,0x23},{SDL_SCANCODE_G,0x24},{SDL_SCANCODE_H,0x25},{SDL_SCANCODE_J,0x26},
        {SDL_SCANCODE_K,0x27},{SDL_SCANCODE_L,0x28},{SDL_SCANCODE_SEMICOLON,0x29},{SDL_SCANCODE_APOSTROPHE,0x2a},
        {SDL_SCANCODE_NONUSHASH,0x2b},{SDL_SCANCODE_NONUSBACKSLASH,0x30},{SDL_SCANCODE_Z,0x31},
        {SDL_SCANCODE_X,0x32},{SDL_SCANCODE_C,0x33},{SDL_SCANCODE_V,0x34},{SDL_SCANCODE_B,0x35},
        {SDL_SCANCODE_N,0x36},{SDL_SCANCODE_M,0x37},{SDL_SCANCODE_COMMA,0x38},{SDL_SCANCODE_PERIOD,0x39},
        {SDL_SCANCODE_SLASH,0x3a},{SDL_SCANCODE_SPACE,0x40},{SDL_SCANCODE_BACKSPACE,0x41},
        {SDL_SCANCODE_TAB,0x42},{SDL_SCANCODE_KP_ENTER,0x43},{SDL_SCANCODE_RETURN,0x44},
        {SDL_SCANCODE_ESCAPE,0x45},{SDL_SCANCODE_DELETE,0x46},{SDL_SCANCODE_KP_MINUS,0x4a},
        {SDL_SCANCODE_KP_PERIOD,0x3c},{SDL_SCANCODE_KP_DIVIDE,0x5c},{SDL_SCANCODE_KP_MULTIPLY,0x5d},
        {SDL_SCANCODE_KP_PLUS,0x5e},{SDL_SCANCODE_INSERT,0x5f},{SDL_SCANCODE_LSHIFT,0x60},
        {SDL_SCANCODE_RSHIFT,0x61},{SDL_SCANCODE_CAPSLOCK,0x62},{SDL_SCANCODE_LALT,0x64},
        {SDL_SCANCODE_RALT,0x65},{SDL_SCANCODE_LGUI,0x66},{SDL_SCANCODE_RGUI,0x67},
    };
    for (size_t i = 0; i < sizeof map / sizeof map[0]; i++) if (map[i].s == s) return map[i].c;
    return -1;
}

/* taster som er joystick og ikke sendes til Amigaen */
static bool is_joy_key(SDL_Scancode s)
{
    switch (s) {
    case SDL_SCANCODE_UP: case SDL_SCANCODE_DOWN: case SDL_SCANCODE_LEFT: case SDL_SCANCODE_RIGHT:
    case SDL_SCANCODE_LCTRL: case SDL_SCANCODE_RCTRL:
    case SDL_SCANCODE_KP_8: case SDL_SCANCODE_KP_2: case SDL_SCANCODE_KP_4: case SDL_SCANCODE_KP_6:
    case SDL_SCANCODE_KP_7: case SDL_SCANCODE_KP_9: case SDL_SCANCODE_KP_1: case SDL_SCANCODE_KP_3:
    case SDL_SCANCODE_KP_0: case SDL_SCANCODE_KP_5:
        return true;
    default:
        return false;
    }
}

static void read_joysticks(void)
{
    const uint8_t *k = SDL_GetKeyboardState(NULL);
    uint8_t j1 = 0, j0 = 0;
    if (k[SDL_SCANCODE_UP]) j1 |= JOY_UP;
    if (k[SDL_SCANCODE_DOWN]) j1 |= JOY_DOWN;
    if (k[SDL_SCANCODE_LEFT]) j1 |= JOY_LEFT;
    if (k[SDL_SCANCODE_RIGHT]) j1 |= JOY_RIGHT;
    if (k[SDL_SCANCODE_LCTRL] || k[SDL_SCANCODE_RCTRL]) j1 |= JOY_FIRE;
    if (k[SDL_SCANCODE_KP_8] || k[SDL_SCANCODE_KP_7] || k[SDL_SCANCODE_KP_9]) j0 |= JOY_UP;
    if (k[SDL_SCANCODE_KP_2] || k[SDL_SCANCODE_KP_1] || k[SDL_SCANCODE_KP_3]) j0 |= JOY_DOWN;
    if (k[SDL_SCANCODE_KP_4] || k[SDL_SCANCODE_KP_7] || k[SDL_SCANCODE_KP_1]) j0 |= JOY_LEFT;
    if (k[SDL_SCANCODE_KP_6] || k[SDL_SCANCODE_KP_9] || k[SDL_SCANCODE_KP_3]) j0 |= JOY_RIGHT;
    if (k[SDL_SCANCODE_KP_0] || k[SDL_SCANCODE_KP_5]) j0 |= JOY_FIRE;
    /* spillkontroller 1 er spiller 1 (port 2), kontroller 2 er spiller 2 (port 1) */
    for (int i = 0; i < 2; i++) {
        SDL_GameController *g = pads[i];
        if (!g) continue;
        uint8_t j = 0;
        int ax = SDL_GameControllerGetAxis(g, SDL_CONTROLLER_AXIS_LEFTX);
        int ay = SDL_GameControllerGetAxis(g, SDL_CONTROLLER_AXIS_LEFTY);
        if (ax < -12000 || SDL_GameControllerGetButton(g, SDL_CONTROLLER_BUTTON_DPAD_LEFT))  j |= JOY_LEFT;
        if (ax >  12000 || SDL_GameControllerGetButton(g, SDL_CONTROLLER_BUTTON_DPAD_RIGHT)) j |= JOY_RIGHT;
        if (ay < -12000 || SDL_GameControllerGetButton(g, SDL_CONTROLLER_BUTTON_DPAD_UP))    j |= JOY_UP;
        if (ay >  12000 || SDL_GameControllerGetButton(g, SDL_CONTROLLER_BUTTON_DPAD_DOWN))  j |= JOY_DOWN;
        if (SDL_GameControllerGetButton(g, SDL_CONTROLLER_BUTTON_A)) j |= JOY_FIRE;
        if (i == 0) j1 |= j; else j0 |= j;
    }
    IN.joy[1] = j1;
    IN.joy[0] = j0;
}

/* Knappene paa en spillkontroller som CD32-padden i cd32load-oppsettet:
 * B = mellomrom (blaa), Start = E (play), LB/RB = 1/2, X/Y = 3/4, Back = Esc. */
static int pad_key(int button)
{
    switch (button) {
    case SDL_CONTROLLER_BUTTON_B: return 0x40;
    case SDL_CONTROLLER_BUTTON_START: return 0x12;
    case SDL_CONTROLLER_BUTTON_LEFTSHOULDER: return 0x01;
    case SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: return 0x02;
    case SDL_CONTROLLER_BUTTON_X: return 0x03;
    case SDL_CONTROLLER_BUTTON_Y: return 0x04;
    case SDL_CONTROLLER_BUTTON_BACK: return 0x45;
    default: return -1;
    }
}

static void pad_added(int index)
{
    if (!SDL_IsGameController(index)) return;
    SDL_JoystickID id = SDL_JoystickGetDeviceInstanceID(index);
    for (int i = 0; i < MAX_PADS; i++)
        if (pads[i] && SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(pads[i])) == id) return;
    for (int i = 0; i < MAX_PADS; i++) {
        if (pads[i]) continue;
        pads[i] = SDL_GameControllerOpen(index);
        if (pads[i]) show("Spillkontroller %d: %s", i + 1, SDL_GameControllerName(pads[i]));
        return;
    }
}

static void pad_removed(SDL_JoystickID id)
{
    for (int i = 0; i < MAX_PADS; i++) {
        if (!pads[i] || SDL_JoystickInstanceID(SDL_GameControllerGetJoystick(pads[i])) != id) continue;
        SDL_GameControllerClose(pads[i]);
        pads[i] = NULL;
        show("Spillkontroller %d koblet fra", i + 1);
    }
}

/* ------------------------------------------------------------ bilde */
static void update_crop(void)
{
    SDL_Rect r = { video_diw[0], video_diw[1], video_diw[2] - video_diw[0], video_diw[3] - video_diw[1] };
    if (r.x < 0) { r.w += r.x; r.x = 0; }
    if (r.y < 0) { r.h += r.y; r.y = 0; }
    if (r.x + r.w > FB_W) r.w = FB_W - r.x;
    if (r.y + r.h > FB_H) r.h = FB_H - r.y;
    if (r.w < 320 || r.h < 100) return;
    if (r.x == crop.x && r.y == crop.y && r.w == crop.w && r.h == crop.h) { crop_stable = 0; return; }
    if (++crop_stable < 25) return;        /* bytt bare naar vinduet har vaert likt en stund */
    crop = r;
    crop_stable = 0;
}

static void present(void)
{
    int ow, oh;
    SDL_GetRendererOutputSize(ren, &ow, &oh);
    /* hires-piksler er halvparten saa brede som hoye */
    double aspect = aspect43 ? 4.0 / 3.0 : (double)crop.w / 2.0 / crop.h;
    SDL_Rect dst;
    if ((double)ow / oh > aspect) { dst.h = oh; dst.w = (int)(oh * aspect + 0.5); }
    else { dst.w = ow; dst.h = (int)(ow / aspect + 0.5); }
    dst.x = (ow - dst.w) / 2;
    dst.y = (oh - dst.h) / 2;
    SDL_UpdateTexture(tex, NULL, video_fb, FB_W * 4);
    SDL_SetRenderDrawColor(ren, 0, 0, 0, 255);
    SDL_RenderClear(ren);
    if (filter == 0) {
        int kx = dst.w / (crop.w / 2), ky = dst.h / crop.h;
        if (kx < 1) kx = 1;
        if (ky < 1) ky = 1;
        int w = crop.w / 2 * kx, h = crop.h * ky;
        if (!scaled || w != scaled_w || h != scaled_h) {
            if (scaled) SDL_DestroyTexture(scaled);
            scaled = SDL_CreateTexture(ren, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, w, h);
            if (scaled) SDL_SetTextureScaleMode(scaled, SDL_ScaleModeLinear);
            scaled_w = w; scaled_h = h;
        }
        if (scaled && SDL_SetRenderTarget(ren, scaled) == 0) {
            SDL_SetTextureScaleMode(tex, SDL_ScaleModeNearest);
            SDL_RenderCopy(ren, tex, &crop, NULL);
            SDL_SetRenderTarget(ren, NULL);
            SDL_RenderCopy(ren, scaled, NULL, &dst);
            SDL_RenderPresent(ren);
            return;
        }
    }
    SDL_SetTextureScaleMode(tex, filter == 2 ? SDL_ScaleModeNearest : SDL_ScaleModeLinear);
    SDL_RenderCopy(ren, tex, &crop, &dst);
    SDL_RenderPresent(ren);
}

static void set_fullscreen(bool on)
{
    fullscreen = on;
    SDL_SetWindowFullscreen(win, on ? SDL_WINDOW_FULLSCREEN_DESKTOP : 0);
    SDL_ShowCursor(on ? SDL_DISABLE : SDL_ENABLE);
}

static void screenshot(void)
{
    char name[64];
    snprintf(name, sizeof name, "skjermbilde_%05u.png", M.frame);
    uint32_t *buf = malloc((size_t)crop.w * crop.h * 4);
    for (int y = 0; y < crop.h; y++)
        memcpy(buf + (size_t)y * crop.w, video_fb + (size_t)(crop.y + y) * FB_W + crop.x, (size_t)crop.w * 4);
    if (png_write(name, buf, crop.w, crop.h, crop.w)) show("Skjermbilde lagret: %s", name);
    free(buf);
}

/* ------------------------------------------------------------ hendelser */
static void state_path(char *out, size_t n) { snprintf(out, n, "moonstone_tilstand%d.sav", slot); }

static void key_event(const SDL_KeyboardEvent *e, bool down)
{
    SDL_Scancode s = e->keysym.scancode;
    bool alt = (e->keysym.mod & KMOD_ALT) != 0;
    if (down && !e->repeat) {
        char path[64];
        switch (s) {
        case SDL_SCANCODE_F11: set_fullscreen(!fullscreen); return;
        case SDL_SCANCODE_RETURN: if (alt) { set_fullscreen(!fullscreen); return; } break;
        case SDL_SCANCODE_F12: screenshot(); return;
        case SDL_SCANCODE_PAUSE: case SDL_SCANCODE_SCROLLLOCK:
            paused = !paused;
            show("%s", paused ? "Pause" : "Fortsetter");
            if (paused && adev) SDL_ClearQueuedAudio(adev);
            return;
        case SDL_SCANCODE_PAGEUP:
            state_path(path, sizeof path);
            show(state_save_file(path) ? "Tilstand lagret paa plass %d" : "Klarte ikke aa lagre (plass %d)", slot);
            return;
        case SDL_SCANCODE_PAGEDOWN:
            state_path(path, sizeof path);
            if (state_load_file(path)) { show("Tilstand lastet fra plass %d", slot); if (adev) SDL_ClearQueuedAudio(adev); }
            else show("Ingen tilstand paa plass %d", slot);
            return;
        case SDL_SCANCODE_END:
            slot = slot % 9 + 1;
            show("Plass %d for lagring", slot);
            return;
        case SDL_SCANCODE_PRINTSCREEN:
            filter = (filter + 1) % 3;
            show("Filter: %s", filter == 0 ? "skarp" : filter == 1 ? "myk" : "piksel");
            return;
        case SDL_SCANCODE_HOME: return;
        case SDL_SCANCODE_KP_DIVIDE:
            if (alt) { aspect43 = !aspect43; show("%s", aspect43 ? "Format 4:3" : "Format som PAL"); return; }
            break;
        default: break;
        }
    }
    if (e->repeat || is_joy_key(s)) return;
    int code = amiga_raw(s);
    if (code >= 0) amiga_key(code, down);
}

static void poll_events(void)
{
    SDL_Event e;
    while (SDL_PollEvent(&e)) {
        switch (e.type) {
        case SDL_QUIT: running = false; break;
        case SDL_KEYDOWN: key_event(&e.key, true); break;
        case SDL_KEYUP: key_event(&e.key, false); break;
        case SDL_CONTROLLERDEVICEADDED: pad_added(e.cdevice.which); break;
        case SDL_CONTROLLERDEVICEREMOVED: pad_removed(e.cdevice.which); break;
        case SDL_CONTROLLERBUTTONDOWN: case SDL_CONTROLLERBUTTONUP: {
            int k = pad_key(e.cbutton.button);
            if (k >= 0) amiga_key(k, e.type == SDL_CONTROLLERBUTTONDOWN);
            break;
        }
        default: break;
        }
    }
}

/* ------------------------------------------------------------ hovedlokken */
int frontend_run(const FrontendOptions *o)
{
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMECONTROLLER) != 0) {
        fprintf(stderr, "SDL: %s\n", SDL_GetError());
        return 1;
    }
    int scale = o->scale > 0 ? o->scale : 3;
    win = SDL_CreateWindow("Moonstone", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                           320 * scale, 200 * scale, SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI);
    if (!win) { fprintf(stderr, "SDL: %s\n", SDL_GetError()); return 1; }
    ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_TARGETTEXTURE | SDL_RENDERER_PRESENTVSYNC);
    if (!ren) ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_SOFTWARE);
    if (!ren) { fprintf(stderr, "SDL: %s\n", SDL_GetError()); return 1; }
    tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_ABGR8888, SDL_TEXTUREACCESS_STREAMING, FB_W, FB_H);
    if (o->fullscreen) set_fullscreen(true);
    SDL_AudioSpec want, have;
    SDL_zero(want);
    want.freq = AUDIO_RATE;
    want.format = AUDIO_S16SYS;
    want.channels = 2;
    want.samples = 1024;
    adev = SDL_OpenAudioDevice(NULL, 0, &want, &have, 0);
    if (adev) SDL_PauseAudioDevice(adev, 0);
    else fprintf(stderr, "Fant ingen lydenhet: %s\n", SDL_GetError());
    for (int i = 0; i < SDL_NumJoysticks(); i++) pad_added(i);
    paula_volume = o->volume;

    printf("Moonstone. Spiller 1: piltaster og Ctrl. Spiller 2: talltastaturet og 0.\n"
           "F10 avslutter, F11 fullskjerm, F12 skjermbilde, Pause pause,\n"
           "Page Up/Down lagre/laste tilstand, End bytter plass, Home (hold) spoler, Print Screen filter.\n");

    static int16_t abuf[AUDIO_RING * 2];
    running = true;
    uint64_t freq = SDL_GetPerformanceFrequency(), t0 = SDL_GetPerformanceCounter();
    double emu_time = 0, rate = 1.0;
    while (running) {
        poll_events();
        if (msg_until && SDL_TICKS_PASSED(SDL_GetTicks(), msg_until)) {
            msg_until = 0;
            SDL_SetWindowTitle(win, paused ? "Moonstone - Pause" : "Moonstone");
        }
        const uint8_t *ks = SDL_GetKeyboardState(NULL);
        bool fast = ks[SDL_SCANCODE_HOME] != 0;
        double real = (double)(SDL_GetPerformanceCounter() - t0) / freq;
        if (paused) emu_time = real;
        else {
            int ran = 0, maxrun = fast ? 8 : 3;
            while ((fast || emu_time <= real) && ran < maxrun && running) {
                read_joysticks();
                amiga_run_frame();
                int n = paula_take(abuf, AUDIO_RING);
                if (adev && !fast && n > 0) {
                    if (SDL_GetQueuedAudioSize(adev) / 4 > AUDIO_MAX) SDL_ClearQueuedAudio(adev);
                    SDL_QueueAudio(adev, abuf, (Uint32)n * 4);
                }
                emu_time += rate / AMIGA_HZ;
                ran++;
                if (M.aborted) {
                    show("%s", M.abort_msg);
                    running = false;
                }
            }
            if (fast || real - emu_time > 0.25) emu_time = real;
        }
        update_crop();
        present();
        if (adev && !paused && !fast) {
            double q = SDL_GetQueuedAudioSize(adev) / 4.0;
            double err = (q - AUDIO_TARGET) / AUDIO_TARGET;
            if (err > 1) err = 1;
            if (err < -1) err = -1;
            rate = 1.0 + 0.005 * err;
        }
        double now = (double)(SDL_GetPerformanceCounter() - t0) / freq;
        double wait = emu_time - now;
        if (wait > 0.003) SDL_Delay((Uint32)(wait * 1000.0) - 1);
    }
    for (int i = 0; i < MAX_PADS; i++) if (pads[i]) SDL_GameControllerClose(pads[i]);
    if (adev) SDL_CloseAudioDevice(adev);
    SDL_Quit();
    return 0;
}
