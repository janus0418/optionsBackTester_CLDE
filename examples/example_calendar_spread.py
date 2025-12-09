"""
Example: Calendar Spread Strategy Backtest

This example demonstrates a calendar spread (time spread) strategy
that profits from time decay and volatility changes.
"""

import pandas as pd
import numpy as np

from backtester import (
    MarketData,
    CalendarSpreadStrategy,
    BacktestEngine,
    BacktestConfig,
    BlackScholesModel,
    PerformanceMetrics,
    VisualizationEngine
)


def main():
    """Run calendar spread backtest example."""

    print("="*60)
    print("CALENDAR SPREAD STRATEGY BACKTEST")
    print("="*60)

    # 1. Load market data
    print("\n1. Loading market data...")

    ticker = "SPY"
    start_date = "2023-01-01"
    end_date = "2023-12-31"

    market_data = MarketData.from_yahoo(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        default_iv=0.20
    )

    print(f"   Loaded {len(market_data.time_index)} days")

    # 2. Create Calendar Spread
    print("\n2. Creating Calendar Spread...")

    current_date = pd.Timestamp(start_date)
    spot = market_data.get_spot(current_date)

    # ATM strike
    strike = round(spot)

    # Near-term expiry (30 days)
    near_expiry = current_date + pd.Timedelta(days=30)

    # Far-term expiry (60 days)
    far_expiry = current_date + pd.Timedelta(days=60)

    print(f"   Spot: ${spot:.2f}")
    print(f"   Strike: ${strike:.2f} (ATM)")
    print(f"   Short leg expiry: {near_expiry.strftime('%Y-%m-%d')}")
    print(f"   Long leg expiry: {far_expiry.strftime('%Y-%m-%d')}")

    calendar_spread = CalendarSpreadStrategy(
        underlying=ticker,
        strike=strike,
        near_expiry=near_expiry,
        far_expiry=far_expiry,
        option_type='call',  # Can also use puts
        quantity=1.0
    )

    print(f"\n   Strategy:")
    print(calendar_spread)

    # 3. Run backtest
    print("\n3. Running backtest...")

    config = BacktestConfig(
        start_date=current_date,
        end_date=far_expiry,
        initial_capital=50000.0,
        model=BlackScholesModel(use_market_iv=True)
    )

    engine = BacktestEngine(market_data, config)
    engine.add_strategy(calendar_spread, entry_date=current_date)

    results = engine.run()

    # 4. Analyze results
    print("\n4. Performance Analysis")
    print("-"*60)

    metrics = PerformanceMetrics(results)
    metrics.print_summary()

    # 5. Visualizations
    print("\n5. Creating visualizations...")

    viz = VisualizationEngine(use_plotly=False)

    viz.plot_equity_curve(results, title="Calendar Spread - Portfolio Value")

    viz.plot_greeks(
        results,
        greeks=['theta', 'vega', 'delta'],
        title="Calendar Spread Greeks"
    )

    viz.plot_risk_profile(
        calendar_spread,
        current_date,
        market_data,
        config.model,
        title="Calendar Spread Risk Profile"
    )

    print("\nBacktest complete!")


if __name__ == "__main__":
    main()
