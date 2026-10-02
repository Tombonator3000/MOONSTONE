# Bygger Moonstone-porten. Krever gcc/clang og SDL2 (libsdl2-dev).
# Linux/macOS: make        Windows (MSYS2/MinGW): make
#   make headless          uten SDL, bare for testing (--headless)
#   make windows           kryssbygging med MinGW (se under)
#   make web               nettleserversjonen (krever emscripten)
CC      ?= gcc
HOSTCC  ?= cc
SDL_CFLAGS := $(shell sdl2-config --cflags 2>/dev/null)
SDL_LIBS   := $(shell sdl2-config --libs 2>/dev/null)
CFLAGS  ?= -O2 -g
CFLAGS  += -std=gnu99 -Wall -Wno-misleading-indentation -Iext/musashi -Isrc

CORE_SRC = src/amiga.c src/custom.c src/blitter.c src/video.c src/paula.c src/cia.c src/whdload.c \
           src/files.c src/unzip.c src/decrunch.c src/hooks.c src/state.c src/cpu_state.c src/png.c \
           src/decomp/decomp.c
MUSASHI_SRC = ext/musashi/m68kcpu.c ext/musashi/m68kops.c ext/musashi/m68kdasm.c ext/musashi/softfloat/softfloat.c
CORE_OBJ = $(CORE_SRC:.c=.o)
MUSASHI_OBJ = $(MUSASHI_SRC:.c=.o)

moonstone: $(CORE_OBJ) $(MUSASHI_OBJ) src/main.o src/frontend.o
	$(CC) -o $@ $^ $(SDL_LIBS) -lm

headless: moonstone-headless
moonstone-headless: $(CORE_OBJ) $(MUSASHI_OBJ) src/main.o src/nofrontend.o
	$(CC) -o $@ $^ -lm

src/frontend.o: src/frontend.c src/amiga.h src/frontend.h
	$(CC) $(CFLAGS) $(SDL_CFLAGS) -c -o $@ $<

# Musashi lager instruksjonstabellene (m68kops.c/h) fra m68k_in.c med m68kmake.
MUSASHI_GEN = ext/musashi/m68kops.c ext/musashi/m68kops.h
ext/musashi/m68kops.c: ext/musashi/m68kmake.c ext/musashi/m68k_in.c
	$(HOSTCC) -O2 -w -o ext/musashi/m68kmake ext/musashi/m68kmake.c
	cd ext/musashi && ./m68kmake
ext/musashi/m68kops.h: ext/musashi/m68kops.c
ext/musashi/%.o: ext/musashi/%.c $(MUSASHI_GEN)
	$(CC) -O2 -Iext/musashi -w -c -o $@ $<

src/%.o: src/%.c src/amiga.h $(MUSASHI_GEN)
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -rf build-win build-web ../web/build
	rm -f $(CORE_OBJ) $(MUSASHI_OBJ) src/*.o moonstone moonstone-headless moonstone.exe SDL2.dll ext/musashi/m68kmake $(MUSASHI_GEN)

.PHONY: clean headless windows web
