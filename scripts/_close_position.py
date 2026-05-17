import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from py_clob_client_v2.client import ClobClient
from py_clob_client_v2.clob_types import OrderArgsV2, OrderType
from py_clob_client_v2.order_builder.constants import SELL
from config import get_config

config = get_config()

TOKEN_ID = "8441400852834915183759801017793514978104486628517653995211751018945988243154"
PRICE = 0.01      # sell at $0.01 — will match any buyer
SIZE = 55.0       # sell all 55 shares we bought

print("\n=== CLOSING POSITION ===")
print("Market: GTA VI released before June 2026?")
print(f"Side: SELL YES @ ${PRICE}")
print(f"Size: {SIZE} shares")

client = ClobClient(
    config.CLOB_API_URL,
    key=config.PRIVATE_KEY,
    chain_id=config.POLY_CHAIN_ID,
    signature_type=3,
    funder=config.POLY_FUNDER,
)
client.set_api_creds(client.create_or_derive_api_key())

order_args = OrderArgsV2(price=PRICE, size=SIZE, side=SELL, token_id=TOKEN_ID)
signed_order = client.create_order(order_args)
resp = client.post_order(signed_order, OrderType.GTC)
print(f"Response: {resp}")

if resp and resp.get("success"):
    print(f"\nPOSITION CLOSED — Order ID: {resp.get('orderID')}")
else:
    print(f"\nFAILED — {resp}")
