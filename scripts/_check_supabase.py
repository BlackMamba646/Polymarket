import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from supabase import create_client
from config import get_config

config = get_config()
sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

wallet = config.TRADER_WALLETS[0]

# Check recent trades in Supabase
print("=== SUPABASE: historic_trades (last 5) ===")
resp = sb.table(config.TABLE_NAME_TRADES).select("*").eq(
    "proxy_wallet", wallet
).order("timestamp", desc=True).limit(5).execute()

if resp.data:
    for r in resp.data:
        print(f"  [{r.get('activity_datetime')}] {r.get('side')} | {(r.get('title') or 'N/A')[:45]} | ${r.get('usdc_size')} | tx: {(r.get('transaction_hash') or '')[:16]}...")
    print(f"  ({len(resp.data)} rows returned)")
else:
    print("  NO DATA — polling may not have run yet or table is empty")

# Check positions in Supabase
print("\n=== SUPABASE: polymarket_positions (last 5) ===")
resp2 = sb.table(config.TABLE_NAME_POSITIONS).select("*").eq(
    "proxy_wallet", wallet
).order("initial_value", desc=True).limit(5).execute()

if resp2.data:
    for r in resp2.data:
        print(f"  {(r.get('title') or 'N/A')[:45]} | {r.get('outcome')} | Size: {r.get('size')} | Val: ${r.get('current_value')}")
    print(f"  ({len(resp2.data)} rows returned)")
else:
    print("  NO DATA — polling may not have run yet or table is empty")
