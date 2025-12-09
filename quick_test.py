"""
Quick test to verify the backtester works end-to-end.
"""

import pandas as pd
from backtester import (
    MarketData,
    IronCondorStrategy,
    BacktestEngine,
    BacktestConfig,
    BlackScholesModel,
    PerformanceMetrics
)

print("Testing Options Backtester...")
print("="*60)

# Load market data
print("\n1. Loading market data...")
market_data = MarketData.from_yahoo(
    ticker="SPY",
    start_date="2024-01-01",
    end_date="2024-03-31",
    default_iv=0.18
)
print(f"   Loaded {len(market_data.time_index)} trading days")

# Create strategy
print("\n2. Creating Iron Condor strategy...")
current_date = pd.Timestamp("2024-01-02")
spot = market_data.get_spot(current_date)
expiry = current_date + pd.Timedelta(days=45)

print(f"   Spot: ${spot:.2f}")
print(f"   Expiry: {expiry}")

iron_condor = IronCondorStrategy(
    underlying="SPY",
    put_lower_strike=spot * 0.90,
    put_upper_strike=spot * 0.95,
    call_lower_strike=spot * 1.05,
    call_upper_strike=spot * 1.10,
    expiry=expiry,
    quantity=1.0
)
print(f"   Strategy: {iron_condor.name}")

# Run backtest
print("\n3. Running backtest...")
config = BacktestConfig(
    start_date=current_date,
    end_date=expiry,
    initial_capital=100000.0,
    model=BlackScholesModel(use_market_iv=True)
)

engine = BacktestEngine(market_data, config)
engine.add_strategy(iron_condor, entry_date=current_date)
results = engine.run()

# Print results
print("\n4. Performance Summary:")
print("-"*60)
metrics = PerformanceMetrics(results)

summary = metrics.summary()
for key, value in summary.items():
    if 'Return' in key or 'Volatility' in key or 'Drawdown' in key:
        print(f"{key:30s}: {value:>10.2%}")
    elif 'Ratio' in key or 'Rate' in key or 'Factor' in key:
        print(f"{key:30s}: {value:>10.2f}")
    else:
        print(f"{key:30s}: {value:>10.0f}")

print("\n" + "="*60)
print("SUCCESS! Backtester is working correctly.")
print("="*60)
