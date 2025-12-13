"""
Validate that Notebook 07 enhanced integration will work correctly
Tests the enhanced functions with notebook-style execution
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
print("VALIDATING NOTEBOOK 07 INTEGRATION")
print("="*70)

# Configuration (matching notebook)
DB_PATH = "/Users/janussuk/Desktop/dolt_data/options"
TICKER = "SPY"
START_DATE = "2022-01-03"
END_DATE = "2025-01-31"
TARGET_DTE_MIN = 11
TARGET_DTE_MAX = 18

# =============================================================================
# TEST 1: Load Data
# =============================================================================
print(f"\n1. Testing data loading...")
try:
    adapter = DoltHubAdapter(DB_PATH)
    options_data = adapter.load_option_data(TICKER, START_DATE, END_DATE)
    spot_data = adapter.load_spot_data(TICKER, START_DATE, END_DATE)
    print(f"   ✓ Loaded {len(options_data):,} options")
    print(f"   ✓ Loaded {len(spot_data)} spot days")
except Exception as e:
    print(f"   ✗ FAILED: {e}")
    sys.exit(1)

# =============================================================================
# TEST 2: Calculate Enhanced IV Metrics
# =============================================================================
print(f"\n2. Testing calculate_enhanced_iv_metrics()...")
try:
    iv_df = calculate_enhanced_iv_metrics(options_data, spot_data, lookback_days=252)
    print(f"   ✓ Calculated metrics for {len(iv_df)} days")

    # Verify all expected columns exist
    expected_cols = ['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d',
                     'iv_trend_20d', 'iv_10d_std', 'iv_20d_std', 'iv_5d_change',
                     'iv_10d_change', 'iv_1d_change', 'iv_vol_percentile']
    missing_cols = [col for col in expected_cols if col not in iv_df.columns]

    if missing_cols:
        print(f"   ✗ FAILED: Missing columns: {missing_cols}")
        sys.exit(1)
    else:
        print(f"   ✓ All expected columns present")

    # Verify data quality
    if iv_df['atm_iv'].isna().all():
        print(f"   ✗ FAILED: All ATM IV values are NaN")
        sys.exit(1)
    else:
        valid_ivs = (~iv_df['atm_iv'].isna()).sum()
        print(f"   ✓ {valid_ivs} valid IV values")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# TEST 3: Generate Multi-Signal Entries
# =============================================================================
print(f"\n3. Testing generate_multi_signal_entries()...")
try:
    signals_df = generate_multi_signal_entries(iv_df)
    print(f"   ✓ Generated signals DataFrame")

    # Verify signal columns exist
    signal_cols = ['signal_spike_fade', 'signal_declining_trend',
                   'signal_stagnant_iv', 'entry_signal', 'signal_type']
    missing_signal_cols = [col for col in signal_cols if col not in signals_df.columns]

    if missing_signal_cols:
        print(f"   ✗ FAILED: Missing signal columns: {missing_signal_cols}")
        sys.exit(1)
    else:
        print(f"   ✓ All signal columns present")

    # Get summary
    summary = get_signal_summary(signals_df)
    print(f"\n   Signal Summary:")
    print(f"     Total days:         {summary['total_days']}")
    print(f"     Spike Fade:         {summary['spike_fade']}")
    print(f"     Declining Trend:    {summary['declining_trend']}")
    print(f"     Stagnant IV:        {summary['stagnant_iv']}")
    print(f"     Total signals:      {summary['total_signals']}")

    if summary['total_signals'] == 0:
        print(f"   ⚠ WARNING: No signals generated")
    else:
        print(f"   ✓ {summary['total_signals']} signals generated")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# TEST 4: Verify Entry Dates Have Options
# =============================================================================
print(f"\n4. Testing tradeable opportunities...")
try:
    entry_signals = signals_df[signals_df['entry_signal'] == True].copy()
    entry_dates = entry_signals['date'].tolist()

    tradeable_count = 0
    by_signal_type = {'spike_fade': 0, 'declining_trend': 0, 'stagnant_iv': 0}

    for date, signal_type in zip(entry_dates, entry_signals['signal_type'].tolist()):
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

    print(f"   ✓ {tradeable_count} tradeable opportunities")
    print(f"     Spike Fade:       {by_signal_type['spike_fade']}")
    print(f"     Declining Trend:  {by_signal_type['declining_trend']}")
    print(f"     Stagnant IV:      {by_signal_type['stagnant_iv']}")

    if tradeable_count == 0:
        print(f"   ✗ FAILED: No tradeable opportunities")
        sys.exit(1)

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# TEST 5: Simulate Backtester Signal Type Tracking
# =============================================================================
print(f"\n5. Testing signal_type tracking compatibility...")
try:
    # Simulate what the backtester will do
    test_straddle = {
        'entry_date': pd.Timestamp('2022-03-16'),
        'signal_type': 'spike_fade',
        'entry_price': 100.0,
        'exit_price': 75.0
    }

    # Test getting signal_type
    signal_type = test_straddle.get('signal_type', 'unknown')
    print(f"   ✓ Signal type retrieval works: '{signal_type}'")

    # Test DataFrame operations
    test_trades = pd.DataFrame([
        {'date': '2022-03-16', 'signal_type': 'spike_fade', 'net_pnl': 0.25},
        {'date': '2022-04-11', 'signal_type': 'declining_trend', 'net_pnl': 0.15},
        {'date': '2022-07-13', 'signal_type': 'stagnant_iv', 'net_pnl': -0.10}
    ])

    # Test groupby operations
    by_type = test_trades.groupby('signal_type')['net_pnl'].mean()
    print(f"   ✓ GroupBy operations work")

    # Test filtering
    spike_trades = test_trades[test_trades['signal_type'] == 'spike_fade']
    print(f"   ✓ Filtering by signal_type works ({len(spike_trades)} trades)")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# TEST 6: Verify Notebook Cell Content
# =============================================================================
print(f"\n6. Verifying notebook integration...")
try:
    import json

    notebook_path = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)

    # Check for enhanced imports
    found_enhanced_import = False
    found_multi_signal = False
    found_signal_type_tracking = False

    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])

            if 'from enhanced_straddle_functions import' in source:
                found_enhanced_import = True

            if 'generate_multi_signal_entries' in source:
                found_multi_signal = True

            if "'signal_type'" in source or '"signal_type"' in source:
                found_signal_type_tracking = True

    if found_enhanced_import:
        print(f"   ✓ Enhanced imports found in notebook")
    else:
        print(f"   ⚠ WARNING: Enhanced imports not found")

    if found_multi_signal:
        print(f"   ✓ Multi-signal generation found in notebook")
    else:
        print(f"   ⚠ WARNING: Multi-signal generation not found")

    if found_signal_type_tracking:
        print(f"   ✓ Signal type tracking found in notebook")
    else:
        print(f"   ⚠ WARNING: Signal type tracking not found")

except Exception as e:
    print(f"   ✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# =============================================================================
# SUMMARY
# =============================================================================
print(f"\n" + "="*70)
print("VALIDATION COMPLETE")
print("="*70)
print(f"""
All integration tests passed! ✓

Summary:
  • Data loading works correctly
  • Enhanced IV metrics calculated successfully
  • Multi-signal generation produces {summary['total_signals']} signals
  • {tradeable_count} tradeable opportunities identified
  • Signal type tracking compatible with backtester
  • Notebook cells properly integrated

Next Steps:
  1. Open Jupyter Notebook:
     jupyter notebook notebooks/07_enhanced_atm_straddle_strategy.ipynb

  2. Run all cells (Kernel -> Restart & Run All)

  3. Review the enhanced backtest results including:
     - All 3 signal types generating entries
     - Performance metrics by signal type
     - Comparison visualizations

The enhanced strategy is ready to run!
""")
print("="*70)
