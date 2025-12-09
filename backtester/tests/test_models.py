"""
Unit tests for pricing models and Greeks calculations.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from backtester.models import BlackScholesModel, BachelierModel
from backtester.instruments import OptionContract
from backtester.data import MarketData, VolSurface


class TestBlackScholesModel:
    """Tests for Black-Scholes pricing model."""

    @pytest.fixture
    def setup_data(self):
        """Set up test data."""
        # Create simple market data
        dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
        spot_data = pd.DataFrame({
            'close': [100.0] * len(dates)
        }, index=dates)

        # Create vol surface
        strikes = np.linspace(80, 120, 10)
        expiries = [30, 60, 90]
        vol_df = pd.DataFrame([
            {'strike': s, 'expiry': e, 'implied_vol': 0.20}
            for s in strikes for e in expiries
        ])

        vol_surface = VolSurface(
            date=pd.Timestamp('2024-01-01'),
            underlying='TEST',
            vol_data=vol_df
        )

        market_data = MarketData(
            spot_data=spot_data,
            vol_surfaces={pd.Timestamp('2024-01-01'): vol_surface},
            underlying='TEST'
        )

        return market_data

    def test_call_price_at_expiry(self, setup_data):
        """Test that call price equals intrinsic value at expiry."""
        model = BlackScholesModel(use_market_iv=True)

        # Create ATM call expiring today
        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=pd.Timestamp('2024-01-01')
        )

        price = model.price(option, pd.Timestamp('2024-01-01'), setup_data)

        # At expiry, price should equal intrinsic value (0 for ATM)
        assert abs(price) < 0.01, "Call price at expiry should be close to intrinsic value"

    def test_put_call_parity(self, setup_data):
        """Test put-call parity holds."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        strike = 100.0
        expiry = pd.Timestamp('2024-02-01')

        # Create call and put
        call = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=strike,
            expiry=expiry
        )

        put = OptionContract(
            underlying='TEST',
            option_type='put',
            strike=strike,
            expiry=expiry
        )

        call_price = model.price(call, date, setup_data)
        put_price = model.price(put, date, setup_data)

        S = setup_data.get_spot(date)
        K = strike
        r = setup_data.get_rate(date, expiry)
        q = setup_data.get_dividend_yield(date, expiry)
        T = (expiry - date).days / 365.0

        # Put-call parity: C - P = S*e^(-qT) - K*e^(-rT)
        lhs = call_price - put_price
        rhs = S * np.exp(-q * T) - K * np.exp(-r * T)

        assert abs(lhs - rhs) < 0.01, f"Put-call parity violated: {lhs} != {rhs}"

    def test_delta_range(self, setup_data):
        """Test that delta is in valid range."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        # Test call delta
        call = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=expiry
        )

        greeks = model.greeks(call, date, setup_data)

        assert 0 <= greeks['delta'] <= 1, f"Call delta {greeks['delta']} not in [0, 1]"

        # Test put delta
        put = OptionContract(
            underlying='TEST',
            option_type='put',
            strike=100.0,
            expiry=expiry
        )

        greeks = model.greeks(put, date, setup_data)

        assert -1 <= greeks['delta'] <= 0, f"Put delta {greeks['delta']} not in [-1, 0]"

    def test_gamma_positive(self, setup_data):
        """Test that gamma is always positive."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=expiry
        )

        greeks = model.greeks(option, date, setup_data)

        assert greeks['gamma'] >= 0, f"Gamma should be positive: {greeks['gamma']}"

    def test_vega_positive(self, setup_data):
        """Test that vega is positive for long options."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=expiry
        )

        greeks = model.greeks(option, date, setup_data)

        assert greeks['vega'] >= 0, f"Vega should be positive: {greeks['vega']}"

    def test_theta_negative_for_long_call(self, setup_data):
        """Test that theta is negative for long calls (time decay)."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=expiry
        )

        greeks = model.greeks(option, date, setup_data)

        # Theta should be negative for long options (they lose value over time)
        # Note: Convention varies; some use negative for decay
        assert greeks['theta'] <= 0, f"Theta should be negative for long call: {greeks['theta']}"

    def test_itm_call_delta_near_one(self, setup_data):
        """Test that deep ITM call has delta near 1."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        # Deep ITM call (strike much below spot)
        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=80.0,  # Spot is 100
            expiry=expiry
        )

        greeks = model.greeks(option, date, setup_data)

        assert greeks['delta'] > 0.9, f"Deep ITM call delta should be near 1: {greeks['delta']}"

    def test_otm_call_delta_near_zero(self, setup_data):
        """Test that deep OTM call has delta near 0."""
        model = BlackScholesModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        # Deep OTM call (strike much above spot)
        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=120.0,  # Spot is 100
            expiry=expiry
        )

        greeks = model.greeks(option, date, setup_data)

        assert greeks['delta'] < 0.1, f"Deep OTM call delta should be near 0: {greeks['delta']}"


class TestBachelierModel:
    """Tests for Bachelier pricing model."""

    @pytest.fixture
    def setup_data(self):
        """Set up test data."""
        dates = pd.date_range('2024-01-01', '2024-01-10', freq='D')
        spot_data = pd.DataFrame({
            'close': [100.0] * len(dates)
        }, index=dates)

        strikes = np.linspace(80, 120, 10)
        expiries = [30, 60, 90]
        vol_df = pd.DataFrame([
            {'strike': s, 'expiry': e, 'implied_vol': 0.20}
            for s in strikes for e in expiries
        ])

        vol_surface = VolSurface(
            date=pd.Timestamp('2024-01-01'),
            underlying='TEST',
            vol_data=vol_df
        )

        market_data = MarketData(
            spot_data=spot_data,
            vol_surfaces={pd.Timestamp('2024-01-01'): vol_surface},
            underlying='TEST'
        )

        return market_data

    def test_bachelier_positive_price(self, setup_data):
        """Test that Bachelier model produces positive prices."""
        model = BachelierModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=expiry
        )

        price = model.price(option, date, setup_data)

        assert price >= 0, f"Bachelier price should be non-negative: {price}"

    def test_bachelier_greeks_exist(self, setup_data):
        """Test that Bachelier model calculates all Greeks."""
        model = BachelierModel(use_market_iv=True)

        date = pd.Timestamp('2024-01-01')
        expiry = pd.Timestamp('2024-02-01')

        option = OptionContract(
            underlying='TEST',
            option_type='call',
            strike=100.0,
            expiry=expiry
        )

        greeks = model.greeks(option, date, setup_data)

        required_greeks = ['delta', 'gamma', 'vega', 'theta', 'rho']

        for greek in required_greeks:
            assert greek in greeks, f"Missing Greek: {greek}"
            assert isinstance(greeks[greek], (int, float)), f"Greek {greek} is not numeric"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
