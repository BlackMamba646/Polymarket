import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import requests
from datetime import datetime
from config import get_config

config = get_config()

wallet = config.TRADER_WALLETS[0]
print(f"Target wallet: {wallet}")
print(f"Total wallets tracked: {len(config.TRADER_WALLETS)}")

# Check recent trades
print("\n=== RECENT TRADES (Activity API) ===")
resp = requests.get(
    "https://data-api.polymarket.com/activity",
    params={"user": wallet, "limit": "5", "sortBy": "TIMESTAMP", "sortDirection": "DESC"},
    timeout=10,
)
activities = resp.json()
print(f"Fetched {len(activities)} recent activities")
for a in activities:
    ts = a.get("timestamp", 0)
    dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"
    print(f"  [{dt}] {a.get('side')} | {a.get('title', 'N/A')[:50]} | ${a.get('usdcSize', 0)} | tx: {(a.get('transactionHash') or 'N/A')[:16]}...")

# Check positions
print("\n=== CURRENT POSITIONS (Positions API) ===")
resp2 = requests.get(
    "https://data-api.polymarket.com/positions",
    params={"user": wallet, "limit": "5", "sortBy": "INITIAL", "sortDirection": "DESC"},
    timeout=10,
)
positions = resp2.json()
print(f"Fetched {len(positions)} positions")
for p in positions:
    print(f"  {p.get('title', 'N/A')[:50]} | {p.get('outcome')} | Size: {p.get('size')} | Value: ${p.get('currentValue', 0)}")
