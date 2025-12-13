# Volatility Spike Mean Reversion Strategy

## Quick Start

To run the complete volatility spike strategy analysis:

```bash
cd "Options Backtester"
source .venv/bin/activate
jupyter notebook notebooks/04_volatility_spike_strategy.ipynb
```

## Strategy Overview

### Hypothesis
When at-the-money (ATM) 1-week implied volatility for SPY spikes significantly above its historical average, it tends to revert to the mean within a predictable timeframe. We can profit by selling volatility during these spikes.

### Strategy Rules

1. **Calculate Baseline Statistics**
   - Track rolling 60-day average of ATM 1-week IV
   - Calculate rolling standard deviation
   - Identify "normal" volatility regime

2. **Detect Volatility Spikes**
   - Spike = IV > (Mean + 1.5 × Std Dev)
   - Z-score threshold: 1.5 sigma

3. **Enter Trades**
   - When spike detected: Sell 2-week ATM straddle
   - Short both call and put at same strike
   - Collect premium from elevated volatility

4. **Exit Trades**
   - Hold until expiration (14 days)
   - Alternative: Close early if 50% profit achieved

### Why This Works

**Volatility Mean Reversion**: Implied volatility tends to revert to its long-term average after spikes due to:
- Emotional overreaction to market events
- VIX term structure dynamics
- Market maker hedging flows
- Fear premium compression

**Statistical Edge**: By selling when IV is 1.5σ above average:
- Premium received is elevated
- Probability of profit is enhanced
- Time decay (theta) works in our favor

## Strategy Components

### 1. Data Analysis
The notebook performs comprehensive analysis:
- Loads 2+ years of SPY options data
- Extracts ATM 1-week IV for each trading day
- Calculates rolling statistics (mean, std dev, z-score)
- Identifies spike events

### 2. Mean Reversion Study
Analyzes post-spike behavior:
- Time for IV to return to normal levels
- Distribution of reversion periods
- Validates 2-week expiration choice

### 3. Backtest Execution
Implements actual trading strategy:
- Sells straddles on spike days
- Tracks P&L progression
- Calculates Greeks exposure
- Manages position lifecycle

### 4. Performance Analysis
**Comprehensive Metrics** (12+ new metrics implemented):

#### Risk-Adjusted Returns
- **Sharpe Ratio**: Return per unit of volatility
- **Sortino Ratio**: Return per unit of downside risk
- **Omega Ratio**: Probability-weighted gains vs losses
- **Sterling Ratio**: Return vs average drawdown
- **Information Ratio**: Excess return vs benchmark

#### Drawdown Metrics
- **Max Drawdown**: Worst peak-to-trough decline
- **Calmar Ratio**: Annual return / max drawdown
- **Ulcer Index**: Depth and duration of pain
- **Recovery Factor**: Profit / worst drawdown

#### Tail Risk Metrics
- **Value at Risk (VaR)**: Max expected loss at 95% confidence
- **Conditional VaR (CVaR)**: Expected loss when VaR exceeded
- **Skewness**: Distribution asymmetry (tail direction)
- **Kurtosis**: Fat tails indicator

#### Trade-Level Metrics
- **Win Rate**: % of profitable days
- **Profit Factor**: Total wins / total losses
- **Expectancy**: Expected value per trade
- **Win/Loss Ratio**: Average win / average loss
- **Consecutive Wins/Losses**: Streak analysis

### 5. Loss Analysis
Identifies and analyzes poor performance:
- Worst performing days
- Spot price movements during losses
- Consecutive loss periods
- Common failure patterns

## Results Visualization

The notebook creates comprehensive visualizations:

1. **IV Analysis Charts**
   - Historical IV with spike markers
   - Z-score evolution
   - Rolling mean and standard deviation bands

2. **Mean Reversion Analysis**
   - Distribution of reversion times
   - Validation of 2-week expiration

3. **P&L Progression**
   - Cumulative P&L curve
   - Daily P&L distribution
   - Equity curve with drawdowns

4. **Risk Metrics**
   - Rolling Sharpe ratio
   - Return distribution histogram
   - Q-Q plot vs normal distribution
   - P&L vs spot movement scatter

5. **Loss Deep Dive**
   - Worst days analysis
   - Consecutive loss periods
   - Risk factor attribution

