# DoltHub Options Dataset Integration Guide

## Overview

This backtester now supports loading real historical options data from the DoltHub **post-no-preference/options** database. This integration provides access to nearly 7 years of options data (Feb 2019 - Dec 2025) for 2000+ symbols.

## Quick Start

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

**Note:** The initial clone will take time depending on your connection speed. The database is large.

### 3. Test the Integration

```bash
cd "Options Backtester"
source .venv/bin/activate
python test_dolthub_integration.py
```

You should see:
```
🎉 All tests passed! The DoltHub integration is working correctly.
```

## Dataset Information

### Database Tables

1. **option_chain** - Options prices and Greeks
   - Columns: `date`, `act_symbol`, `expiration`, `strike`, `call_put`, `bid`, `ask`, `vol` (IV), `delta`, `gamma`, `theta`, `vega`, `rho`
   - Records: Millions of option contracts
   - Date range: 2019-02-09 to 2025-12-08

2. **volatility_history** - Volatility metrics
   - Columns: `date`, `act_symbol`, `hv_current`, `hv_week_ago`, `hv_month_ago`, `iv_current`, etc.
   - Provides historical and implied volatility tracking

### Available Tickers

The dataset includes options data for major stocks and ETFs:
- **Indexes**: SPY, QQQ, IWM, DIA
- **Tech**: AAPL, MSFT, NVDA, TSLA, META, GOOGL, AMZN
- **Finance**: JPM, BAC, GS, MS, WFC
- **And 2000+ more symbols**

## Usage Examples

### Basic Usage

```python
from backtester import (
    DoltHubAdapter,
    MarketDataLoader,
    IronCondorStrategy,
    BacktestEngine,
    BlackScholesModel
)

# Connect to database
DB_PATH = "/path/to/dolt_data/options"
adapter = DoltHubAdapter(DB_PATH)

# Load market data
loader = MarketDataLoader(adapter)
market_data = loader.load(
    ticker="SPY",
    start_date="2024-01-01",
    end_date="2024-03-31",
    build_vol_surface=True
)

# Now use market_data for backtesting!
```

### Load Options Chain

```python
# Load specific date's options
options = adapter.load_option_data(
    ticker="AAPL",
    start_date="2024-01-03",
    end_date="2024-01-03"
)

# Filter by option type
calls = adapter.load_option_data(
    ticker="AAPL",
    start_date="2024-01-03",
    end_date="2024-01-03",
    option_type="call"
)
```

### Load Volatility History

```python
vol_hist = adapter.load_volatility_data(
    ticker="AAPL",
    start_date="2024-01-01",
    end_date="2024-03-31"
)

# Access HV and IV data
print(vol_hist[['date', 'hv_current', 'iv_current']])
```

### Get Available Expirations and Strikes

```python
loader = MarketDataLoader(adapter)

# Get available expiration dates
expirations = loader.get_available_expirations("SPY", "2024-01-03")
print(f"Available expirations: {expirations[:5]}")

# Get strikes for specific expiration
strikes = loader.get_strikes_for_expiration(
    ticker="SPY",
    date="2024-01-03",
    expiration="2024-02-16",
    option_type="call"
)
print(f"Available strikes: {strikes}")
```

## Architecture

### Data Loading System

The system uses an **adapter pattern** to support multiple data sources:

```
DataSourceAdapter (ABC)
    ├── DoltHubAdapter (Dolt SQL databases)
    ├── CSVAdapter (CSV files)
    └── Custom adapters (extensible)

MarketDataLoader
    - Uses adapters to create MarketData objects
    - Builds volatility surfaces automatically
    - Handles data transformation
```

### Key Classes

1. **DoltHubAdapter**: Connects to Dolt databases via SQL
2. **MarketDataLoader**: High-level interface for loading complete market data
3. **CSVAdapter**: For CSV-based datasets (extensible)

### Extensibility

You can create custom adapters for other data sources:

```python
from backtester import DataSourceAdapter

class MyCustomAdapter(DataSourceAdapter):
    def load_spot_data(self, ticker, start_date, end_date):
        # Your implementation
        pass

    def load_option_data(self, ticker, start_date, end_date, option_type=None):
        # Your implementation
        pass

    def load_volatility_data(self, ticker, start_date, end_date):
        # Optional: return None if not available
        return None
```

## Jupyter Notebooks

Interactive examples are provided in the `notebooks/` directory:

1. **01_getting_started_dolthub.ipynb**
   - Connect to database
   - Explore options data
   - Visualize volatility smiles
   - Create MarketData objects

2. **02_iron_condor_backtest_dolthub.ipynb**
   - Complete iron condor backtest
   - Performance analysis
   - P&L attribution
   - Greeks visualization

