"""
Example: Iron Condor Strategy Backtest

This example demonstrates:
1. Loading market data from Yahoo Finance
2. Creating an Iron Condor strategy
3. Running a backtest
4. Analyzing performance metrics
5. Visualizing results
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import backtester modules
from backtester import (
    MarketData,
    IronCondorStrategy,
    BacktestEngine,
    BacktestConfig,
    BlackScholesModel,
    PerformanceMetrics,
    PnLAttributionEngine,
    BreakevenAnalyzer,
    VisualizationEngine
)


def main():
    """Run iron condor backtest example."""

    print("="*60)
    print("IRON CONDOR STRATEGY BACKTEST EXAMPLE")
    print("="*60)

    # 1. Load market data
    print("\n1. Loading market data from Yahoo Finance...")

    ticker = "SPY"
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    market_data = MarketData.from_yahoo(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        default_iv=0.18  # 18% implied volatility
    )

    print(f"   Loaded {len(market_data.time_index)} trading days of data")
    print(f"   Price range: ${market_data.spot_data['close'].min():.2f} - ${market_data.spot_data['close'].max():.2f}")

    # 2. Create Iron Condor strategy
    print("\n2. Creating Iron Condor strategy...")

    # Get current spot price
    current_date = pd.Timestamp(start_date)
    spot = market_data.get_spot(current_date)

    print(f"   Current spot: ${spot:.2f}")

    # Set up strikes (typically 1 standard deviation OTM on each side)
    # For simplicity, use ±5% and ±10% strikes
    put_lower_strike = spot * 0.90   # Long put (10% OTM)
    put_upper_strike = spot * 0.95   # Short put (5% OTM)
    call_lower_strike = spot * 1.05  # Short call (5% OTM)
    call_upper_strike = spot * 1.10  # Long call (10% OTM)

    # Expiry in 45 days
    expiry = current_date + pd.Timedelta(days=45)

    print(f"   Put spread: ${put_lower_strike:.2f} / ${put_upper_strike:.2f}")
    print(f"   Call spread: ${call_lower_strike:.2f} / ${call_upper_strike:.2f}")
    print(f"   Expiry: {expiry.strftime('%Y-%m-%d')}")

    iron_condor = IronCondorStrategy(
        underlying=ticker,
        put_lower_strike=put_lower_strike,
        put_upper_strike=put_upper_strike,
        call_lower_strike=call_lower_strike,
        call_upper_strike=call_upper_strike,
        expiry=expiry,
        quantity=1.0
    )

    print(f"\n   Strategy structure:")
    print(iron_condor)

    # 3. Set up backtest
    print("\n3. Setting up backtest...")

    config = BacktestConfig(
        start_date=pd.Timestamp(start_date),
        end_date=expiry,
        initial_capital=100000.0,
        transaction_cost_per_contract=0.65,
        model=BlackScholesModel(use_market_iv=True)
    )

    engine = BacktestEngine(market_data, config)

    # Add the strategy
    engine.add_strategy(iron_condor, entry_date=current_date)

    # 4. Run backtest
    print("\n4. Running backtest...")
    results = engine.run()

    # 5. Calculate performance metrics
    print("\n5. Performance Analysis")
    print("-"*60)

    metrics = PerformanceMetrics(results, risk_free_rate=0.05)
    metrics.print_summary()

    # 6. P&L Attribution
    attribution = PnLAttributionEngine(results)
    attribution.print_summary()

    # 7. Breakeven Analysis
    print("\n7. Breakeven Analysis")
    print("-"*60)

    analyzer = BreakevenAnalyzer(iron_condor, market_data, config.model)
    analyzer.print_breakevens(current_date)

    # 8. Visualizations
    print("\n8. Creating visualizations...")

    viz = VisualizationEngine(use_plotly=False)  # Use matplotlib

    # Equity curve
    viz.plot_equity_curve(results, title="Iron Condor - Portfolio Value")

    # Greeks over time
    viz.plot_greeks(results, greeks=['delta', 'theta', 'vega'])

    # P&L attribution
    viz.plot_pnl_attribution(results, cumulative=True)

    # Risk profile
    viz.plot_risk_profile(
        iron_condor,
        current_date,
        market_data,
        config.model,
        title="Iron Condor Risk Profile"
    )

    print("\n" + "="*60)
    print("BACKTEST COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
