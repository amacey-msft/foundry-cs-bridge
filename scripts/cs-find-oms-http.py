"""Find an existing OMS-bot HTTP topic to compare YAML."""
import importlib.util, requests

spec = importlib.util.spec_from_file_location("p", "scripts/cs-provision-tools.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tok = m.az_token(m.ORG_URL)
flt = "componenttype eq 9 and contains(data,'HttpRequestAction') and contains(data,'modelDescription')"
r = requests.get(
    f"{m.API}/botcomponents",
    params={"$filter": flt, "$select": "name,schemaname,botcomponentid", "$top": "10"},
    headers=m.headers(tok, prefer_return=False),
    timeout=30,
)
for x in r.json().get("value", []):
    print(x["botcomponentid"], x["schemaname"], "|", x["name"])
