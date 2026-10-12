"""Kjor naturfont og tekstnegative sekvensielt etter ferdig Balok-standardproeve."""
from pathlib import Path
import json
import os
import subprocess
import time

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
BASE = ART / 'verification/frontend008-candidate-v1'
NODE = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
RUNTIME = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
PRODUCTION = ROOT / 'art/hd-completion-figures-2026-10-11/production'
pending = BASE / 'balok-standard/test.json'
deadline = time.monotonic() + 900
while not pending.exists():
    assert time.monotonic() < deadline, 'Balok-standard ble ikke ferdig'
    time.sleep(5)
assert json.loads(pending.read_text())['status'] == 'passed'
for directory, script, report in [
    ('font', 'runtime-tekst-eierskap-font-v1.cjs', 'font-runtime-test.json'),
    ('text-fixtures', 'runtime-tekst-eierskap-fixtures-v1.cjs', 'text-owner-fixtures.json'),
]:
    out = BASE / directory
    assert not out.exists(), 'Bevar tidligere proeve'
    env = os.environ.copy()
    env.update(NODE_PATH=RUNTIME, MOONSTONE_FONT_PACKAGE=str(BASE / 'package'),
               MOONSTONE_VERIFY_OUT=str(out), MOONSTONE_TEXT_SCRIPT=script)
    result = subprocess.run([NODE, str(PRODUCTION / 'runtime-tekst-eierskap-host-v1.cjs')],
                            cwd=ROOT, env=env, text=True, capture_output=True)
    (BASE / (directory + '.stdout.txt')).write_text(result.stdout)
    (BASE / (directory + '.stderr.txt')).write_text(result.stderr)
    data = json.loads((out / report).read_text())
    assert result.returncode == 0 and data['status'] == 'passed', result.stderr
    print(json.dumps(dict(test=directory, status=data['status'], checks=len(data['checks']))), flush=True)
result = subprocess.run(['python3', str(ART / 'freeze-frontend008-v1.py')], cwd=ROOT)
assert result.returncode == 0
