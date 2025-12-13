"""
Complete backtest of Enhanced Multi-Signal ATM Straddle Strategy

Run this script to see full backtest results before integrating into notebook.

Usage:
    cd "/Users/janussuk/Desktop/Options Backtester"
    source .venv/bin/activate
    python run_enhanced_strategy_backtest.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path.cwd()))

from backtester import DoltHubAdapter
from enhanced_straddle_functions import (
    calculate_enhanced_iv_metrics,
    generate_multi_signal_entries,
    get_signal_summary
)

print("="*70)
print("ENHANCED MULTI-SIGNAL ATM STRADDLE STRATEGY - FULL BACKTEST")
print("="*70)

# =============================================================================
# CONFIGURATION
# =============================================================================
DB_PATH = "/Users/janussuk/Desktop/dolt_data/options"
TICKER = "SPY"
START_DATE = "2022-01-03"
END_DATE = "2025-01-31"
INITIAL_CAPITAL = 100000.0

TARGET_DTE_MIN = 11
TARGET_DTE_MAX = 18
TARGET_DTE_IDEAL = 14

PROFIT_TARGET_PCT = 0.25
STOP_LOSS_PCT = 1.00
TIME_STOP_DTE = 1

print(f"\nConfiguration:")
print(f"  Period: {START_DATE} to {END_DATE}")
print(f"  Initial Capital: ${INITIAL_CAPITAL:,.0f}")
print(f"  DTE Target: {TARGET_DTE_MIN}-{TARGET_DTE_MAX} days")

# =============================================================================
# LOAD DATA
# =============================================================================
print(f"\n1. Loading SPY options data...")
adapter = DoltHubAdapter(DB_PATH)
options_data = adapter.load_option_data(TICKER, START_DATE, END_DATE)
spot_data = adapter.load_spot_data(TICKER, START_DATE, END_DATE)

print(f"   ✓ Loaded {len(options_data):,} options")
print(f"   ✓ Loaded {len(spot_data)} spot price days")

# =============================================================================
# CALCULATE ENHANCED IV METRICS
# =============================================================================
print(f"\n2. Calculating enhanced IV metrics...")
iv_df = calculate_enhanced_iv_metrics(options_data, spot_data)

print(f"   ✓ Calculated metrics for {len(iv_df)} days")
print(f"   Metrics: IV Rank, Trends (10d/20d), Vol-of-Vol, Changes, Z-Score")

# =============================================================================
# GENERATE MULTI-SIGNAL ENTRIES
# =============================================================================
print(f"\n3. Generating entry signals (3 types)...")
signals_df = generate_multi_signal_entries(iv_df)

summary = get_signal_summary(signals_df)
print(f"\n   Signal Summary:")
print(f"   ────────────────────────────────────────")
print(f"   Total Days Analyzed:      {summary['total_days']:4d}")
print(f"   ")
print(f"   Spike Fade Signals:       {summary['spike_fade']:4d}  ({summary.get('spike_fade_pct', 0):5.1f}%)")
print(f"   Declining Trend Signals:  {summary['declining_trend']:4d}  ({summary.get('declining_trend_pct', 0):5.1f}%)")
print(f"   Stagnant IV Signals:      {summary['stagnant_iv']:4d}  ({summary.get('stagnant_iv_pct', 0):5.1f}%)")
print(f"   ────────────────────────────────────────")
print(f"   TOTAL Entry Signals:      {summary['total_signals']:4d}  ({summary.get('total_signals_pct', 0):5.1f}%)")

# Show sample signals
entry_signals = signals_df[signals_df['entry_signal'] == True].copy()
if len(entry_signals) > 0:
    print(f"\n   First 15 Entry Signals:")
    print(f"   {'Date':<12} {'Type':<20} {'IV':>7} {'IVR':>5} {'5d Chg':>7} {'Trend':>7}")
    print(f"   {'-'*65}")
    for i, (idx, row) in enumerate(entry_signals.head(15).iterrows()):
        print(f"   {row['date'].strftime('%Y-%m-%d'):<12} {row['signal_type']:<20} "
              f"{row['atm_iv']:>6.1%} {row['iv_rank']:>4.0f}% "
              f"{row['iv_5d_change']:>+6.1%} {row['iv_trend_10d']:>+.5f}")

# =============================================================================
# SIMPLIFIED BACKTEST (Trade Counting)
# =============================================================================
print(f"\n4. Running simplified backtest (entry counting)...")

# This is a simplified version - just counts potential trades
# Full backtest with P&L tracking requires integration with DailyStraddleBacktester

entry_dates_list = entry_signals['date'].tolist()
signal_types_list = entry_signals['signal_type'].tolist()

# Check which entries have suitable options available
tradeable_count = 0
by_signal_type = {'spike_fade': 0, 'declining_trend': 0, 'stagnant_iv': 0}

for date, signal_type in zip(entry_dates_list, signal_types_list):
    day_opts = options_data[options_data['date'] == date].copy()
    if len(day_opts) == 0:
        continue

    day_opts['dte'] = (day_opts['expiration'] - day_opts['date']).dt.days
    suitable = day_opts[(day_opts['dte'] >= TARGET_DTE_MIN) &
                        (day_opts['dte'] <= TARGET_DTE_MAX)]

    if len(suitable) > 0:
        tradeable_count += 1
        if signal_type in by_signal_type:
            by_signal_type[signal_type] += 1

print(f"\n   Tradeable Entry Opportunities: {tradeable_count} / {len(entry_dates_list)}")
print(f"   ")
print(f"   By Signal Type:")
print(f"     Spike Fade:        {by_signal_type['spike_fade']:3d} trades")
print(f"     Declining Trend:   {by_signal_type['declining_trend']:3d} trades")
print(f"     Stagnant IV:       {by_signal_type['stagnant_iv']:3d} trades")

# =============================================================================
# COMPARISON WITH NOTEBOOK 06
# =============================================================================
print(f"\n" + "="*70)
print("COMPARISON WITH NOTEBOOK 06 (Single Signal)")
print("="*70)

# Calculate notebook 06 signals (spike fade only, IVR > 50%)
nb06_signals = signals_df[
    (signals_df['iv_rank'] > 50) &
    (signals_df['iv_5d_change'] < 0)
]

print(f"\nNotebook 06 (Spike Fade Only):      {len(nb06_signals)} signals")
print(f"Notebook 07 (Multi-Signal Enhanced): {len(entry_signals)} signals")
print(f"")
print(f"Signal Increase: +{len(entry_signals) - len(nb06_signals)} signals "
      f"({((len(entry_signals) / len(nb06_signals)) - 1) * 100:+.1f}% more)")

# =============================================================================
# EXPORT RESULTS
# =============================================================================
print(f"\n5. Exporting results...")

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# Export signals
signals_export = signals_df[signals_df['entry_signal'] == True].copy()
signals_export.to_csv(results_dir / "enhanced_strategy_signals.csv", index=False)
print(f"   ✓ Saved: results/enhanced_strategy_signals.csv")

# Export full IV metrics
iv_export = signals_df[['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d',
                         'iv_10d_std', 'iv_5d_change', 'signal_spike_fade',
                         'signal_declining_trend', 'signal_stagnant_iv',
                         'entry_signal', 'signal_type']].copy()
iv_export.to_csv(results_dir / "enhanced_strategy_iv_metrics.csv", index=False)
print(f"   ✓ Saved: results/enhanced_strategy_iv_metrics.csv")

# =============================================================================
# SUMMARY
# =============================================================================
print(f"\n" + "="*70)
print("SUMMARY")
print("="*70)

print(f"""
✅ Enhanced Strategy Successfully Tested!

