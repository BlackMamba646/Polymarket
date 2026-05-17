# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Python bot that copy-trades Polymarket prediction markets. It monitors target traders via Supabase Realtime subscriptions and polling threads, then places scaled orders through the Polymarket CLOB API.

## Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt

# Run the bot (from repo root — scripts/ uses relative imports via sys.path)
cd scripts && python main.py

# Validate config without starting the bot
python scripts/config.py

# Run all tests
pytest tests/ -v

# Run a single test
pytest tests/test_logic.py::test_sizing_constraints -v
```

## Architecture

### Data Flow

Polymarket Data API -> polling threads write to Supabase -> Supabase Realtime fires callbacks -> sizing + risk checks -> `make_order` hits CLOB API.

Two polling daemon threads in `main.py` (`_start_polling_threads`) continuously fetch from the Polymarket Data API:
- **History poller** (10s interval): `get_player_history_new.fetch_activities` -> upserts into `historic_trades`
- **Position poller** (5m interval): `get_player_positions.fetch_player_positions` -> upserts into `polymarket_positions`

Three async Supabase Realtime listeners react to DB changes:
- `listen_to_trades` (INSERT on `historic_trades`) -> `handle_new_trade`
- `listen_to_positions` (INSERT on `polymarket_positions`) -> `handle_new_position`
- `listen_to_updates` (UPDATE on `polymarket_positions`) -> `handle_update_position`

### Order Pipeline

`handle_new_trade` follows the full pipeline: **filter by target wallet -> size the trade -> check risk constraints -> claim idempotency lock -> place order -> mark result**.

`handle_new_position` and `handle_update_position` skip the `claim_trade` step — they have no idempotency protection against replays. Only `handle_new_trade` is fully idempotent.

- `constraints/sizing.py`: Scales trader's USDC size by `STAKE_WHALE_PCT`, rejects below `STAKE_MIN` (does NOT inflate to floor), caps at `STAKE_MAX`.
- `constraints/risk_manager.py`: Enforces total exposure <= bankroll, per-market <= 20%, per-trader <= 40%.
- `copied_trades.py`: Idempotency ledger — `claim_trade` inserts into `copied_trades` table; UNIQUE violation means replay, so the order is skipped. Fail-closed on DB errors.
- `make_orders.py`: Singleton `ClobClient`, retry with exponential backoff, slippage protection, dry-run mode.

### SELL / Update Logic

**SELL from trade event** (`handle_new_trade`): Proportional to the trader's position — calculates what percentage of the trader's position is being sold, sells the same percentage of the bot's own position.

**`handle_update_position`**: Detects position value changes (ignores deltas < $1):
- Positive delta (position grew) -> BUY the sized delta amount
- Negative delta (position shrank) -> SELL proportionally: `(old_size - new_size) / old_size * my_current_size`

### Risk Check Data Source

`get_current_exposures` fetches bot exposure live from the Polymarket Data API (not Supabase), so risk checks always reflect current on-chain state but add an extra API call per BUY trade. `trader_exposure` reads from the `copied_trades` ledger in Supabase (upper bound — doesn't reconcile SELLs).

### Configuration

All config is centralized in `config.py` as a singleton `Config` class loaded from `.env`. Key settings:
- `TRADER_WALLET`: comma-separated list of wallets to copy (stored lowercase in `TRADER_WALLETS`)
- `DRY_RUN`: defaults to `True` — orders are logged but not placed
- `BANKROLL`, `STAKE_MIN`, `STAKE_MAX`, `STAKE_WHALE_PCT`: sizing parameters
- `MAX_RETRY_ATTEMPTS`, `RETRY_BACKOFF_FACTOR`, `DEFAULT_SLIPPAGE`: order reliability
- `LOG_LEVEL`: passed to the logger (default `INFO`)
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`: optional Telegram alerts via `notifier.py`

### Database (Supabase)

Three tables defined in `supabase/create_table.sql`:
- `historic_trades`: deduped via generated `unique_activity_key` column
- `polymarket_positions`: composite PK `(proxy_wallet, asset)`
- `copied_trades`: idempotency ledger, PK on `transaction_hash`

Realtime must be manually enabled on `historic_trades` and `polymarket_positions` in the Supabase dashboard.

### Utility / Diagnostic Scripts

The `scripts/_*.py` files are standalone operational tools (run directly, not imported by the bot):
- `_check_realtime.py`: Inserts a test row and verifies Supabase Realtime delivers the callback
- `_check_supabase.py`: Validates DB connectivity and table access
- `_check_wallet.py`: Inspects bot wallet balance and open positions
- `_find_market.py`: Searches Polymarket for a market by keyword
- `_place_order.py`: Places a single manual order
- `_close_position.py`: Closes a specific open position
- `_close_gta.py`: Closes positions matching a specific condition

## Testing

Tests use `unittest.mock` to patch `config.get_config` **before** importing modules (necessary because config is loaded at module scope). Follow this pattern when adding new tests:

```python
mock_config_obj = MagicMock()
mock_config_obj.SOME_SETTING = value
with patch('config.get_config', return_value=mock_config_obj):
    from module_under_test import function
```

`test_logic.py` covers sizing and risk manager unit tests. `test_integration.py` covers the full trade handler flow with mocked externals.

## Important Gotchas

- All scripts expect to be run from `scripts/` directory (or with `scripts/` on `sys.path`) because they use bare imports like `from config import get_config`.
- The Supabase client in `copied_trades.py` and the polling modules is synchronous (`create_client`), while `main.py` listeners use the async client (`acreate_client`). Don't mix them.
- `get_player_positions.py` transforms camelCase API fields to snake_case DB columns. The handlers read snake_case keys from Supabase payloads, not camelCase.
- Risk manager thresholds (`MAX_SINGLE_MARKET_EXPOSURE_PCT`, `MAX_TRADER_EXPOSURE_PCT`) are hardcoded constants in `risk_manager.py`, not env vars.
- `get_player_history_new.py` uses `print()` instead of `logger` — its output won't appear in structured log aggregation.
