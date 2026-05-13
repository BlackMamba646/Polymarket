import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Create a mock config object
mock_config_obj = MagicMock()
mock_config_obj.STAKE_WHALE_PCT = 0.30
mock_config_obj.STAKE_MIN = 0.0
mock_config_obj.STAKE_MAX = 50.0
mock_config_obj.BANKROLL = 1000.0
mock_config_obj.LOG_LEVEL = "INFO"

# Patch config.get_config BEFORE importing other modules
with patch('config.get_config', return_value=mock_config_obj):
    # Now we can import the modules that depend on config
    from constraints.sizing import sizing_constraints
    from constraints.risk_manager import check_risk_constraints

def test_sizing_constraints():
    with patch('constraints.sizing.config', mock_config_obj):
        # 30% of 100 = 30, within max
        assert sizing_constraints(100) == 30.0
        # 30% of 200 = 60, capped at STAKE_MAX (50)
        assert sizing_constraints(200) == 50.0
        # 30% of 0.10 = 0.03, no minimum so it passes
        assert sizing_constraints(0.10) == 0.03
        # 30% of 10 = 3.0
        assert sizing_constraints(10) == 3.0

def test_risk_manager_total_exposure():
    with patch('constraints.risk_manager.config', mock_config_obj):
        # Current 900 + new 50 = 950 (OK)
        assert check_risk_constraints(current_exposure=900, order_value=50) is True
        
        # Current 980 + new 50 = 1030 (Too much)
        assert check_risk_constraints(current_exposure=980, order_value=50) is False

def test_risk_manager_market_exposure():
    with patch('constraints.risk_manager.config', mock_config_obj):
        # Bankroll 1000, max market exposure 20% = 200
        # Current market 180 + new 10 = 190 (OK)
        assert check_risk_constraints(current_exposure=200, order_value=10, market_exposure=180) is True
        
        # Current market 195 + new 10 = 205 (Too much)
        assert check_risk_constraints(current_exposure=200, order_value=10, market_exposure=195) is False
