#!/bin/bash
# Kjorer nettlesertestene i tests/nettleser mot en lokal kopi av nettsiden.
#
# Bruk:  tests/kjor.sh            alle testene
#        tests/kjor.sh lag1 ver1  bare disse
#
# Bygger nettsiden (make -C port web) og moonstone-headless om de mangler, installerer
# serverne (npm i tests/nettleser/servere) foerste gang, starter en HTTP-server,
# PeerJS og MQTT lokalt, kjorer testene og skriver OK eller FEIL per test. Serverne
# stoppes etterpaa. Exit 1 om en test feilet.
#
# Miljovariabler:
#   SIDE            nettsiden som testes (standard web/build/moonstone.html)
#   MOONSTONE_PORT  porten til HTTP-serveren (8765)
#   PEER_PORT       PeerJS (9000)
#   MQTT_PORT       MQTT over WebSocket (8883)
#   TIDSGRENSE      sekunder per test (900)
#   MOONSTONE_UT    mappe for logger, skjermbilder og tilstander (standard: ny mappe i /tmp)
#   MOONSTONE_GAMLE mappe med lagringer fra eldre versjoner (kamp6.sav, gml.sav) til lag1
set -u

REPO=$(cd "$(dirname "$0")/.." && pwd)
T=$REPO/tests/nettleser
SIDE=${SIDE:-$REPO/web/build/moonstone.html}
export MOONSTONE_PORT=${MOONSTONE_PORT:-8765}
PEER_PORT=${PEER_PORT:-9000}
MQTT_PORT=${MQTT_PORT:-8883}
TIDSGRENSE=${TIDSGRENSE:-900}
UT=${MOONSTONE_UT:-$(mktemp -d /tmp/moonstone-tester-XXXXXX)}
mkdir -p "$UT"
export MOONSTONE_PEER=127.0.0.1:$PEER_PORT
export MOONSTONE_MQTT=ws://127.0.0.1:$MQTT_PORT/mqtt
export PEER_PORT MQTT_PORT

# Playwright: fra NODE_PATH, eller /opt/node-tools der det ligger i skymiljoet
if ! node -e "require('playwright')" 2>/dev/null; then
    export NODE_PATH=${NODE_PATH:+$NODE_PATH:}/opt/node-tools/node_modules
    if ! node -e "require('playwright')" 2>/dev/null; then
        echo "Fant ikke Playwright. Installer med: npm install -g playwright && npx playwright install chromium"
        exit 1
    fi
fi

# testene som skal kjores
if [ $# -gt 0 ]; then
    TESTER=("$@")
else
    TESTER=()
    for f in "$T"/*.js; do
        n=$(basename "$f" .js)
        [ "$n" = felles ] || TESTER+=("$n")
    done
fi
for t in "${TESTER[@]}"; do
    [ -f "$T/$t.js" ] || { echo "Ukjent test: $t (se tests/README.md)"; exit 1; }
done

# bygg det som mangler
if [ ! -f "$SIDE" ]; then
    echo "Bygger nettsiden (make -C port web)"
    make -C "$REPO/port" -j4 web || exit 1
fi
if [ ! -x "$REPO/port/moonstone-headless" ]; then
    echo "Bygger moonstone-headless"
    make -C "$REPO/port" -j4 headless || exit 1
fi
if [ ! -d "$T/servere/node_modules" ]; then
    echo "Installerer testserverne (npm)"
    (cd "$T/servere" && npm install --no-audit --no-fund) || exit 1
fi

lytter() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }

# portene maa vaere ledige
for p in "$MOONSTONE_PORT" "$PEER_PORT" "$MQTT_PORT"; do
    if lytter "$p"; then
        echo "Porten $p er i bruk. Stopp det som kjorer der, eller velg andre porter (MOONSTONE_PORT, PEER_PORT, MQTT_PORT)."
        exit 1
    fi
done

PIDS=()
stopp() {
    for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null; done
    wait 2>/dev/null
}
trap stopp EXIT
trap 'exit 130' INT TERM

mkdir -p "$UT/side"
cp "$SIDE" "$UT/side/index.html"
python3 -m http.server "$MOONSTONE_PORT" --bind 127.0.0.1 --directory "$UT/side" > "$UT/http.log" 2>&1 &
PIDS+=($!)
node "$T/servere/peerserver.js" > "$UT/peer.log" 2>&1 &
PIDS+=($!)
node "$T/servere/mqttserver.js" > "$UT/mqtt.log" 2>&1 &
PIDS+=($!)

klar() {   # venter til porten svarer (opptil 15 s)
    for _ in $(seq 1 75); do
        lytter "$1" && return 0
        sleep 0.2
    done
    echo "Serveren paa port $1 startet ikke (se $UT)"
    exit 1
}
klar "$MOONSTONE_PORT"; klar "$PEER_PORT"; klar "$MQTT_PORT"

echo "Tester $SIDE paa http://127.0.0.1:$MOONSTONE_PORT/ (logger i $UT)"
FEILET=0
for t in "${TESTER[@]}"; do
    start=$(date +%s)
    timeout "$TIDSGRENSE" node "$T/$t.js" --ut "$UT/$t" > "$UT/$t.log" 2>&1
    rc=$?
    ok=$(grep -c '^OK' "$UT/$t.log")
    feil=$(grep -c '^FEIL' "$UT/$t.log")
    tid=$(( $(date +%s) - start ))
    if [ $rc -eq 0 ] && [ "$feil" -eq 0 ] && [ "$ok" -gt 0 ]; then
        echo "OK   $t ($ok sjekker, $tid s)"
    else
        FEILET=1
        [ $rc -eq 124 ] && grunn="tidsgrensen paa $TIDSGRENSE s" || grunn="exit $rc"
        echo "FEIL $t ($ok OK, $feil FEIL, $grunn, $tid s, logg: $UT/$t.log)"
        grep '^FEIL' "$UT/$t.log" | sed 's/^/       /' | head -20
    fi
    grep '^HOPPER OVER' "$UT/$t.log" | sed 's/^/       /'
done
exit $FEILET
