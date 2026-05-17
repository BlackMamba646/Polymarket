import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from py_clob_client_v2.client import ClobClient
from py_clob_client_v2.clob_types import OrderArgsV2, OrderType
from py_clob_client_v2.order_builder.constants import BUY
from config import get_config

config = get_config()

# GTA VI released before June 2026? — YES token
TOKEN_ID = "8441400852834915183759801017793514978104486628517653995211751018945988243154"
PRICE = 0.02      # very low limit — stays on the book
SIZE = 55.0       # $1.10 total to clear $1 minimum

print("\n=== PLACING LIVE ORDER ===")
print("Market: GTA VI released before June 2026?")
print(f"Side: BUY YES @ ${PRICE}")
print(f"Size: {SIZE} units (${PRICE * SIZE:.2f} total risk)")

# Init client
print("\n[1/3] Initializing CLOB client (signature_type=3)...")
client = ClobClient(
    config.CLOB_API_URL,
    key=config.PRIVATE_KEY,
    chain_id=config.POLY_CHAIN_ID,
    signature_type=3,
    funder=config.POLY_FUNDER,
)
client.set_api_creds(client.create_or_derive_api_key())
print("  OK")

# Create & sign
print("[2/3] Creating and signing order...")
order_args = OrderArgsV2(price=PRICE, size=SIZE, side=BUY, token_id=TOKEN_ID)
signed_order = client.create_order(order_args)
print("  OK")

# Post
print("[3/3] Posting order (GTC)...")
resp = client.post_order(signed_order, OrderType.GTC)
print(f"  Response: {resp}")

if resp and resp.get("success"):
    print(f"\n  ORDER PLACED — ID: {resp.get('orderID')}")
    print("  This is a live limit order. Check your Polymarket portfolio to see it.")
else:
    print(f"\n  ORDER FAILED — {resp}")
