#!/bin/sh
# Lager three.min.js med bare delene av three.js som nettsiden bruker.
# Krever Node og npm. Kjor fra web/vendor: sh lag-three.sh
set -e
TMP=$(mktemp -d)
cp three-entry.js "$TMP/"
cd "$TMP"
npm init -y >/dev/null
npm install --silent esbuild@0.25 three@0.186.1
./node_modules/.bin/esbuild three-entry.js --bundle --minify --format=iife --global-name=THREE --outfile=three.min.js --legal-comments=none
cd - >/dev/null
( echo "/* three.js r186 (MIT-lisens, se LICENSE-three.txt), bare delene vi bruker. Lages med web/vendor/lag-three.sh */"; cat "$TMP/three.min.js" ) > three.min.js
rm -rf "$TMP"
