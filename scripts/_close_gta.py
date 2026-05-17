import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from py_clob_client_v2.client import ClobClient
from py_clob_client_v2.clob_types import OrderArgsV2, OrderType
from py_clob_client_v2.order_builder.constants import SELL
from config import get_config

config = get_config()

TOKEN_ID = "8441400852834915183759801017793514978104486628517653995211751018945988243154"

client = ClobClient(
    config.CLOB_API_URL,
    key=config.PRIVATE_KEY,
    chain_id=config.POLY_CHAIN_ID,
    signature_type=3,
    funder=config.POLY_FUNDER,
)
client.set_api_creds(client.create_or_derive_api_key())

# Step 1: Cancel all open orders first
print("[1] Cancelling all open orders...")
try:
    cancel_resp = client.cancel_all()
    print(f"  Cancel response: {cancel_resp}")
except Exception as e:
    print(f"  Cancel error: {e}")

# Step 2: Check order book for the best bid
print("\n[2] Checking order book...")
try:
    book = client.get_order_book(TOKEN_ID)
    bids = book.bids if book and book.bids else []
    asks = book.asks if book and book.asks else []
    print(f"  Bids: {len(bids)}, Asks: {len(asks)}")
    if bids:
        best_bid = bids[0]
        print(f"  Best bid: ${best_bid.price} x {best_bid.size}")
    else:
        print("  No bids on book")
except Exception as e:
    print(f"  Order book error: {e}")
    bids = []

# Step 3: Sell at the best bid price (or $0.01 if no bids)
sell_price = float(bids[0].price) if bids else 0.01
print(f"\n[3] Selling 55 shares at ${sell_price}...")
order_args = OrderArgsV2(price=sell_price, size=55.0, side=SELL, token_id=TOKEN_ID)
signed_order = client.create_order(order_args)
resp = client.post_order(signed_order, OrderType.GTC)
print(f"  Response: {resp}")

if resp and resp.get("success"):
    status = resp.get("status")
    print(f"\n  Order {status} — ID: {resp.get('orderID')}")
    if status == "matched":
        print("  Position fully closed!")
    else:
        print("  Order is live on the book, waiting for a buyer.")
else:
    print(f"\n  FAILED: {resp}")
