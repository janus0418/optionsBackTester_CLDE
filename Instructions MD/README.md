# Options Strategy Backtester

A comprehensive, production-grade Python framework for backtesting complex options trading strategies with advanced Greeks calculation, P&L attribution, and risk analysis.

## Features

### Core Capabilities
- **Multi-leg Strategy Support**: Calendar spreads, vertical spreads, butterflies, iron condors, straddles, strangles, and custom strategies
- **Advanced Pricing Models**:
  - Black-Scholes-Merton with implied volatility surfaces
  - Bachelier (normal model)
  - SABR (Stochastic Alpha Beta Rho)
  - Model-free surface-based Greeks (bump-and-revalue)
- **Comprehensive Greeks**: Delta, Gamma, Vega, Theta, Rho with surface-aware calculations
- **P&L Attribution**: Decompose daily P&L by Greek contributions
- **Performance Metrics**: Sharpe ratio, Sortino ratio, max drawdown, Calmar ratio, win rate, profit factor
- **Rolling Analytics**: Rolling Sharpe, volatility, and drawdown over configurable windows
- **Breakeven Analysis**: Daily, weekly, monthly, and expiration breakeven levels
- **Rich Visualizations**: Equity curves, drawdown plots, Greeks evolution, P&L attribution, risk profiles

### Design Principles
- **Object-Oriented Architecture**: Clean separation of concerns with extensible base classes
- **Type Safety**: Full type hints throughout
- **Modular**: Easy to add new pricing models, strategies, or analytics
- **Well-Tested**: Comprehensive unit tests for pricing and Greeks
- **Production-Ready**: Transaction costs, slippage, and realistic market data handling

## Installation

### Using uv (Recommended)

```bash
cd "Options Backtester"
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install numpy pandas scipy matplotlib plotly numba statsmodels pyyaml pytest jupyter notebook yfinance
```

### Using pip

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Iron Condor Backtest

```python
import pandas as pd
from backtester import (
    MarketData,
    IronCondorStrategy,
    BacktestEngine,
    BacktestConfig,
    BlackScholesModel,
    PerformanceMetrics,
    VisualizationEngine
)

# 1. Load market data
market_data = MarketData.from_yahoo(
    ticker="SPY",
    start_date="2023-01-01",
    end_date="2023-12-31",
    default_iv=0.18
)

# 2. Create strategy
current_date = pd.Timestamp("2023-01-01")
spot = market_data.get_spot(current_date)
expiry = current_date + pd.Timedelta(days=45)

iron_condor = IronCondorStrategy(
    underlying="SPY",
    put_lower_strike=spot * 0.90,
    put_upper_strike=spot * 0.95,
    call_lower_strike=spot * 1.05,
    call_upper_strike=spot * 1.10,
    expiry=expiry,
    quantity=1.0
)

# 3. Configure and run backtest
config = BacktestConfig(
    start_date=current_date,
    end_date=expiry,
    initial_capital=100000.0,
    model=BlackScholesModel(use_market_iv=True)
)

engine = BacktestEngine(market_data, config)
engine.add_strategy(iron_condor, entry_date=current_date)
results = engine.run()

# 4. Analyze results
metrics = PerformanceMetrics(results)
metrics.print_summary()

# 5. Visualize
viz = VisualizationEngine()
viz.plot_equity_curve(results)
viz.plot_risk_profile(iron_condor, current_date, market_data, config.model)
```

## Architecture

### Module Structure

```
backtester/
├── __init__.py          # Package initialization
├── data.py              # MarketData, VolSurface classes
├── instruments.py       # OptionContract, OptionLeg, Strategy classes
├── models.py            # Pricing models (BS, Bachelier, SABR, etc.)
├── backtest.py          # BacktestEngine, BacktestConfig
├── metrics.py           # PerformanceMetrics, PnLAttribution, Breakeven
├── visualize.py         # VisualizationEngine
├── utils.py             # Utility functions
└── tests/
    ├── __init__.py
    └── test_models.py   # Unit tests
```

### Key Classes

#### Data Layer
- **MarketData**: Manages historical spot prices, volatility surfaces, rates, and dividends
- **VolSurface**: Implied volatility surface with strike/expiry interpolation

#### Instrument Layer
- **OptionContract**: Individual option specification
- **OptionLeg**: Option position (contract + quantity + direction)
- **OptionStrategy**: Base class for multi-leg strategies
- **Portfolio**: Collection of strategies with cash management

