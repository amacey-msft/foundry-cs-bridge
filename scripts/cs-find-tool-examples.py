"""Find MCP/Connector tool examples to crib YAML pattern from."""
import importlib.util, requests

spec = importlib.util.spec_from_file_location("p", "scripts/cs-provision-tools.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
tok = m.az_token(m.ORG_URL)

for label, term in (("MCP", "InvokeMCP"), ("Connector", "InvokeConnector"), ("Flow", "InvokeFlow"), ("Skill", "InvokeSkill")):
    flt = f"componenttype eq 9 and contains(data,'{term}')"
    r = requests.get(
        f"{m.API}/botcomponents",
        params={"$filter": flt, "$select": "name,schemaname,botcomponentid", "$top": "5"},
        headers=m.headers(tok, prefer_return=False),
        timeout=30,
    )
    print(f"=== {label} ===")
    for x in r.json().get("value", []):
        print(" ", x["botcomponentid"], "|", x["schemaname"], "|", x["name"])
