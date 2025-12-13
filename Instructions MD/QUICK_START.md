# Quick Start Guide - Volatility Spike Strategy

## Prerequisites

1. **Install Dolt** (if not already installed):
   ```bash
   # macOS
   brew install dolt

   # Linux
   curl -L https://github.com/dolthub/dolt/releases/latest/download/install.sh | sudo bash
   ```

2. **Clone DoltHub Dataset** (if not already done):
   ```bash
   cd ~/Desktop
   mkdir -p dolt_data && cd dolt_data
   dolt clone post-no-preference/options
   ```

   This downloads ~several GB of data (one-time operation).

3. **Activate Virtual Environment**:
   ```bash
   cd "Options Backtester"
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate  # Windows
   ```

## Run the Volatility Spike Strategy

### Option 1: Jupyter Notebook (Interactive)

```bash
jupyter notebook notebooks/04_volatility_spike_strategy.ipynb
```

Then click "Cell → Run All" to execute the entire analysis.

### Option 2: Command Line (Non-Interactive)

```bash
cd "/Users/janussuk/Desktop/Options Backtester"
source .venv/bin/activate
jupyter nbconvert --to notebook --execute \
  notebooks/04_volatility_spike_strategy.ipynb \
  --output 04_volatility_spike_strategy_output.ipynb
```

## What the Notebook Does

### Step-by-Step Analysis:

1. **Load Data** (30 sec - 2 min)
   - Loads SPY options data from DoltHub
   - Loads spot prices from Yahoo Finance

2. **Calculate IV Metrics** (5-10 sec)
   - Extracts ATM near-term implied volatility
   - Computes rolling statistics (60-day mean/std)

3. **Identify Spikes** (< 1 sec)
   - Detects when IV > mean + 1.5σ
   - Marks spike events for trading

4. **Visualize Patterns** (5 sec)
   - Plots IV over time with spike markers
   - Shows z-score evolution

5. **Mean Reversion Analysis** (2 sec)
   - Calculates time for IV to revert
   - Validates strategy timeframe

6. **Run Backtest** (1-5 min depending on date range)
   - Sells ATM straddles on spike days
   - Simulates full strategy execution

7. **Performance Metrics** (2 sec)
   - Calculates 22+ professional metrics
   - Risk-adjusted returns (Sharpe, Sortino, Omega)
   - Tail risk (VaR, CVaR, Skewness, Kurtosis)
   - Trade statistics (Win Rate, Profit Factor, etc.)

8. **Loss Analysis** (2 sec)
   - Identifies worst performing days
   - Analyzes spot movements vs P&L
   - Consecutive loss periods

9. **Risk Deep Dive** (2 sec)
   - Return distribution analysis
   - Q-Q plot vs normal distribution
   - Tail risk quantification

10. **Conclusions** (instant)
    - Strategy summary
    - Key insights
    - Recommendations

**Total Runtime**: 2-8 minutes depending on date range

## Expected Output

### Metrics You'll See:

- **Total Return**: Overall strategy performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk-adjusted returns
- **Omega Ratio**: Probability-weighted gains/losses
- **Max Drawdown**: Worst peak-to-trough decline
- **Win Rate**: % of profitable days
- **VaR (95%)**: Maximum expected loss (95% confidence)
- **CVaR (95%)**: Expected loss when VaR exceeded
- **Skewness**: Tail risk direction (negative = bad for short vol)
- **Kurtosis**: Fat tails indicator

### Visualizations You'll Get:

1. IV time series with spike detection
2. Z-score evolution
3. Mean reversion distribution
4. Cumulative P&L curve
5. Daily P&L distribution
6. Rolling Sharpe ratio
7. Drawdown chart
8. P&L vs spot movement scatter
9. Return distribution histogram
10. Q-Q plot (normality test)

## Customization

You can adjust parameters in the notebook:

```python
# In cell 3 (Data Loading):
START_DATE = "2022-01-01"  # Change start date
END_DATE = "2024-12-31"    # Change end date

# In cell 8 (Statistics):
LOOKBACK_WINDOW = 60       # Rolling window size (days)
SPIKE_THRESHOLD = 1.5      # Spike sensitivity (std devs)

# In cell 15 (Backtest):
TARGET_DTE_MIN = 25        # Minimum days to expiration
TARGET_DTE_MAX = 35        # Maximum days to expiration
initial_capital = 100000   # Starting capital
```

## Troubleshooting

### "No ATM IV data extracted"
- Check that DoltHub database is cloned correctly
- Verify date range has data: `dolt sql -q "SELECT DISTINCT date FROM option_chain WHERE act_symbol='SPY' LIMIT 10"`

### "No suitable options found"
- The dataset has monthly options (14, 28, 46+ DTE)
- Adjust TARGET_DTE_MIN/MAX to match available DTEs

### "Import errors"
- Ensure virtual environment is activated
- Run: `uv pip install -r requirements.txt`

### "Dolt command not found"
- Install Dolt: `brew install dolt` (macOS)
- Or download from: https://github.com/dolthub/dolt/releases

## Performance Notes

The strategy may show losses during volatile periods (2022-2023):
- **This is expected** - short volatility strategies have tail risk
- The notebook demonstrates methodology, not a guaranteed profit
- Use for educational purposes and research

## Further Research

Try these experiments:
1. Different spike thresholds (1.0σ, 2.0σ)
2. Different DTE ranges
3. Position sizing strategies
4. Stop-loss rules
5. Different tickers (QQQ, IWM)
6. Hedging strategies

## Support

For issues or questions:
1. Check `NOTEBOOK_FIXES.md` for technical details
2. Review `PERFORMANCE_METRICS_GUIDE.md` for metric explanations
3. See `INSTALLATION.md` for setup help

---

**Happy Backtesting!** 📊📈