#### Pricing Layer
- **PricingModel**: Abstract base for pricing models
- **BlackScholesModel**: Classic BSM with surface-based IV
- **BachelierModel**: Normal (arithmetic) model
- **SABRModel**: SABR stochastic volatility model
- **SurfaceGreeksModel**: Model-free bump-and-revalue Greeks

#### Backtest Layer
- **BacktestConfig**: Configuration (dates, costs, model, windows)
- **BacktestEngine**: Main simulation engine
- **RollingStrategy**: Helper for periodic strategy rolling
- **DeltaHedger**: Delta-neutral hedging utility

#### Analytics Layer
- **PerformanceMetrics**: Sharpe, Sortino, drawdown, etc.
- **PnLAttributionEngine**: Greek-based P&L decomposition
- **BreakevenAnalyzer**: Multi-horizon breakeven calculation

#### Visualization Layer
- **VisualizationEngine**: Comprehensive plotting (matplotlib/plotly)

## Supported Strategies

### Pre-built Strategies
1. **CalendarSpreadStrategy**: Same strike, different expiries
2. **VerticalSpreadStrategy**: Different strikes, same expiry (debit/credit)
3. **ButterflyStrategy**: 1-2-1 ratio across 3 strikes
4. **IronCondorStrategy**: OTM put spread + OTM call spread
5. **StraddleStrategy**: Long/short ATM call + put
6. **StrangleStrategy**: Long/short OTM call + put

### Custom Strategies
Easily build custom strategies by composing legs:

```python
from backtester import OptionStrategy, OptionLeg, OptionContract

custom_strategy = OptionStrategy(name="My Custom Strategy")

# Add legs manually
call1 = OptionContract(underlying="SPY", option_type="call", strike=400, expiry=expiry)
custom_strategy.add_leg(OptionLeg(call1, quantity=2))

call2 = OptionContract(underlying="SPY", option_type="call", strike=410, expiry=expiry)
custom_strategy.add_leg(OptionLeg(call2, quantity=-3))
```

## Pricing Models

### Black-Scholes-Merton
- Uses implied volatility from surface (skew-aware)
- Closed-form prices and Greeks
- Most commonly used for liquid options

### Bachelier (Normal Model)
- Additive (not multiplicative) returns
- Useful for low-rate environments and futures options
- Closed-form solutions

### SABR Model
- Captures volatility smile/skew dynamics
- Stochastic volatility model
- Uses Hagan's approximation formulas

### Surface-Based Greeks
- Model-free approach using bump-and-revalue
- Respects market skew/smile
- Numerically stable

## Performance Metrics

### Standard Metrics
- **Total Return**: Absolute and percentage
- **Annualized Return (CAGR)**: Compound annual growth rate
- **Volatility**: Annualized standard deviation
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted return
- **Max Drawdown**: Largest peak-to-trough decline
- **Calmar Ratio**: Return / Max Drawdown
- **Win Rate**: Percentage of profitable days
- **Profit Factor**: Gross profit / Gross loss

### Rolling Metrics
- Rolling Sharpe (configurable windows)
- Rolling volatility
- Rolling max drawdown

### Greeks-Based Attribution
- Delta P&L: From underlying price movement
- Gamma P&L: From convexity
- Vega P&L: From volatility changes
- Theta P&L: From time decay
- Rho P&L: From rate changes
- Residual: Unexplained P&L

## Breakeven Analysis

Calculate breakeven levels at multiple horizons:
- **Daily**: 1 trading day forward
- **Weekly**: 5 trading days forward
- **Monthly**: 21 trading days forward
- **At Expiration**: Terminal payoff

```python
from backtester import BreakevenAnalyzer

analyzer = BreakevenAnalyzer(strategy, market_data, model)
analyzer.print_breakevens(current_date)

# Example output:
# Current Spot: $420.50
#
# In 1 day(s):
#   Lower: $412.30 (-1.9%)
#   Upper: $428.70 (+2.0%)
#
# At EXPIRY:
#   Lower: $400.00 (-4.9%)
#   Upper: $440.00 (+4.6%)
```

## Visualization

### Available Charts
- Equity curve (portfolio value over time)
- Returns distribution (histogram)
- Drawdown curve (underwater chart)
- Greeks evolution (delta, gamma, vega, theta, rho)
- P&L attribution (cumulative/stacked by Greek)
- Risk profile (P&L vs spot at multiple time points)
- Rolling metrics (Sharpe, volatility, drawdown)

### Plotly vs Matplotlib
```python
# Interactive Plotly charts (default)
viz = VisualizationEngine(use_plotly=True)

# Static Matplotlib charts
viz = VisualizationEngine(use_plotly=False)
```

