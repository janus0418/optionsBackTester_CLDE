# Volatility Spike Strategy Notebook - Fixes Applied

## Problem Identified

The original notebook was designed to use **weekly options (5-10 DTE)**, but the DoltHub dataset only contains **monthly options** with DTEs around:
- 14-15 days (front month)
- 28-30 days (next month)
- 46-60 days (further out)

This caused the ATM IV extraction function to return zero results, breaking the entire notebook.

## Fixes Applied

### 1. Updated Cell 0 (Introduction)
- **Changed**: Added dataset note explaining monthly options constraint
- **Why**: Set user expectations about available data

### 2. Updated Cell 4 (Section Header)
- **Changed**: "ATM 1-Week IV" → "ATM Near-Term IV"
- **Why**: Accurately reflect we're using front-month (14-15 DTE) options

### 3. Fixed Cell 6 (ATM IV Extraction Function)
- **Changed**:
  - Function name: `get_atm_1week_iv` → `get_atm_nearterm_iv`
  - DTE filter: `(dte >= 5) & (dte <= 10)` → `(dte >= 12) & (dte <= 18)`
  - Column name: `atm_iv_1w` → `atm_iv_nearterm`
- **Why**: Match available data in DoltHub dataset

### 4. Updated Cell 8 (Statistics Calculation)
- **Changed**: All references from `atm_iv_1w` to `atm_iv_nearterm`
- **Why**: Match new column name from extraction function

### 5. Updated Cell 9 (Visualization)
- **Changed**: Plot labels and data references to use `atm_iv_nearterm`
- **Why**: Consistent naming throughout

### 6. Fixed Cell 11 (Mean Reversion Analysis)
- **Changed**:
  - Updated column references to `atm_iv_nearterm`
  - Added defensive `revert_date = None` initialization
  - Added 28-day marker to histogram
- **Why**: Fix column name and add relevant DTE markers

### 7. Updated Cell 12 (Strategy Description)
- **Changed**: Added note about using 28-30 DTE straddles
- **Why**: Clarify we're using next-month cycle

### 8. Fixed Cell 15 (Backtest Execution) - MAJOR FIX
- **Changed**:
  - Removed hardcoded `expiry = spike_date + Timedelta(days=14)`
  - Added dynamic expiration lookup from actual dataset
  - Filter for options with 25-35 DTE
  - Use `.mode()[0]` to get most common expiration
  - Added verbose logging for each trade
- **Why**: Use actual expirations from dataset instead of guessing dates

### 9. Updated Cell 29 (Conclusions)
- **Changed**: Removed "2-week expiry is appropriate" recommendation
- **Added**: Note about monthly options constraint
- **Why**: Reflect actual dataset characteristics

## Testing Results

### Short Test (6 months):
- ✅ Loaded 10,756 option records
- ✅ Calculated 69 days of ATM IV
- ✅ Identified 2 spike events
- ✅ Executed 2 straddle trades
- ✅ Backtest completed successfully
- ✅ All metrics calculated correctly

### Full Test (2 years: 2022-2024):
- ✅ Loaded 44,498 option records
- ✅ Calculated 278 days of ATM IV
- ✅ Identified 9 spike events
- ✅ Executed 9 straddle trades
- ✅ Backtest completed successfully
- ✅ All 22+ performance metrics working

## How to Run the Fixed Notebook

```bash
cd "Options Backtester"
source .venv/bin/activate
jupyter notebook notebooks/04_volatility_spike_strategy.ipynb
```

Then run all cells in sequence (Cell → Run All).

## Expected Behavior

The notebook will now:
1. ✓ Load SPY options data from DoltHub
2. ✓ Extract ATM near-term (14-15 DTE) implied volatility
3. ✓ Calculate rolling statistics and identify IV spikes
4. ✓ Visualize spike events and z-scores
5. ✓ Analyze mean reversion behavior
6. ✓ Execute backtest selling 28-30 DTE straddles on spike days
7. ✓ Display comprehensive performance metrics
8. ✓ Show loss analysis and risk metrics

## Strategy Performance Notes

The strategy may show losses during certain periods (like 2022-2023) due to:
- Market volatility events (Fed rate hikes, banking crisis)
- Short volatility strategies suffer during sustained high volatility
- This is **expected behavior** - short vol strategies have tail risk

The notebook is working correctly even if the strategy loses money. The purpose is to demonstrate:
- Professional backtesting methodology
- Comprehensive performance metrics
- Risk analysis techniques

## Key Dataset Constraints

1. **Monthly Options Only**: DoltHub has monthly cycles, not weeklies
2. **Limited DTEs**: Only ~14, 28, 46+ day options available
3. **Sparse Data**: Not every trading day has options data
4. **Date Alignment**: Must match option dates to spot price dates carefully

## Files Modified

- `/Users/janussuk/Desktop/Options Backtester/notebooks/04_volatility_spike_strategy.ipynb`

## All Errors Fixed ✅

The notebook now runs completely error-free from start to finish with realistic data from the DoltHub options dataset.
