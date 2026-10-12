"""Kjor nye kandidatreproofs og skrivebeskyttet preflight sekvensielt paa008."""
from pathlib import Path
import json
import os
import subprocess
import time

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
BASE = ART / 'verification/frontend008-candidate-v1'
BEAST = ROOT / 'art/hd-completion-figures-2026-10-11/production/beast'
NODE = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
RUNTIME = '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
pending = BASE / 'combined-regression-v1.json'
deadline = time.monotonic() + 900
while not pending.exists():
    assert time.monotonic() < deadline, 'Samlet008-port ble ikke ferdig'
    time.sleep(5)
assert json.loads(pending.read_text())['status'] == 'passed'
results = []


def execute(command, env, name):
    process = subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True)
    (BASE / (name + '.stdout.txt')).write_text(process.stdout)
    (BASE / (name + '.stderr.txt')).write_text(process.stderr)
    assert process.returncode == 0, (name, process.stdout, process.stderr)
    print(process.stdout, end='', flush=True)


for group, directory, script, output, contract in [
    ('shadow015', BEAST / 'shadow015-v1', 'runtime-frontend008-v1.cjs', 'verification/fixtures-frontend008-v1', 'activation-set-shadow015-v2.json'),
    ('beast11', BEAST / 'next042-055-v1', 'runtime-fixtures-frontend008-v1.cjs', 'verification/runtime-frontend008-v1', 'activation-set-eleven-v2.json'),
]:
    env = os.environ.copy()
    env.update(NODE_PATH=RUNTIME, MOONSTONE_BEAST_PACKAGE=str(BASE / 'package'),
               MOONSTONE_CODE_FREEZE=str(BASE / 'sources'), MOONSTONE_HD_TEST_OUTPUT=str(directory / output),
               MOONSTONE_BEAST_MODE='fixtures')
    execute([NODE, str(directory / script)], env, group + '-runtime')
    execute(['python3', str(ART / 'rebind-candidates-frontend008-v2.py'), group], env, group + '-freeze')
    execute(['python3', 'tools/hd_figurer_aktiver.py', str(directory / contract)], env, group + '-preflight')
    results.append(dict(group=group, contract=str((directory / contract).relative_to(ROOT))))

env = os.environ.copy()
execute(['python3', str(ART / 'run-r1-rest40-frontend008-v1.py')], env, 'ratmen40-runtime')
execute(['python3', str(ART / 'rebind-candidates-frontend008-v2.py'), 'ratmen40'], env, 'ratmen40-freeze')
contract = ART / 'activation-set-ratmen-r1-rest40-v2.json'
execute(['python3', 'tools/hd_figurer_aktiver.py', str(contract)], env, 'ratmen40-preflight')
results.append(dict(group='ratmen40', contract=str(contract.relative_to(ROOT))))
summary = BASE / 'candidate-reproofs-v1.json'
assert not summary.exists()
summary.write_text(json.dumps(dict(schema=1, status='passed_not_activated', groups=results), indent=2) + '\n')