## Examples

See the `examples/` directory:
- `example_iron_condor.py`: Iron condor backtest with full analysis
- `example_calendar_spread.py`: Calendar spread time decay strategy

Run examples:
```bash
python examples/example_iron_condor.py
python examples/example_calendar_spread.py
```

## Testing

Run unit tests:
```bash
pytest backtester/tests/ -v
```

Run specific test file:
```bash
pytest backtester/tests/test_models.py -v
```

## Advanced Usage

### Custom Volatility Surface

```python
import pandas as pd
from backtester import VolSurface

# Create custom vol surface data
vol_data = pd.DataFrame({
    'strike': [380, 390, 400, 410, 420],
    'expiry': [30, 30, 30, 30, 30],
    'implied_vol': [0.22, 0.20, 0.18, 0.19, 0.21]  # Smile
})

vol_surface = VolSurface(
    date=pd.Timestamp('2024-01-01'),
    underlying='SPY',
    vol_data=vol_data,
    interpolation_method='cubic'
)
```

### Delta Hedging

```python
from backtester import DeltaHedger

# Create delta hedger
hedger = DeltaHedger(
    target_delta=0.0,
    tolerance=0.1,
    rebalance_frequency='daily'
)

# In backtest loop
if hedger.should_rebalance(current_delta):
    hedger.execute_hedge(portfolio, current_delta, spot, date)
```

### Rolling Strategies

```python
from backtester import RollingStrategy

# Define strategy factory
def create_monthly_iron_condor(date):
    # ... create iron condor
    return iron_condor

rolling = RollingStrategy(
    strategy_factory=create_monthly_iron_condor,
    entry_frequency='monthly',
    days_before_expiry=7  # Roll 7 days before expiry
)
```

## Configuration

### Backtest Configuration Options

```python
config = BacktestConfig(
    start_date=pd.Timestamp('2023-01-01'),
    end_date=pd.Timestamp('2023-12-31'),
    initial_capital=100000.0,
    rebalancing_frequency='daily',  # 'daily', 'weekly', 'monthly'
    transaction_cost_per_contract=0.65,
    transaction_cost_pct=0.0001,
    slippage_bps=1.0,
    risk_free_rate=0.05,
    rolling_windows=[20, 60, 252],
    model=BlackScholesModel(use_market_iv=True)
)
```

## Extending the Framework

### Add a New Pricing Model

```python
from backtester.models import PricingModel

class MyCustomModel(PricingModel):
    def price(self, option, date, market_data):
        # Your pricing logic
        return price

    def greeks(self, option, date, market_data):
        # Your Greeks calculation
        return {
            'delta': ...,
            'gamma': ...,
            'vega': ...,
            'theta': ...,
            'rho': ...
        }
```

### Add a New Strategy

```python
from backtester import OptionStrategy, OptionLeg, OptionContract

class MyStrategy(OptionStrategy):
    def __init__(self, underlying, ...):
        super().__init__("My Strategy")
        # Build legs
        # self.add_leg(...)
```

## Performance Optimization

For large-scale backtests:
- Use `numba` JIT compilation for pricing loops
- Implement lazy loading for large datasets
- Vectorize calculations with NumPy/Pandas
- Use multiprocessing for parameter sweeps

## Limitations and Future Enhancements

### Current Limitations
- European-style options only (American exercise not yet implemented)
- Simplified early exercise boundary for American options
- Basic transaction cost modeling
- No dividend adjustments for option strikes

### Planned Features
- American option pricing (binomial/trinomial trees, Longstaff-Schwartz)
- Dividend strike adjustments
- Margin requirements and account constraints
- Multi-asset strategies
- Scenario analysis and stress testing
- Parameter optimization (grid search, genetic algorithms)
- Live trading integration
- Machine learning signal integration

## References

### Academic Papers
- Black, F., & Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities"
- Heston, S. (1993). "A Closed-Form Solution for Options with Stochastic Volatility"
- Hagan, P. et al. (2002). "Managing Smile Risk" (SABR model)

### Books
- Hull, J. (2022). "Options, Futures, and Other Derivatives" (10th ed.)
- Natenberg, S. (1994). "Option Volatility and Pricing"
- Taleb, N. N. (1997). "Dynamic Hedging: Managing Vanilla and Exotic Options"

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

Built following industry best practices and state-of-the-art options pricing research.

---

**Disclaimer**: This software is for educational and research purposes only. Not financial advice. Use at your own risk.
