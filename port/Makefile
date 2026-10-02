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

# Spillfila fra repoet bygges inn i programmet, saa spillet starter uten at noen
# maa finne den (Moonstone regnes som abandonware, og eieren har bestemt det).
# make MED_SPILLET=nei bygger uten; da ser programmet etter fila paa disk.
MED_SPILLET ?= ja
SPILL       ?= ../Moonstonecd32-AMIGA.zip
SPILL_INN    = $(if $(filter ja,$(MED_SPILLET)),$(wildcard $(SPILL)))

CORE_SRC = src/amiga.c src/custom.c src/blitter.c src/video.c src/paula.c src/cia.c src/whdload.c \
           src/files.c src/unzip.c src/decrunch.c src/hooks.c src/game.c src/patch.c src/meny.c src/hver.c src/lag.c src/state.c src/cpu_state.c src/png.c \
           src/decomp/decomp.c src/spilldata.c
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

# lages hver gang, men skrives bare om naar innholdet er endret
src/spilldata.c: bin2c.py FORCE
	python3 bin2c.py $@ $(SPILL_INN)

clean:
	rm -rf build-win build-web ../web/build
	rm -f $(CORE_OBJ) $(MUSASHI_OBJ) src/*.o src/spilldata.c moonstone moonstone-headless moonstone.exe SDL2.dll ext/musashi/m68kmake $(MUSASHI_GEN)

.PHONY: clean headless windows web FORCE
FORCE:

# Kryssbygging til Windows fra Linux:
#   make windows SDL2_MINGW=/sti/til/SDL2-2.30.x/x86_64-w64-mingw32
SDL2_MINGW ?= SDL2/x86_64-w64-mingw32
WIN_SRC = $(CORE_SRC) $(MUSASHI_SRC) src/main.c src/frontend.c
WOBJ = $(WIN_SRC:%.c=build-win/%.o)
windows: moonstone.exe
moonstone.exe: $(WOBJ)
	x86_64-w64-mingw32-gcc -o $@ $(WOBJ) -L$(SDL2_MINGW)/lib -lmingw32 -lSDL2main -lSDL2 -mconsole -static-libgcc -Wl,-Bstatic -lwinpthread -Wl,-Bdynamic
	cp $(SDL2_MINGW)/bin/SDL2.dll .
build-win/%.o: %.c src/amiga.h $(MUSASHI_GEN)
	@mkdir -p $(dir $@)
	x86_64-w64-mingw32-gcc -O2 -std=gnu99 -w -Iext/musashi -Isrc -I$(SDL2_MINGW)/include/SDL2 -Dmain=SDL_main -c -o $@ $<

# Nettleserversjonen: kjernen som WebAssembly (krever emscripten), pakket sammen
# med web/src og web/vendor til en fil, web/build/moonstone.html.
#   make web
WEB_C   = src/web.c $(filter-out src/png.c,$(CORE_SRC)) $(filter-out ext/musashi/m68kdasm.c,$(MUSASHI_SRC)) ext/musashi/m68kdasm.c
WEB_OBJ = $(WEB_C:%.c=build-web/%.o)
WEB_LDFLAGS = -O3 -sMODULARIZE=1 -sEXPORT_NAME=MoonCore -sSINGLE_FILE=1 -sENVIRONMENT=web,worker \
          -sALLOW_MEMORY_GROWTH=1 -sINITIAL_MEMORY=67108864 -sTOTAL_STACK=1048576 -sFILESYSTEM=0 \
          -sEXPORTED_FUNCTIONS=_malloc,_free -sEXPORTED_RUNTIME_METHODS=UTF8ToString,stringToUTF8,lengthBytesUTF8,HEAPU8,HEAP16,HEAP32,HEAPU32,HEAPF32
web: ../web/build/moonstone.html
../web/build/moonstone-core.js: $(WEB_OBJ)
	@mkdir -p $(dir $@)
	emcc -o $@ $(WEB_OBJ) $(WEB_LDFLAGS)
../web/build/moonstone.html: ../web/build/moonstone-core.js $(wildcard ../web/src/*) $(wildcard ../web/vendor/*)
	python3 ../web/pakk.py ../web/build/moonstone-core.js $@
build-web/%.o: %.c src/amiga.h $(MUSASHI_GEN)
	@mkdir -p $(dir $@)
	emcc -O3 -std=gnu99 -w -Iext/musashi -Isrc -c -o $@ $<
