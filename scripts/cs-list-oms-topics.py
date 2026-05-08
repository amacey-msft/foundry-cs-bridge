"""List OMS bot's topics for reference."""
import importlib.util, requests

spec = importlib.util.spec_from_file_location("p", "scripts/cs-provision-tools.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tok = m.az_token(m.ORG_URL)
flt = "_parentbotid_value eq 757c2a0a-22dc-4c44-b3e6-b91da31554ea and componenttype eq 9"
r = requests.get(
    f"{m.API}/botcomponents",
    params={"$filter": flt, "$select": "name,schemaname,botcomponentid", "$top": "50"},
    headers=m.headers(tok, prefer_return=False),
    timeout=30,
)
for x in r.json().get("value", []):
    print(x["botcomponentid"], "|", x["schemaname"], "|", x["name"])
