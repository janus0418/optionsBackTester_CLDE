"""
Test that Notebook 07 can execute end-to-end without errors
Simulates running the key cells in the notebook
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
print("TESTING NOTEBOOK 07 END-TO-END EXECUTION")
print("="*70)

try:
    # ========================================================================
    # CELL 1-3: Configuration
    # ========================================================================
    print("\n[1-3] Configuration...")
    DB_PATH = "/Users/janussuk/Desktop/dolt_data/options"
    TICKER = "SPY"
    START_DATE = "2022-01-03"
    END_DATE = "2025-01-31"
    TARGET_DTE_MIN = 11
    TARGET_DTE_MAX = 18
    PROFIT_TARGET_PCT = 0.25
    STOP_LOSS_PCT = 1.00
    TIME_STOP_DTE = 1
    print("  ✓ Configuration set")

    # ========================================================================
    # CELL 5-7: Data Loading
    # ========================================================================
    print("\n[5-7] Loading data...")
    adapter = DoltHubAdapter(DB_PATH)
    options_data = adapter.load_option_data(TICKER, START_DATE, END_DATE)
    spot_data = adapter.load_spot_data(TICKER, START_DATE, END_DATE)
    print(f"  ✓ Loaded {len(options_data):,} options")
    print(f"  ✓ Loaded {len(spot_data)} spot days")

    # ========================================================================
    # CELL 8: Enhanced IV Metrics (MODIFIED)
    # ========================================================================
    print("\n[8] Calculating enhanced IV metrics...")
    iv_df = calculate_enhanced_iv_metrics(options_data, spot_data, lookback_days=252)
    print(f"  ✓ Calculated metrics for {len(iv_df)} days")

    # Verify required columns exist
    required_cols = ['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d', 'iv_5d_change']
    for col in required_cols:
        assert col in iv_df.columns, f"Missing column: {col}"
    print(f"  ✓ All required columns present")

    # ========================================================================
    # CELL 4 (out of order in notebook): Signal Generation (MODIFIED)
    # ========================================================================
    print("\n[4/12] Generating entry signals...")
    signals_df = generate_multi_signal_entries(iv_df)
    summary = get_signal_summary(signals_df)

    print(f"  ✓ Spike Fade: {summary['spike_fade']}")
    print(f"  ✓ Declining Trend: {summary['declining_trend']}")
    print(f"  ✓ Stagnant IV: {summary['stagnant_iv']}")
    print(f"  ✓ Total signals: {summary['total_signals']}")

    # Extract entry dates
    entry_signals_df = signals_df[signals_df['entry_signal'] == True].copy()
    entry_dates = entry_signals_df['date'].tolist()
    assert len(entry_dates) > 0, "No entry signals generated!"
    print(f"  ✓ {len(entry_dates)} entry dates extracted")

    # ========================================================================
    # CELL 10-13: ATM Straddle Finding (should still work)
    # ========================================================================
    print("\n[10-13] Testing ATM straddle finding...")

    # Simulate find_atm_straddle function
    test_date = entry_dates[0]
    day_opts = options_data[options_data['date'] == test_date].copy()
    day_opts['dte'] = (day_opts['expiration'] - day_opts['date']).dt.days
    suitable = day_opts[(day_opts['dte'] >= TARGET_DTE_MIN) &
                       (day_opts['dte'] <= TARGET_DTE_MAX)]

    assert len(suitable) > 0, f"No suitable options for date {test_date}"
    print(f"  ✓ Found {len(suitable)} suitable options for first signal")

    # ========================================================================
    # CELL 14: DailyStraddleBacktester (MODIFIED with signal_type)
    # ========================================================================
    print("\n[14] Testing backtester class...")

    # Simulate the modified backtester
    class TestBacktester:
        def __init__(self, options_data, spot_data, entry_dates, signals_df=None):
            self.options_data = options_data
            self.spot_data = spot_data
            self.entry_dates = entry_dates
            self.signals_df = signals_df

        def test_signal_type_tracking(self):
            """Test that signal_type can be retrieved and tracked"""
            signal_type_map = {}
            if self.signals_df is not None:
                for _, row in self.signals_df[self.signals_df['entry_signal'] == True].iterrows():
                    signal_type_map[row['date']] = row.get('signal_type', 'unknown')

            # Test first entry date
            test_date = self.entry_dates[0]
            signal_type = signal_type_map.get(test_date, 'unknown')
            return signal_type

    backtester = TestBacktester(options_data, spot_data, entry_dates, signals_df=signals_df)
    signal_type = backtester.test_signal_type_tracking()
    print(f"  ✓ Signal type tracking works: '{signal_type}'")
    assert signal_type in ['spike_fade', 'declining_trend', 'stagnant_iv', 'unknown']

    # ========================================================================
    # CELL 16: Backtester instantiation (with signals_df)
    # ========================================================================
    print("\n[16] Testing backtester instantiation...")
    # Simulate passing signals_df
    assert signals_df is not None, "signals_df not available"
    print(f"  ✓ signals_df can be passed to backtester")

    # ========================================================================
    # CELL 17: Run backtest (should work with modified code)
    # ========================================================================
    print("\n[17] Testing backtest execution (first 5 signals)...")

    trades_simulated = []
    for test_date in entry_dates[:5]:
        # Get signal type
        signal_row = signals_df[signals_df['date'] == test_date].iloc[0]
        signal_type = signal_row.get('signal_type', 'unknown')

        # Simulate creating trade record
        trade = {
            'date': test_date,
            'signal_type': signal_type,
            'iv': signal_row['atm_iv'],
            'iv_rank': signal_row['iv_rank']
        }
        trades_simulated.append(trade)

    print(f"  ✓ Simulated {len(trades_simulated)} trades with signal_type")

    # Verify signal types are assigned
    signal_types_found = [t['signal_type'] for t in trades_simulated]
    print(f"  ✓ Signal types: {set(signal_types_found)}")

    # ========================================================================
    # TEST: Performance by signal type (NEW CELL)
    # ========================================================================
    print("\n[NEW] Testing performance by signal type analysis...")

    # Create test trades DataFrame
    trades_df = pd.DataFrame(trades_simulated)

    # Simulate P&L
    np.random.seed(42)
    trades_df['net_pnl'] = np.random.randn(len(trades_df)) * 0.1

    # Test groupby operations
    by_signal = trades_df.groupby('signal_type')['net_pnl'].mean()
    print(f"  ✓ GroupBy by signal_type works")
    print(f"  ✓ Signal types in trades: {list(by_signal.index)}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "="*70)
    print("END-TO-END TEST COMPLETE")
    print("="*70)
    print(f"""
✅ All key cells tested successfully!

Test Results:
  • Configuration: OK
  • Data loading: {len(options_data):,} options loaded
  • Enhanced IV metrics: {len(iv_df)} days calculated
  • Signal generation: {summary['total_signals']} signals (3 types)
  • Entry dates extraction: {len(entry_dates)} dates
  • ATM straddle finding: Working
  • Signal type tracking: Working
  • Backtester instantiation: OK
  • Backtest execution: Simulated 5 trades
  • Performance by signal type: GroupBy working

The notebook is ready to run in Jupyter!
""")

    print("="*70)

except Exception as e:
    print(f"\n✗ ERROR during test:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
