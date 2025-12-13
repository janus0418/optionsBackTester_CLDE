# Jupyter Notebook Examples

This directory contains interactive Jupyter notebooks demonstrating how to use the Options Backtester with the DoltHub options dataset.

## Setup

### 1. Install Dolt

**macOS:**
```bash
brew install dolt
```

**Linux:**
```bash
curl -L https://github.com/dolthub/dolt/releases/latest/download/install.sh | sudo bash
```

**Windows:**
Download from https://github.com/dolthub/dolt/releases

### 2. Clone the Options Database

```bash
cd ~/Desktop
mkdir dolt_data && cd dolt_data
dolt clone post-no-preference/options
```

This will download the options dataset to `~/Desktop/dolt_data/options`. The initial clone may take some time depending on your connection.

### 3. Install Required Packages

```bash
cd "Options Backtester"
source .venv/bin/activate  # Or activate your virtual environment
pip install jupyter notebook ipykernel
```

### 4. Start Jupyter

```bash
jupyter notebook notebooks/
```

## Notebooks

### 1. Getting Started with DoltHub (`01_getting_started_dolthub.ipynb`)

**Level:** Beginner

Learn the basics:
- Connect to the DoltHub options database
- Load and explore options chain data
- Visualize volatility smiles and surfaces
- Access historical and implied volatility data
- Create MarketData objects for backtesting

**Estimated time:** 15 minutes

### 2. Iron Condor Backtest (`02_iron_condor_backtest_dolthub.ipynb`)

**Level:** Intermediate

Complete backtest of an Iron Condor strategy:
- Load real market data from DoltHub
- Construct an iron condor with realistic strikes
- Run full backtest with transaction costs
- Analyze performance metrics and P&L attribution
- Visualize results and Greeks evolution

**Estimated time:** 20 minutes

### 3. Calendar Spread Backtest (`03_calendar_spread_backtest.ipynb`)

**Level:** Intermediate

Time decay strategy backtest:
- Design calendar spreads with near/far expirations
- Analyze theta decay and breakevens
- Test strategies on different market conditions
- Compare call vs put calendars

**Estimated time:** 20 minutes

## Dataset Information

### DoltHub post-no-preference/options

- **Date Range:** February 2019 - December 2025
- **Tickers:** 2000+ symbols (SPY, AAPL, NVDA, TSLA, etc.)
- **Data Points:**
  - Options chain with bid/ask prices
  - Greeks (delta, gamma, vega, theta, rho)
  - Implied volatility
  - Historical volatility metrics

### Tables

1. **option_chain**: Options prices and Greeks
   - Columns: date, act_symbol, expiration, strike, call_put, bid, ask, vol, delta, gamma, theta, vega, rho

2. **volatility_history**: Volatility metrics
   - Columns: date, act_symbol, hv_current, hv_week_ago, hv_month_ago, iv_current, iv_week_ago, iv_month_ago, etc.

## Common Tasks

### Update Database Path

If you cloned the database to a different location, update the `DB_PATH` variable in each notebook:

```python
DB_PATH = "/path/to/your/dolt_data/options"
```

### Try Different Tickers

Change the `TICKER` variable to test strategies on different underlyings:

```python
TICKER = "SPY"   # S&P 500 ETF
TICKER = "AAPL"  # Apple
TICKER = "NVDA"  # NVIDIA
TICKER = "TSLA"  # Tesla
```

### Adjust Time Periods

Modify date ranges to test different market conditions:

```python
START_DATE = "2024-01-01"  # Bull market
START_DATE = "2020-03-01"  # COVID crash
START_DATE = "2022-01-01"  # Bear market
```

## Next Steps

After completing the notebooks:

1. **Customize Strategies**
   - Modify strike selections
   - Test different DTE (days to expiration)
   - Experiment with position sizing

2. **Build Custom Strategies**
   - Create your own strategy classes
   - Combine multiple strategies
   - Implement rolling strategies

3. **Advanced Analysis**
   - Parameter optimization
   - Walk-forward testing
   - Monte Carlo simulation
   - Regime-based analysis

4. **Production Testing**
   - Backtest on full dataset (2019-2025)
   - Test on multiple tickers
   - Analyze across different market regimes

## Troubleshooting

### Database Connection Issues

If you get errors connecting to the database:

```python
# Verify database path
import os
DB_PATH = "/Users/janussuk/Desktop/dolt_data/options"
print(f"Database exists: {os.path.exists(DB_PATH)}")
```

### Missing Data

Some tickers may not have complete data for all dates:

```python
# Check data availability first
try:
    options = adapter.load_option_data(ticker, date, date)
    print(f"✓ Data available for {ticker}")
except Exception as e:
    print(f"✗ No data for {ticker}: {e}")
```

### Performance Issues

For large date ranges, consider:
- Reducing the date range
- Using fewer tickers
- Filtering to specific expirations
- Disabling volatility surface building if not needed

## Resources

- **DoltHub Repository:** https://www.dolthub.com/repositories/post-no-preference/options
- **Backtester Documentation:** ../README.md
- **Dolt Documentation:** https://docs.dolthub.com/

## Contributing

Have ideas for new notebooks? Found a bug? Contributions are welcome!

## Support

For questions or issues:
1. Check the main README.md
2. Review the QUICKSTART.md guide
3. Open an issue on GitHub

---

**Happy Backtesting!**
