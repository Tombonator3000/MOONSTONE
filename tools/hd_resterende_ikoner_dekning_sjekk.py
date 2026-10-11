#!/usr/bin/env python3
"""Valider levert CEL-dekning etter flettingen av main.

Standardkommandoen validerer de nye 62 CEL-fixturene og tilleggskontrollene
mot aktiv kode og grafikk. Den tidligere 833-rapporten er historisk bevis
fra foer flettingen og valideres ikke mot dagens renderer.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/hd-remaining-icons-2026-10-11'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def contract_sha(meta):
    return sha(json.dumps(meta,sort_keys=True,separators=(',',':')).encode())


def proof(row):
    keys=('key','raw_sha256','source_sha256','record_sha256','prompt_sha256','packed_sha256')
    return {**{k:row[k] for k in keys},'variants':[{k:v[k] for k in ('id','key','raw_sha256','packed_sha256')} for v in row.get('variants',[])]}


def main():
    # Mergeverktøyet importerer hashe-/kontrakthjelperne over. Kjoer det som egen
    # CLI i stedet for aa importere det tilbake her og lage en sirkulaer import.
    checker = ROOT/'tools/hd_resterende_ikoner_merge_sjekk.py'
    return subprocess.call([sys.executable, str(checker)], cwd=ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
