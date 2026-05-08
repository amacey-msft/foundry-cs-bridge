"""Inspect Granite Peak bot record for orchestration / classifier fields."""
import importlib.util, requests

spec = importlib.util.spec_from_file_location("p", "scripts/cs-provision-tools.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tok = m.az_token(m.ORG_URL)
r = requests.get(
    f"{m.API}/bots(b6159d14-2485-4369-b65c-dafde20997d3)",
    headers=m.headers(tok, prefer_return=False),
    timeout=30,
)
b = r.json()
for k, v in sorted(b.items()):
    kl = k.lower()
    if any(x in kl for x in ("orches", "generat", "intent", "llm", "classif", "dispatch", "grounding", "knowledge", "contentmod", "boost", "auth", "config")):
        print(k, "=", v)
