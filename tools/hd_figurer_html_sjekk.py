"""Kontroller at manifestinnsetting ikke skjuler endret produksjonskode."""
import json
from pathlib import Path
import hd_figurer_aktiver as gate

code = (gate.ROOT/'web/src/hd.js').read_bytes().replace(b'</script', b'<\\/script')
html_path = gate.ROOT/'art/hd-embedded-tavern-2026-10-11/verification/runtime-v9-package/moonstone.html'
html = html_path.read_bytes()
before, after = code.split(b'%%HD_MANIFEST%%')
tests = [
    ('faktisk frosset bygget HTML', gate.code_in_html(code, html)),
    ('endret kode foer manifest avvises', not gate.code_in_html(code.replace(b'const manifest', b'let manifest'), html)),
    ('endret kode etter manifest avvises', not gate.code_in_html(code.replace(b'const poser', b'let poser'), html)),
    ('tomt JSON-objekt bevarer kode', gate.code_in_html(code, before+b'{}'+after)),
    ('JSON-liste avvises', not gate.code_in_html(code, before+b'[]'+after)),
    ('ugyldig JSON avvises', not gate.code_in_html(code, before+b'{bad}'+after)),
    ('ekstra kode etter JSON avvises', not gate.code_in_html(code, before+b'{};alert(1)'+after)),
]
assert all(value for _, value in tests), tests
out = gate.ROOT/'art/hd-completion-figures-2026-10-11/verification/activation-html-gates.json'
out.write_text(json.dumps(dict(status='passed', checks=[dict(name=name, passed=value) for name, value in tests],
    html_sha256=gate.sha(html), production_hd_js_sha256=gate.sha((gate.ROOT/'web/src/hd.js').read_bytes())),
    ensure_ascii=False, indent=2)+'\n')
print(f'{len(tests)} HTML-/manifestporter bestaar.')
