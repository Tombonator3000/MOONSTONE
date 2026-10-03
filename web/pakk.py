#!/usr/bin/env python3
"""
pakk.py - setter sammen nettleserversjonen til en HTML-fil.

    python3 web/pakk.py web/build/moonstone-core.js web/build/moonstone.html

Kjernen (WebAssembly innebygd i moonstone-core.js), bibliotekene i web/vendor
og kildene i web/src legges inn i web/src/index.html. Filen virker fra disk og
paa GitHub Pages uten noe annet.
"""
import os
import sys

HER = os.path.dirname(os.path.abspath(__file__))
APP = ['core.js', 'audio.js', 'render.js', 'input.js', 'store.js', 'net.js', 'rooms.js', 'grafikk.js', 'app.js']
VENDOR = ['three.min.js', 'peerjs.min.js', 'mqtt.min.js']


def les(sti):
    with open(sti, encoding='utf-8') as f:
        return f.read()


def trygg(js):
    # "</script" inne i et skript ville avsluttet taggen for tidlig
    return js.replace('</script', '<\\/script')


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    kjerne, ut = sys.argv[1], sys.argv[2]
    html = les(os.path.join(HER, 'src', 'index.html'))
    stil = les(os.path.join(HER, 'src', 'style.css'))
    vendor = '\n;\n'.join(trygg(les(os.path.join(HER, 'vendor', f))) for f in VENDOR)
    app = '\n'.join('/* ---- %s ---- */\n%s' % (f, trygg(les(os.path.join(HER, 'src', f)))) for f in APP)
    html = html.replace('%%STIL%%', stil)
    html = html.replace('%%VENDOR%%', vendor)
    html = html.replace('%%KJERNE%%', trygg(les(kjerne)))
    html = html.replace('%%APP%%', app)
    os.makedirs(os.path.dirname(os.path.abspath(ut)), exist_ok=True)
    with open(ut, 'w', encoding='utf-8') as f:
        f.write(html)
    print('%s: %d kB' % (ut, os.path.getsize(ut) // 1024))


if __name__ == '__main__':
    main()