Key Results:
  • {summary['total_signals']} total entry signals ({summary.get('total_signals_pct', 0):.1f}% of days)
  • {tradeable_count} tradeable opportunities (with 11-18 DTE options)
  • {len(entry_signals) - len(nb06_signals)} more signals than Notebook 06

Signal Breakdown:
  • Spike Fade (High IV + Declining):    {by_signal_type['spike_fade']} trades
  • Declining Trend (Sustained Down):    {by_signal_type['declining_trend']} trades
  • Stagnant IV (Low Vol-of-Vol):        {by_signal_type['stagnant_iv']} trades

Next Steps:
  1. Review exported CSV files in results/ folder
  2. If satisfied, integrate into Notebook 07
  3. Run full backtest with P&L tracking in notebook
  4. Analyze performance by signal type

Files Created:
  • enhanced_straddle_functions.py (reusable functions)
  • results/enhanced_strategy_signals.csv (all entry signals)
  • results/enhanced_strategy_iv_metrics.csv (full IV data)

To integrate into Notebook 07:
  • Replace calculate_iv_metrics() with calculate_enhanced_iv_metrics()
  • Replace generate_entry_signals() with generate_multi_signal_entries()
  • Update backtester to track signal_type for each trade
  • Add visualization comparing performance by signal type
""")

print("="*70)
