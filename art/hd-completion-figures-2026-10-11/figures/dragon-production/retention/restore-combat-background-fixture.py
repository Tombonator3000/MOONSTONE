"""Gjenopprett den frosne originalkilde-fixturen uten aa endre den."""
from pathlib import Path
import gzip
import hashlib

base = Path(__file__).resolve().parent
raw = gzip.decompress((base / "combat-background-fixture-input.json.gz").read_bytes())
assert hashlib.sha256(raw).hexdigest() == "d503998d637fa0125bbb3b25ac139879e74491981118846adc0d7c99a385e1df", "Endret kildefixtur"
target = base / "combat-background-fixture-input.json"
if target.exists():
    assert target.read_bytes() == raw, "En annen fixtur finnes allerede"
else:
    target.write_bytes(raw)
print("Frosset kildefixtur klar:", target)
