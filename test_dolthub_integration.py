"""
Test script for DoltHub integration.

This script verifies that:
1. DoltHub adapter can connect to the database
2. Data can be loaded successfully
3. Market data can be created with vol surfaces
4. Backtests can run with real data
"""

import pandas as pd
import numpy as np
from pathlib import Path

from backtester import (
    DoltHubAdapter,
    MarketDataLoader,
    IronCondorStrategy,
    BacktestEngine,
    BacktestConfig,
    BlackScholesModel,
    PerformanceMetrics
)


def test_adapter_connection():
    """Test 1: Verify database connection."""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)

    db_path = "/Users/janussuk/Desktop/dolt_data/options"

    try:
        adapter = DoltHubAdapter(db_path)
        print(f"✓ Successfully connected to database at {db_path}")
        return adapter
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return None


def test_load_option_data(adapter):
    """Test 2: Load option chain data."""
    print("\n" + "="*60)
    print("TEST 2: Load Option Data")
    print("="*60)

    try:
        options = adapter.load_option_data(
            ticker="AAPL",
            start_date="2024-01-03",
            end_date="2024-01-03"
        )

        print(f"✓ Loaded {len(options)} option records")
        print(f"  Columns: {list(options.columns)}")
        print(f"\nSample data:")
        print(options.head(3))
        return True
    except Exception as e:
        print(f"✗ Failed to load options: {e}")
        return False


def test_load_vol_data(adapter):
    """Test 3: Load volatility history."""
    print("\n" + "="*60)
    print("TEST 3: Load Volatility Data")
    print("="*60)

    try:
        vol_data = adapter.load_volatility_data(
            ticker="AAPL",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        print(f"✓ Loaded {len(vol_data)} days of volatility data")
        if not vol_data.empty:
            print(f"\nSample:")
            print(vol_data.head(3)[['date', 'hv_current', 'iv_current']])
        return True
    except Exception as e:
        print(f"✗ Failed to load volatility: {e}")
        return False


def test_market_data_loader(adapter):
    """Test 4: Create MarketData with vol surfaces."""
    print("\n" + "="*60)
    print("TEST 4: Market Data Loader")
    print("="*60)

    try:
        loader = MarketDataLoader(adapter)

        market_data = loader.load(
            ticker="SPY",
            start_date="2024-01-01",
            end_date="2024-01-31",
            build_vol_surface=True
        )

        print(f"\n✓ Market data created successfully")
        print(f"  Spot data points: {len(market_data.time_index)}")
        print(f"  Volatility surfaces: {len(market_data.vol_surfaces)}")

        # Test surface
        test_date = pd.Timestamp("2024-01-15")
        spot = market_data.get_spot(test_date)
        strike = spot * 1.05
        expiry = test_date + pd.Timedelta(days=30)

        iv = market_data.get_implied_vol(test_date, strike, expiry, spot)
        print(f"\n  Test surface query:")
        print(f"    Date: {test_date.date()}")
        print(f"    Spot: ${spot:.2f}")
        print(f"    Strike: ${strike:.2f}")
        print(f"    Implied Vol: {iv:.2%}")

        return market_data
    except Exception as e:
        print(f"✗ Failed to create market data: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_backtest(market_data):
    """Test 5: Run a simple backtest."""
    print("\n" + "="*60)
    print("TEST 5: Backtest Execution")
    print("="*60)

    if market_data is None:
        print("✗ Skipping backtest (no market data)")
        return False

    try:
        # Create simple iron condor
        entry_date = pd.Timestamp("2024-01-03")
        spot = market_data.get_spot(entry_date)
        expiry = entry_date + pd.Timedelta(days=30)

        strategy = IronCondorStrategy(
            underlying="SPY",
            put_lower_strike=spot * 0.95,
            put_upper_strike=spot * 0.98,
            call_lower_strike=spot * 1.02,
            call_upper_strike=spot * 1.05,
            expiry=expiry,
            quantity=1.0
        )

        print(f"\nStrategy: {strategy.name}")
        print(f"Entry date: {entry_date.date()}")
        print(f"Expiry: {expiry.date()}")

        # Configure backtest
        config = BacktestConfig(
            start_date=entry_date,
            end_date=min(expiry, market_data.time_index[-1]),
            initial_capital=100000.0,
            model=BlackScholesModel(use_market_iv=True)
        )

        # Run backtest
        engine = BacktestEngine(market_data, config)
        engine.add_strategy(strategy, entry_date=entry_date)
        results = engine.run()

        # Show results
        print(f"\n✓ Backtest completed successfully")
        print(f"  Days simulated: {len(results)}")
        print(f"  Final portfolio value: ${results['portfolio_value'].iloc[-1]:,.2f}")
        print(f"  Total return: {results['total_return'].iloc[-1]:.2%}")

        # Quick metrics
        metrics = PerformanceMetrics(results)
        print(f"\n  Performance Summary:")
        print(f"    Sharpe Ratio: {metrics.sharpe_ratio():.3f}")
        max_dd = metrics.max_drawdown()
        if isinstance(max_dd, tuple):
            max_dd = max_dd[0]  # Get the drawdown value
        print(f"    Max Drawdown: {max_dd:.2%}")
        print(f"    Win Rate: {metrics.win_rate():.2%}")

        return True
    except Exception as e:
        print(f"✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# DoltHub Integration Test Suite")
    print("#"*60)

    results = {
        'connection': False,
        'option_data': False,
        'vol_data': False,
        'market_data': False,
        'backtest': False
    }

    # Test 1: Connection
    adapter = test_adapter_connection()
    results['connection'] = adapter is not None

    if not adapter:
        print("\n✗ Cannot proceed without database connection")
        return results

    # Test 2: Load option data
    results['option_data'] = test_load_option_data(adapter)

    # Test 3: Load volatility data
    results['vol_data'] = test_load_vol_data(adapter)

    # Test 4: Create market data
    market_data = test_market_data_loader(adapter)
    results['market_data'] = market_data is not None

    # Test 5: Run backtest
    results['backtest'] = test_backtest(market_data)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:20s}: {status}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("\n🎉 All tests passed! The DoltHub integration is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - total_passed} test(s) failed. Please check the errors above.")

    return results


if __name__ == "__main__":
    main()
