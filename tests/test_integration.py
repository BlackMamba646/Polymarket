import asyncio
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Create a mock config object for testing
mock_config_obj = MagicMock()
mock_config_obj.LOG_LEVEL = "INFO"
mock_config_obj.SUPABASE_URL = "https://example.supabase.co"
mock_config_obj.SUPABASE_KEY = "dummy_key"
mock_config_obj.STAKE_WHALE_PCT = 0.30  # 30%
mock_config_obj.STAKE_MIN = 0.0
mock_config_obj.STAKE_MAX = 50.0
mock_config_obj.BANKROLL = 1000.0
mock_config_obj.MIN_TRADER_TRADE = 50.0
mock_config_obj.DRY_RUN = True
mock_config_obj.TRADER_WALLETS = ["0xtrader1"]
mock_config_obj.POLY_FUNDER = "0xbotwallet"
mock_config_obj.DEFAULT_SLIPPAGE = 0.01
mock_config_obj.MAX_RETRY_ATTEMPTS = 1

# Patch BEFORE importing main
with patch('config.get_config', return_value=mock_config_obj):
    from main import handle_new_trade, handle_new_position

@pytest.mark.asyncio
async def test_full_trade_flow():
    """
    Test the flow from a new trade event through sizing, risk checks, and mock execution.
    """
    # 1. Prepare a mock trade payload (similar to what Supabase sends)
    payload = {
        "data": {
            "record": {
                "proxy_wallet": "0xtrader1",
                "usdc_size": 1000,  # Trader bet 1000
                "side": "BUY",
                "asset": "0xtoken123",
                "title": "Test Market",
                "price": 0.5,
                "transaction_hash": "0xabc123"
            }
        }
    }

    # 2. Mock external dependencies inside main.py
    with patch('main.claim_trade', return_value=True), \
         patch('main.mark_trade'), \
         patch('main.make_order', return_value={"success": True, "orderID": "MOCK_ID"}) as mock_make_order:

        result = await handle_new_trade(payload)

        # 30% of $1000 = $300, capped at $50. $50 / 0.5 price = 100 units
        mock_make_order.assert_called_once()
        args, kwargs = mock_make_order.call_args
        assert kwargs['size'] == 100.0
        assert kwargs['price'] == 0.5
        assert kwargs['token_id'] == "0xtoken123"
        assert result["success"] is True


@pytest.mark.asyncio
async def test_replay_is_skipped():
    """A duplicate Realtime event must not place a second order."""
    payload = {
        "data": {
            "record": {
                "proxy_wallet": "0xtrader1",
                "usdc_size": 1000,
                "side": "BUY",
                "asset": "0xtoken123",
                "title": "Test Market",
                "price": 0.5,
                "transaction_hash": "0xreplay",
            }
        }
    }

    with patch('main.claim_trade', return_value=False), \
         patch('main.mark_trade'), \
         patch('main.make_order') as mock_make_order:

        result = await handle_new_trade(payload)
        mock_make_order.assert_not_called()
        assert result is None


@pytest.mark.asyncio
async def test_position_handler_reads_snake_case():
    """Regression: handle_new_position must read snake_case DB columns, not camelCase API field names."""
    payload = {
        "data": {
            "record": {
                "proxy_wallet": "0xtrader1",
                "asset": "0xtokenABC",
                "initial_value": 500,
                "avg_price": 0.25,
                "title": "Test Position",
            }
        }
    }

    with patch('main.make_order', return_value={"success": True, "orderID": "POS_ID"}) as mock_make_order:
        result = await handle_new_position(payload)
        mock_make_order.assert_called_once()
        kwargs = mock_make_order.call_args.kwargs
        # 30% of $500 = $150, capped at $50. $50 / 0.25 price = 200 units.
        assert kwargs['size'] == 200.0
        assert kwargs['price'] == 0.25
        assert kwargs['token_id'] == "0xtokenABC"
        assert result["success"] is True


@pytest.mark.asyncio
async def test_sell_partial_position():
    """When the trader partially sells, bot sells the same percentage of its position."""
    payload = {
        "data": {
            "record": {
                "proxy_wallet": "0xtrader1",
                "usdc_size": 25,
                "size": 50,        # trader sold 50 shares
                "side": "SELL",
                "asset": "0xtoken123",
                "title": "Test Market",
                "price": 0.5,
                "condition_id": "cond1",
                "transaction_hash": "0xsell_partial",
            }
        }
    }

    # Trader had 200 shares pre-sell (150 remaining + 50 sold)
    trader_positions = [{"size": 150}]
    bot_positions = [{"size": 80}]

    with patch('main.fetch_player_positions', side_effect=[trader_positions, bot_positions]), \
         patch('main.claim_trade', return_value=True), \
         patch('main.mark_trade'), \
         patch('main.make_order', return_value={"success": True, "orderID": "SELL1"}) as mock_order:

        result = await handle_new_trade(payload)
        mock_order.assert_called_once()
        kwargs = mock_order.call_args.kwargs
        # pre_sell = 150 + 50 = 200, pct = 50/200 = 25%, final = 80 * 0.25 = 20
        assert kwargs['size'] == pytest.approx(20.0)
        assert kwargs['side'] == "SELL"
        assert result["success"] is True


@pytest.mark.asyncio
async def test_sell_full_exit():
    """When the trader fully exits, bot sells 100% of its position."""
    payload = {
        "data": {
            "record": {
                "proxy_wallet": "0xtrader1",
                "usdc_size": 50,
                "size": 100,       # trader sold all 100 shares
                "side": "SELL",
                "asset": "0xtoken123",
                "title": "Test Market",
                "price": 0.5,
                "condition_id": "cond1",
                "transaction_hash": "0xsell_full",
            }
        }
    }

    # Trader has 0 remaining (empty from API)
    bot_positions = [{"size": 80}]

    with patch('main.fetch_player_positions', side_effect=[[], bot_positions]), \
         patch('main.claim_trade', return_value=True), \
         patch('main.mark_trade'), \
         patch('main.make_order', return_value={"success": True, "orderID": "SELL2"}) as mock_order:

        result = await handle_new_trade(payload)
        mock_order.assert_called_once()
        kwargs = mock_order.call_args.kwargs
        # Trader fully exited -> sell 100% of bot's 80 shares
        assert kwargs['size'] == pytest.approx(80.0)
        assert kwargs['side'] == "SELL"


@pytest.mark.asyncio
async def test_sell_no_bot_position():
    """When the bot has no position in this market, nothing to sell."""
    payload = {
        "data": {
            "record": {
                "proxy_wallet": "0xtrader1",
                "usdc_size": 50,
                "size": 100,
                "side": "SELL",
                "asset": "0xtoken123",
                "title": "Test Market",
                "price": 0.5,
                "condition_id": "cond1",
                "transaction_hash": "0xsell_nopos",
            }
        }
    }

    with patch('main.fetch_player_positions', side_effect=[[], []]), \
         patch('main.make_order') as mock_order:

        result = await handle_new_trade(payload)
        mock_order.assert_not_called()
        assert result is None


if __name__ == "__main__":
    asyncio.run(test_full_trade_flow())