## Expected Outcomes

### What the Strategy Teaches

1. **Volatility Behavior**: Understanding IV spikes and mean reversion
2. **Options Greeks**: Delta, gamma, theta, vega dynamics
3. **Risk Management**: Tail risk in short volatility strategies
4. **Performance Metrics**: Professional evaluation techniques

### Performance Characteristics

**Typical Results** (will vary by period):
- Win rate: 60-70% (most days are profitable)
- Max drawdown: 5-15% (large moves hurt)
- Sharpe ratio: 0.5-1.5 (moderate risk-adjusted returns)
- Negative skew: Short options have tail risk

**Risk Factors**:
- Large market moves (>2%) cause losses
- "Gamma risk": Accelerating losses if spot moves
- "Vega risk": If IV continues to rise
- Consecutive loss streaks during volatile periods

## Key Insights

### Strengths
✓ Exploits volatility mean reversion
✓ Positive theta (time decay)
✓ High win rate provides steady income
✓ Quantifiable edge (statistical)

### Weaknesses
⚠️ Tail risk (negative skew)
⚠️ Large losses on big market moves
⚠️ Gamma exposure during volatility
⚠️ May underperform in trending volatility regimes

### Improvements to Consider

1. **Position Sizing**: Kelly Criterion or risk parity
2. **Stop Losses**: Close at 2x max credit received
3. **Hedging**: Buy far OTM options for tail protection
4. **Dynamic Thresholds**: Adjust spike threshold based on regime
5. **Expiration Management**: Close early at 50% profit
6. **Diversification**: Trade multiple underlyings (SPY, QQQ, IWM)

## Files

- **Notebook**: `notebooks/04_volatility_spike_strategy.ipynb`
- **Metrics Guide**: `PERFORMANCE_METRICS_GUIDE.md`
- **Integration Guide**: `DOLTHUB_INTEGRATION.md`

## Running the Analysis

### Prerequisites
```bash
# Ensure DoltHub database is cloned
cd ~/Desktop/dolt_data
ls options  # Should show dolt database files

# Activate environment
cd "Options Backtester"
source .venv/bin/activate
```

### Execute Notebook
```bash
jupyter notebook notebooks/04_volatility_spike_strategy.ipynb
```

### Modify Parameters

In the notebook, you can adjust:

```python
# Spike detection sensitivity
SPIKE_THRESHOLD = 1.5  # Try 1.0, 2.0

# Lookback period
LOOKBACK_WINDOW = 60  # Try 30, 90

# Straddle expiration
STRADDLE_DTE = 14  # Try 7, 21

# Date range
START_DATE = "2022-01-01"
END_DATE = "2024-12-31"
```

## Further Research

### Suggested Experiments

1. **Threshold Sensitivity**: Test 1.0σ, 1.5σ, 2.0σ thresholds
2. **Expiration Testing**: 1-week vs 2-week vs 1-month
3. **Strike Selection**: ATM vs 1% OTM
4. **Regime Filtering**: Only trade in certain VIX environments
5. **Multi-Symbol**: SPY, QQQ, IWM basket
6. **Hedging Strategies**: Long OTM options vs short delta
7. **Exit Rules**: 50% profit, trailing stops, time-based

### Questions to Answer

- What VIX level makes strategy most profitable?
- How does performance vary across market regimes?
- Can machine learning predict better entry points?
- What's optimal position size using Kelly Criterion?

## Academic Context

This strategy is based on well-documented phenomena:

1. **Volatility Risk Premium**: Implied vol > Realized vol on average
2. **Mean Reversion**: IV tends to revert after spikes
3. **Behavioral Finance**: Fear-driven overreaction
4. **Term Structure**: VIX futures contango/backwardation

## Disclaimer

**For educational purposes only.**

- Past performance doesn't guarantee future results
- Short options have unlimited risk
- Real trading involves slippage, commissions, margin requirements
- Consult a financial advisor before live trading

## Support

For questions or issues:
1. Review the notebook comments
2. Check `PERFORMANCE_METRICS_GUIDE.md`
3. See `DOLTHUB_INTEGRATION.md` for data issues
4. Open GitHub issue

---

**Built with**: DoltHub options data, Black-Scholes pricing, 12+ professional performance metrics

**License**: MIT - Use at your own risk
