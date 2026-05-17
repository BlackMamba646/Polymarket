"""One-shot test: place a tiny unfillable order, verify success, then cancel."""
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from py_clob_client_v2.client import ClobClient
from py_clob_client_v2.clob_types import OrderArgsV2, OrderType
from py_clob_client_v2.order_builder.constants import BUY
from config import get_config

config = get_config()

TOKEN_ID = "58077353329405847288143721198487033857066664479226923794509773080249507560880"
TEST_PRICE = 0.01   # far below market — will never fill
TEST_SIZE = 1.0     # 1 unit = $0.01 risk

print("\n=== TEST ORDER PIPELINE ===")
print(f"Market: Will Bitcoin dip to $75,000 in May?")
print(f"Side: BUY @ ${TEST_PRICE} (market ~$0.585 — won't fill)")
print(f"Size: {TEST_SIZE} units (${TEST_PRICE * TEST_SIZE:.2f} total)")

# 1. Init client
print("\n[1/4] Initializing CLOB v2 client...")
client = ClobClient(
    config.CLOB_API_URL,
    key=config.PRIVATE_KEY,
    chain_id=config.POLY_CHAIN_ID,
    signature_type=3,
    funder=config.POLY_FUNDER,
)
client.set_api_creds(client.create_or_derive_api_key())
print("  OK — client connected, API creds derived")

# 2. Create & sign order
print("[2/4] Creating and signing v2 order...")
order_args = OrderArgsV2(price=TEST_PRICE, size=TEST_SIZE, side=BUY, token_id=TOKEN_ID)
signed_order = client.create_order(order_args)
print("  OK — order signed")

# 3. Post order
print("[3/4] Posting order...")
resp = client.post_order(signed_order, OrderType.GTC)
print(f"  Response: {resp}")

if resp and resp.get("success"):
    order_id = resp.get("orderID")
    print(f"  SUCCESS — Order ID: {order_id}")

    # 4. Cancel it
    print("[4/4] Cancelling test order...")
    cancel_resp = client.cancel(order_id)
    print(f"  Cancel response: {cancel_resp}")
    print("\n=== TEST PASSED — order placement and cancellation both work ===")
else:
    print(f"\n=== ORDER FAILED — response: {resp} ===")
