"""
Carefully integrate enhanced strategy into Notebook 07
This script properly modifies only the necessary cells
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")

print("="*70)
print("INTEGRATING ENHANCED STRATEGY (CAREFUL APPROACH)")
print("="*70)

# Load notebook
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"\nLoaded {len(notebook['cells'])} cells")

# Track modifications
modifications = []

# ===========================================================================
# STEP 1: Update title cell
# ===========================================================================
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        if '# Daily Short ATM Straddle' in source:
            print(f"\nStep 1: Updating title (cell {i})")
            new_source = source.replace(
                '# Daily Short ATM Straddle Strategy',
                '# Enhanced Multi-Signal ATM Straddle Strategy'
            )
            # Add note about enhancement
            new_source = new_source.replace(
                'This notebook implements a',
                'This notebook implements an enhanced'
            )
            if new_source != source:
                cell['source'] = [new_source]
                modifications.append(f"Cell {i}: Updated title")
            break

# ===========================================================================
# STEP 2: Find and replace calculate_iv_metrics function
# ===========================================================================
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Look for the IV metrics calculation function definition
        if 'def calculate_iv_metrics' in source:
            print(f"\nStep 2: Replacing IV metrics function (cell {i})")

            # Replace entire function with import
            new_source = """# === IV METRICS CALCULATION ===
# Import enhanced IV metrics function
from enhanced_straddle_functions import calculate_enhanced_iv_metrics

# Calculate comprehensive IV metrics (21 metrics vs 8 in original)
print("\\nCalculating enhanced IV metrics...")
iv_df = calculate_enhanced_iv_metrics(options_data, spot_data, lookback_days=252)
print(f"✓ Calculated enhanced metrics for {len(iv_df)} days")

# Show first few rows
print("\\nFirst 5 days of IV metrics:")
print(iv_df[['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d', 'iv_5d_change']].head())
"""
            cell['source'] = [new_source]
            modifications.append(f"Cell {i}: Replaced with calculate_enhanced_iv_metrics()")
            break

# ===========================================================================
# STEP 3: Find and replace signal generation
# ===========================================================================
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Look for signal generation (IV_RANK_THRESHOLD or similar)
        if 'IV_RANK_THRESHOLD' in source or ('entry_signal' in source and 'iv_rank' in source and '>' in source):
            print(f"\nStep 3: Replacing signal generation (cell {i})")

            new_source = """# === ENTRY SIGNAL GENERATION ===
# Import multi-signal generation functions
from enhanced_straddle_functions import generate_multi_signal_entries, get_signal_summary

print("\\nGenerating entry signals (3 types: Spike Fade, Declining Trend, Stagnant IV)...")
signals_df = generate_multi_signal_entries(iv_df)

# Get summary statistics
summary = get_signal_summary(signals_df)

print("\\n" + "="*70)
print("ENTRY SIGNAL SUMMARY")
print("="*70)
print(f"Total Days Analyzed:        {summary['total_days']:4d}")
print(f"")
print(f"Signal Types:")
print(f"  Spike Fade (High IV):     {summary['spike_fade']:4d}  ({summary.get('spike_fade_pct', 0):5.1f}%)")
print(f"  Declining Trend (Down):   {summary['declining_trend']:4d}  ({summary.get('declining_trend_pct', 0):5.1f}%)")
print(f"  Stagnant IV (Stable):     {summary['stagnant_iv']:4d}  ({summary.get('stagnant_iv_pct', 0):5.1f}%)")
print(f"  " + "-"*50)
print(f"  TOTAL Entry Signals:      {summary['total_signals']:4d}  ({summary.get('total_signals_pct', 0):5.1f}%)")

# Extract entry dates and signal info for backtesting
entry_signals_df = signals_df[signals_df['entry_signal'] == True].copy()
entry_dates = entry_signals_df['date'].tolist()

print(f"\\nFirst 10 Entry Signals:")
print(f"{'Date':<12} {'Type':<20} {'IV':>7} {'IVR':>5}")
print("-"*50)
for idx, row in entry_signals_df.head(10).iterrows():
    print(f"{row['date'].strftime('%Y-%m-%d'):<12} {row['signal_type']:<20} "
          f"{row['atm_iv']:>6.1%} {row['iv_rank']:>4.0f}%")
