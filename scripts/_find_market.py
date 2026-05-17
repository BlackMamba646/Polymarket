import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import requests

# Paginate through all active markets looking for hantavirus
offset = 0
found = []
while True:
    resp = requests.get(
        "https://gamma-api.polymarket.com/markets",
        params={"closed": "false", "active": "true", "limit": "500", "offset": str(offset)},
        timeout=15,
    )
    markets = resp.json()
    if not markets:
        break
    for m in markets:
        q = (m.get("question") or "").lower()
        desc = (m.get("description") or "").lower()
        if "hanta" in q or "hanta" in desc:
            found.append(m)
    print(f"Checked offset {offset}, batch size {len(markets)}, found so far: {len(found)}")
    offset += len(markets)
    if len(markets) < 500:
        break

print(f"\nTotal hantavirus matches: {len(found)}")
for m in found:
    print("---")
    print("Question:", m.get("question"))
    print("Condition ID:", m.get("conditionId"))
    tokens_raw = m.get("clobTokenIds")
    if isinstance(tokens_raw, str):
        tokens = json.loads(tokens_raw)
    else:
        tokens = tokens_raw
    print("Tokens:", tokens)
    print("Active:", m.get("active"), "Closed:", m.get("closed"))
