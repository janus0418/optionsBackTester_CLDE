# Comprehensive Performance Metrics Guide

## Overview

The backtester now includes a comprehensive suite of performance metrics used by professional algorithmic traders. These metrics provide deep insights into strategy performance, risk characteristics, and return distribution.

## New Metrics Implemented

### 1. Omega Ratio

**Formula**: `Ω = Sum(Gains above threshold) / Sum(Losses below threshold)`

**What it measures**: Probability-weighted ratio of gains versus losses.

**Advantages over Sharpe**:
- Considers entire return distribution, not just mean and variance
- Doesn't assume normal distribution
- Captures all higher moments (skewness, kurtosis)
- Better for non-normal returns (like options strategies)

**Interpretation**:
- Ω > 1.0: Good (more gains than losses)
- Ω > 1.5: Excellent
- Ω > 2.0: Outstanding

**Usage**:
```python
omega = metrics.omega_ratio(threshold=0.0)
print(f"Omega Ratio: {omega:.2f}")
```

**Source**: [The Omega Ratio: A Much Better Performance Metric](https://mechanicalforex.com/2016/06/the-omega-ratio-a-much-better-performance-metric-than-the-sharpe.html)

---

### 2. Sterling Ratio

**Formula**: `Sterling = Annual Return / Average(N Largest Drawdowns)`

**What it measures**: Return relative to average of worst drawdowns.

**Why it's useful**:
- More stable than Calmar (which uses single worst drawdown)
- Accounts for multiple drawdown periods
- Better for strategies with multiple risk events

**Interpretation**:
- Sterling > 1.0: Acceptable
- Sterling > 2.0: Good
- Sterling > 3.0: Excellent

**Usage**:
```python
sterling = metrics.sterling_ratio(lookback_years=3)
print(f"Sterling Ratio: {sterling:.2f}")
```

---

### 3. Ulcer Index

**Formula**: `UI = sqrt(mean(drawdown²))`

**What it measures**: "Pain" of drawdowns - both depth and duration.

**Why it's useful**:
- Captures psychological pain of holding through drawdowns
- Penalizes both deep and prolonged losses
- Lower is better

**Interpretation**:
- UI < 5%: Low pain
- UI 5-10%: Moderate
- UI > 10%: High pain

**Usage**:
```python
ulcer = metrics.ulcer_index()
print(f"Ulcer Index: {ulcer:.2f}%")
```

---

### 4. Value at Risk (VaR)

**Formula**: `VaR = -Percentile(returns, 1-confidence)`

**What it measures**: Maximum expected loss at given confidence level.

**Common confidence levels**:
- 95%: Standard
- 99%: Conservative
- 99.9%: Extreme events

**Interpretation**:
"We expect to lose no more than X% on 95% of days"

**Usage**:
```python
var_95 = metrics.value_at_risk(confidence=0.95)
var_99 = metrics.value_at_risk(confidence=0.99)
print(f"Daily VaR (95%): {var_95:.2%}")
print(f"Daily VaR (99%): {var_99:.2%}")
```

---

### 5. Conditional VaR (CVaR / Expected Shortfall)

**Formula**: `CVaR = -Mean(returns below VaR threshold)`

**What it measures**: Expected loss when VaR is exceeded.

**Why it's better than VaR**:
- Coherent risk measure
- Tells you HOW BAD losses are when they happen
- More useful for risk management

**Interpretation**:
"When we have a bad day (worse than VaR), we expect to lose X%"

**Usage**:
```python
cvar_95 = metrics.conditional_var(confidence=0.95)
print(f"Daily CVaR (95%): {cvar_95:.2%}")
```

---

### 6. Skewness

**Formula**: `Skewness = E[(X - μ)³] / σ³`

**What it measures**: Asymmetry of return distribution.

**Interpretation**:
- Skew = 0: Symmetric (normal distribution)
- Skew < 0: **Negative skew** - More extreme losses than gains (BAD for most strategies)
- Skew > 0: **Positive skew** - More extreme gains than losses (GOOD)

**Common values**:
- Short options: Usually negative (-0.5 to -2.0)
- Long options: Usually positive (0.5 to 2.0)

**Usage**:
```python
skew = metrics.skewness()
if skew < -0.5:
    print(f"⚠️ Negative skew ({skew:.2f}): Tail risk present")
```

---

### 7. Kurtosis (Excess)

**Formula**: `Kurtosis = E[(X - μ)⁴] / σ⁴ - 3`

**What it measures**: "Fat-tailedness" of distribution.

**Interpretation**:
- Kurtosis = 0: Normal distribution
- Kurtosis > 0: Fat tails - more extreme events than normal
- Kurtosis < 0: Thin tails - fewer extreme events

**Common values**:
- Options strategies: Often 3-10+ (fat tails)
- Stock returns: Often 3-5

**Usage**:
```python
kurt = metrics.kurtosis()
if kurt > 3:
    print(f"⚠️ High kurtosis ({kurt:.2f}): Fat tails - expect outliers")
```

---

### 8. Recovery Factor

**Formula**: `Recovery = Total Return / |Max Drawdown|`

**What it measures**: How much profit relative to worst drawdown.

**Why it's useful**:
- Similar to Calmar but uses total return instead of annual
- Shows if gains justify the pain
- High recovery = quick bounce back

**Interpretation**:
- Recovery > 2.0: Good
- Recovery > 5.0: Excellent
- Recovery > 10.0: Outstanding

**Usage**:
```python
recovery = metrics.recovery_factor()
print(f"Recovery Factor: {recovery:.2f}")
```

---

### 9. Expectancy

**Formula**: `Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)`

**What it measures**: Expected value per trade.

**Why it's useful**:
- Simple expected value calculation
- Positive = profitable long-term
- Can be scaled to position size

**Usage**:
```python
exp = metrics.expectancy()
print(f"Expectancy: ${exp * initial_capital:,.2f} per trade")
```

---

### 10. Average Win/Loss Ratio

**Formula**: `Win/Loss = Average Win / Average Loss`

**What it measures**: Size of average win vs average loss.

**Interpretation**:
- Ratio > 1: Wins larger than losses
- Ratio < 1: Losses larger than wins (need high win rate)
- Ratio × Win Rate should be > 1 for profitability

**Usage**:
```python
wl_ratio = metrics.average_win_loss_ratio()
win_rate = metrics.win_rate()
print(f"Win/Loss: {wl_ratio:.2f}")
print(f"Combined: {wl_ratio * win_rate:.2f}")
```

---

### 11. Consecutive Wins/Losses

**What it measures**: Maximum streak of consecutive profitable/losing days.

**Why it's useful**:
- Risk management for position sizing
- Psychological preparedness
- Identifies unstable periods

**Usage**:
```python
max_wins = metrics.max_consecutive_wins()
max_losses = metrics.max_consecutive_losses()
print(f"Max win streak: {max_wins} days")
print(f"Max loss streak: {max_losses} days")
```

---

### 12. Information Ratio

**Formula**: `IR = (Portfolio Return - Benchmark Return) / Tracking Error`

**What it measures**: Excess return per unit of active risk.

**Why it's useful**:
- Shows skill vs benchmark
- Higher IR = better active management
- IR > 0.5 is good, IR > 1.0 is excellent

**Usage**:
```python
# Compare to SPY
benchmark_returns = spy_returns
ir = metrics.information_ratio(benchmark_returns)
print(f"Information Ratio: {ir:.2f}")
```

---

## Existing Metrics (Previously Implemented)

### Total Return
Simple percentage return over the period.

### Annualized Return (CAGR)
Compound Annual Growth Rate.

### Annualized Volatility
Standard deviation of returns, annualized.

### Sharpe Ratio
`(Return - Risk Free Rate) / Volatility`

### Sortino Ratio
Like Sharpe but only penalizes downside volatility.

### Calmar Ratio
`Annual Return / |Max Drawdown|`

### Max Drawdown
Largest peak-to-trough decline.

### Win Rate
Percentage of positive return days.

### Profit Factor
`Sum of Wins / Sum of Losses`

---

## How to Use Multiple Metrics

### Recommended Composite Score

Many institutions use a weighted composite:

```python
score = (
    0.25 * sharpe_ratio +
    0.25 * sortino_ratio +
    0.30 * calmar_ratio +
    0.20 * (cvar_ratio)  # 1/CVaR
)
```

### Quick Health Check

```python
def strategy_health_check(metrics):
    warnings = []

    # Check Sharpe
    if metrics.sharpe_ratio() < 1.0:
        warnings.append("⚠️ Low Sharpe (<1.0)")

    # Check drawdown
    if metrics.max_drawdown()[0] < -0.20:
        warnings.append("⚠️ Large drawdown (>20%)")

    # Check tail risk
    if metrics.skewness() < -0.5:
        warnings.append("⚠️ Negative skew (tail risk)")

    if metrics.kurtosis() > 5:
        warnings.append("⚠️ Fat tails (extreme events)")

    # Check profitability
    if metrics.win_rate() < 0.4:
        warnings.append("⚠️ Low win rate (<40%)")

    if metrics.expectancy() < 0:
        warnings.append("⚠️ Negative expectancy")

    return warnings
```

---

## When to Use Which Metric

### For Risk-Adjusted Returns
- **Sharpe**: Standard, good for normal distributions
- **Sortino**: When downside risk matters most
- **Omega**: Best for non-normal distributions (options)
- **Calmar/Sterling**: When drawdowns are key concern

### For Drawdown Analysis
- **Max Drawdown**: Worst case scenario
- **Calmar**: Return vs worst drawdown
- **Sterling**: More stable, uses average of worst
- **Ulcer**: Captures pain of holding through drawdowns

### For Tail Risk
- **VaR**: Maximum expected loss at confidence level
- **CVaR**: Expected loss when VaR exceeded
- **Skewness**: Direction of tail risk
- **Kurtosis**: Likelihood of extreme events

### For Trade-Level Analysis
- **Win Rate**: Basic profitability
- **Profit Factor**: Wins vs losses
- **Expectancy**: Expected value per trade
- **Win/Loss Ratio**: Size of wins vs losses

---

## References

1. [Decoding Risk-Adjusted Returns: Sharpe, Sortino, Calmar & Omega Ratios](https://medium.com/@wl8380/decoding-risk-adjusted-returns-the-guide-to-sharpe-sortino-calmar-omega-ratios-5245d725d23f)

2. [Measuring Risk-Adjusted Returns: Beyond Sharpe Ratio](https://breakingalpha.io/insights/measuring-risk-adjusted-returns-beyond-sharpe-ratio.html)

3. [The Omega Ratio: A Much Better Performance Metric](https://mechanicalforex.com/2016/06/the-omega-ratio-a-much-better-performance-metric-than-the-sharpe.html)

4. [5 Key Metrics to Evaluate Trading Algorithms](https://www.utradealgos.com/blog/5-key-metrics-to-evaluate-the-performance-of-your-trading-algorithms)

5. [Performance Metrics for Algorithmic Trading](https://www.quantstart.com/articles/Sharpe-Ratio-for-Algorithmic-Trading-Performance-Measurement/)

---

## Example: Complete Analysis

```python
# Run backtest
results = engine.run()

# Calculate metrics
metrics = PerformanceMetrics(results, risk_free_rate=0.05)

# Print full summary (includes all metrics)
metrics.print_summary()

# Custom analysis
print("\n🔍 Risk Analysis:")
print(f"  Omega Ratio: {metrics.omega_ratio():.2f}")
print(f"  VaR (95%): {metrics.value_at_risk(0.95):.2%}")
print(f"  CVaR (95%): {metrics.conditional_var(0.95):.2%}")
print(f"  Skewness: {metrics.skewness():.2f}")
print(f"  Kurtosis: {metrics.kurtosis():.2f}")

# Health check
warnings = strategy_health_check(metrics)
if warnings:
    print("\n⚠️ Strategy Warnings:")
    for w in warnings:
        print(f"  {w}")
```

---

**Note**: All metrics are accessible through the `PerformanceMetrics` class. See `backtester/metrics.py` for implementation details.