"""
            cell['source'] = [new_source]
            modifications.append(f"Cell {i}: Replaced with generate_multi_signal_entries()")
            break

# ===========================================================================
# STEP 4: Update DailyStraddleBacktester to track signal_type
# ===========================================================================
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Look for DailyStraddleBacktester class
        if 'class DailyStraddleBacktester' in source:
            print(f"\nStep 4: Updating backtester class (cell {i})")

            # Check if it already has signal_type tracking
            if "'signal_type':" not in source:
                # Need to add signal_type tracking
                # Find run_backtest method and modify it

                lines = source.split('\n')
                new_lines = []
                in_run_backtest = False
                added_signal_map = False

                for j, line in enumerate(lines):
                    # Track when we're in run_backtest method
                    if 'def run_backtest(self' in line:
                        in_run_backtest = True
                        new_lines.append(line)
                        continue

                    # Add signal_type mapping at start of run_backtest
                    if in_run_backtest and not added_signal_map and 'entry_dates_set = set(' in line:
                        new_lines.append(line)
                        # Add signal type mapping
                        indent = len(line) - len(line.lstrip())
                        new_lines.append('')
                        new_lines.append(' ' * indent + '# Create mapping of date -> signal_type')
                        new_lines.append(' ' * indent + 'signal_type_map = {}')
                        new_lines.append(' ' * indent + 'if hasattr(self, "signals_df"):')
                        new_lines.append(' ' * (indent + 4) + 'for _, row in self.signals_df[self.signals_df["entry_signal"] == True].iterrows():')
                        new_lines.append(' ' * (indent + 8) + 'signal_type_map[row["date"]] = row.get("signal_type", "unknown")')
                        added_signal_map = True
                        continue

                    # Add signal_type to straddle when it's found
                    if in_run_backtest and 'if straddle:' in line and 'signal_type' not in line:
                        new_lines.append(line)
                        # Add signal_type assignment
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * (indent + 4) + '# Add signal type to straddle')
                        new_lines.append(' ' * (indent + 4) + 'straddle["signal_type"] = signal_type_map.get(date, "unknown")')
                        continue

                    # Add signal_type to trade record
                    if "'net_pnl':" in line and "'signal_type':" not in source[source.find('def run_backtest'):]:
                        new_lines.append(line)
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + "'signal_type': straddle.get('signal_type', 'unknown'),")
                        continue

                    new_lines.append(line)

                new_source = '\n'.join(new_lines)
                cell['source'] = [new_source]
                modifications.append(f"Cell {i}: Added signal_type tracking to backtester")
            else:
                print(f"  ✓ Already has signal_type tracking")

#============================================================================
# STEP 5: Update backtester instantiation to pass signals_df
# ===========================================================================
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Look for backtester instantiation
        if 'backtester = DailyStraddleBacktester' in source:
            print(f"\nStep 5: Updating backtester instantiation (cell {i})")

            # Check if signals_df is already passed
            if 'signals_df=' not in source and 'signals_df)' not in source:
                # Need to add signals_df parameter
                source = source.replace(
                    'backtester = DailyStraddleBacktester(',
                    'backtester = DailyStraddleBacktester(\n    signals_df=signals_df,  # Pass signals for type tracking'
                )

                # Also need to update __init__ to accept signals_df
                cell['source'] = [source]
                modifications.append(f"Cell {i}: Added signals_df to backtester instantiation")

# ===========================================================================
# STEP 6: Add __init__ parameter to DailyStraddleBacktester if needed
# ===========================================================================
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        if 'class DailyStraddleBacktester' in source and 'def __init__' in source:
            print(f"\nStep 6: Checking __init__ parameters (cell {i})")

            if 'signals_df' not in source.split('def run_backtest')[0]:  # Check only __init__ part
                # Add signals_df parameter to __init__
                lines = source.split('\n')
                new_lines = []

                for j, line in enumerate(lines):
                    if 'def __init__(self,' in line:
                        # Find the closing parenthesis
                        paren_line = j
                        while ')' not in lines[paren_line]:
                            paren_line += 1

                        # Add signals_df parameter before closing
                        if paren_line == j:
                            # Single line __init__
                            line = line.replace(')', ', signals_df=None)')
                        else:
                            # Multi-line - add before last line
                            new_lines.append(line)
                            for k in range(j + 1, paren_line):
                                new_lines.append(lines[k])
                            indent = len(lines[paren_line]) - len(lines[paren_line].lstrip())
                            new_lines.append(' ' * indent + 'signals_df=None,')
                            line = lines[paren_line]

                    # Add instance variable assignment
                    if 'self.time_stop_dte = time_stop_dte' in line:
                        new_lines.append(line)
                        indent = len(line) - len(line.lstrip())
                        new_lines.append(' ' * indent + 'self.signals_df = signals_df')
                        continue

                    new_lines.append(line)

                new_source = '\n'.join(new_lines)
                cell['source'] = [new_source]
                modifications.append(f"Cell {i}: Added signals_df parameter to __init__")

# Save notebook
print(f"\n{'='*70}")
print(f"Saving modified notebook...")
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"✓ Saved to {NOTEBOOK_PATH}")
print(f"\nModifications applied ({len(modifications)}):")
for mod in modifications:
    print(f"  • {mod}")

print("\n" + "="*70)
print("INTEGRATION COMPLETE")
print("="*70)
print(f"""
Next steps:
  1. Test the notebook:
     cd "/Users/janussuk/Desktop/Options Backtester"
     source .venv/bin/activate
     python -m pytest backtester/tests/test_notebook_07.py -v

  2. Or run notebook validation:
     python validate_notebook_integration.py

  3. Or open in Jupyter:
     jupyter notebook notebooks/07_enhanced_atm_straddle_strategy.ipynb
""")
