import sys, asyncio
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from supabase import create_client, acreate_client
from config import get_config

config = get_config()

# Check via sync client if we can query the realtime publication
sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

print("=== Checking Supabase Realtime Config ===\n")

# Try to query the pg publication tables (requires service role key usually)
# Instead, let's just test if realtime actually delivers events
print("Testing realtime by inserting a dummy row and listening for the callback...\n")

got_callback = False

async def test_realtime():
    global got_callback
    client = await acreate_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    def on_insert(payload):
        global got_callback
        got_callback = True
        print(f"  CALLBACK RECEIVED: {payload}")

    print("[1] Subscribing to historic_trades INSERT...")
    channel = client.channel("test-realtime")
    channel.on_postgres_changes(
        "INSERT", schema="public", table=config.TABLE_NAME_TRADES, callback=on_insert
    )
    await channel.subscribe()
    print("  Subscribed. Waiting 5 seconds for any existing events...")
    await asyncio.sleep(5)

    # Now insert a test row
    print("[2] Inserting a test trade row...")
    sync_sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    test_row = {
        "proxy_wallet": "0x0000000000000000000000000000000000000000",
        "timestamp": 1,
        "activity_datetime": "2000-01-01T00:00:00",
        "condition_id": "test_realtime_check",
        "type": "test",
        "size": "0",
        "usdc_size": "0",
        "transaction_hash": "0x_realtime_test_" + str(int(__import__("time").time())),
        "price": "0",
        "asset": "test",
        "side": "BUY",
        "outcome_index": "0",
        "title": "REALTIME TEST - DELETE ME",
    }
    try:
        sync_sb.table(config.TABLE_NAME_TRADES).insert(test_row).execute()
        print("  Inserted test row.")
    except Exception as e:
        print(f"  Insert error (may be duplicate): {e}")

    print("[3] Waiting 10 seconds for realtime callback...")
    await asyncio.sleep(10)

    if got_callback:
        print("\n  REALTIME IS WORKING - callback received!")
    else:
        print("\n  NO CALLBACK RECEIVED - Realtime is NOT enabled on this table!")
        print("  Go to Supabase Dashboard -> Database -> Replication")
        print("  Enable the table 'historic_trades' and 'polymarket_positions' for Realtime.")

    # Clean up test row
    try:
        sync_sb.table(config.TABLE_NAME_TRADES).delete().eq(
            "transaction_hash", test_row["transaction_hash"]
        ).execute()
        print("  (cleaned up test row)")
    except:
        pass

asyncio.run(test_realtime())
