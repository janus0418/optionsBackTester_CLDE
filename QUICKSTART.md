# Quick Start Guide

## Installation

The backtester has been set up with `uv` virtual environment. To activate it:

```bash
cd "/Users/janussuk/Desktop/Options Backtester"
source .venv/bin/activate
```

## Running Tests

Verify everything works:

```bash
# Run unit tests
pytest backtester/tests/test_models.py -v

# Run quick integration test
python quick_test.py
```

## Running Examples

Try the example strategies:

```bash
# Iron Condor example
python examples/example_iron_condor.py

# Calendar Spread example
python examples/example_calendar_spread.py
```

## Basic Usage

### 1. Import the backtester

```python
from backtester import (
    MarketData,
    IronCondorStrategy,
    BacktestEngine,
    BacktestConfig,
    BlackScholesModel,
    PerformanceMetrics,
    VisualizationEngine
)
```

### 2. Load market data

```python
import pandas as pd

# From Yahoo Finance
market_data = MarketData.from_yahoo(
    ticker="SPY",
    start_date="2023-01-01",
    end_date="2023-12-31",
    default_iv=0.18  # 18% implied volatility
)
```

### 3. Create a strategy

```python
current_date = pd.Timestamp("2023-01-02")
spot = market_data.get_spot(current_date)
expiry = current_date + pd.Timedelta(days=45)

# Iron Condor example
strategy = IronCondorStrategy(
    underlying="SPY",
    put_lower_strike=spot * 0.90,
    put_upper_strike=spot * 0.95,
    call_lower_strike=spot * 1.05,
    call_upper_strike=spot * 1.10,
    expiry=expiry,
    quantity=1.0
)
```

### 4. Configure and run backtest

```python
config = BacktestConfig(
    start_date=current_date,
    end_date=expiry,
    initial_capital=100000.0,
    model=BlackScholesModel(use_market_iv=True)
)

engine = BacktestEngine(market_data, config)
engine.add_strategy(strategy, entry_date=current_date)
results = engine.run()
```

### 5. Analyze results

```python
# Performance metrics
metrics = PerformanceMetrics(results)
metrics.print_summary()

# Visualizations
viz = VisualizationEngine(use_plotly=False)
viz.plot_equity_curve(results)
viz.plot_greeks(results)
viz.plot_risk_profile(strategy, current_date, market_data, config.model)
```

## Available Strategies

- **IronCondorStrategy**: OTM put spread + OTM call spread
- **CalendarSpreadStrategy**: Same strike, different expiries
- **VerticalSpreadStrategy**: Different strikes, same expiry
- **ButterflyStrategy**: 1-2-1 ratio across 3 strikes
- **StraddleStrategy**: ATM call + put
- **StrangleStrategy**: OTM call + put

## Key Features

### Pricing Models
- Black-Scholes-Merton (with implied vol surface)
- Bachelier (normal model)
- SABR (stochastic volatility)
- Model-free surface Greeks

### Analytics
- Sharpe ratio, Sortino ratio, Calmar ratio
- Max drawdown, win rate, profit factor
- P&L attribution by Greeks (Delta, Gamma, Vega, Theta, Rho)
- Breakeven analysis (daily/weekly/monthly/expiry)
- Rolling metrics (Sharpe, volatility, drawdown)

### Visualizations
- Equity curves
- Drawdown charts
- Greeks evolution
- P&L attribution
- Risk profiles (P&L vs spot)
- Rolling metrics

## Project Structure

```
backtester/
├── __init__.py         # Package exports
├── data.py             # Market data and volatility surfaces
├── instruments.py      # Options and strategies
├── models.py           # Pricing models and Greeks
├── backtest.py         # Backtesting engine
├── metrics.py          # Performance analytics
├── visualize.py        # Plotting tools
├── utils.py            # Utility functions
└── tests/              # Unit tests
    └── test_models.py

examples/
├── example_iron_condor.py
└── example_calendar_spread.py
```

## Next Steps

1. Read the full [README.md](README.md) for comprehensive documentation
2. Explore the example scripts in `examples/`
3. Check the [instructions.txt](instructions.txt) for detailed implementation notes
4. Customize strategies for your own trading ideas

## Support

For issues or questions:
- Check the README.md for detailed documentation
- Review the example scripts
- Run the tests to verify your environment

---

**Happy Backtesting!**