3. **03_calendar_spread_backtest.ipynb**
   - Calendar spread strategy
   - Time decay analysis
   - Breakeven calculations

### Running Notebooks

```bash
cd "Options Backtester"
source .venv/bin/activate
pip install jupyter notebook
jupyter notebook notebooks/
```

## Performance Considerations

### Database Size

The options database is large. Consider:
- Using smaller date ranges during development
- Filtering to specific tickers
- Building volatility surfaces only when needed

### Query Optimization

The adapter uses Dolt SQL, which may be slower than traditional databases:
- Cache loaded data when possible
- Load full date ranges once rather than querying repeatedly
- Use the MarketDataLoader which optimizes queries

### Memory Usage

Loading large date ranges or multiple tickers can use significant memory:
- Process data in chunks if needed
- Use date range slicing
- Clear unused data with `del market_data` when done

## Troubleshooting

### Database Not Found

```
Error: Database path does not exist
```

**Solution**: Verify database path and clone if needed:
```bash
ls /path/to/dolt_data/options  # Should show dolt database files
dolt clone post-no-preference/options  # If not cloned
```

### No Data for Ticker/Date

```
Error: No option data available for TICKER
```

**Possible causes**:
1. Date was a non-trading day (weekend, holiday)
2. Ticker not in dataset
3. Data not available for that date range

**Solution**: Check available dates:
```bash
cd /path/to/dolt_data/options
dolt sql -q "SELECT MIN(date), MAX(date) FROM option_chain WHERE act_symbol = 'TICKER';"
```

### Type Conversion Errors

If you see errors about string/float conversion:
- The adapter automatically converts numeric columns
- Check that your Dolt version is up to date
- Verify data integrity in the database

### Slow Performance

If queries are slow:
- Use smaller date ranges
- Consider indexing in Dolt (advanced)
- Cache frequently accessed data
- Use the shallow clone (`--depth 1`) for testing

## Best Practices

### 1. Data Validation

Always validate loaded data:
```python
# Check for NaN values
options = adapter.load_option_data(...)
print(f"Missing values:\n{options.isnull().sum()}")

# Verify date ranges
print(f"Date range: {options['date'].min()} to {options['date'].max()}")
```

### 2. Trading Days

Remember that markets are closed on weekends and holidays:
```python
# Use actual trading dates from the dataset
trading_dates = market_data.time_index
print(f"Trading days: {len(trading_dates)}")
```

### 3. Volatility Surfaces

Building surfaces can be computationally expensive:
```python
# Build surfaces only when needed
market_data = loader.load(
    ticker="SPY",
    start_date="2024-01-01",
    end_date="2024-03-31",
    build_vol_surface=True  # Set to False if not using Greeks
)
```

### 4. Testing

Start with small date ranges and simple strategies:
```python
# Good for testing
start_date = "2024-01-01"
end_date = "2024-01-31"  # One month

# Then scale up
start_date = "2024-01-01"
end_date = "2024-12-31"  # Full year
```

## Advanced Usage

### Custom Vol Surfaces

You can customize how volatility surfaces are built:

```python
# In data_loaders.py, modify _build_vol_surfaces()
# to use different interpolation methods or filters
```

### Multi-Ticker Analysis

Load data for multiple tickers:

```python
tickers = ["SPY", "QQQ", "IWM"]
market_data_dict = {}

for ticker in tickers:
    market_data_dict[ticker] = loader.load(
        ticker=ticker,
        start_date="2024-01-01",
        end_date="2024-03-31"
    )
```

### Custom Data Filters

Filter options by specific criteria:

```python
options = adapter.load_option_data("SPY", "2024-01-03", "2024-01-03")

# Filter to near-term expirations only
near_term = options[
    (options['expiration'] - options['date']).dt.days <= 45
]

# Filter to ATM options only
spot = market_data.get_spot(pd.Timestamp("2024-01-03"))
atm_options = options[
    (options['strike'] >= spot * 0.95) &
    (options['strike'] <= spot * 1.05)
]
```

## Resources

- **DoltHub Repository**: https://www.dolthub.com/repositories/post-no-preference/options
- **Dolt Documentation**: https://docs.dolthub.com/
- **Backtester README**: README.md
- **Quick Start Guide**: QUICKSTART.md

## Contributing

If you create custom adapters or improve the integration:
1. Fork the repository
2. Add your adapter to `backtester/data_loaders.py`
3. Add tests
4. Submit a pull request

## Support

For issues:
1. Check this guide
2. Run `python test_dolthub_integration.py`
3. Review the Jupyter notebooks
4. Open an issue on GitHub

---

**Disclaimer**: This software is for educational and research purposes only. Historical data does not guarantee future results. Use at your own risk.
