"""
Fix all bugs in Notebook 07
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")

print("="*70)
print("FIXING NOTEBOOK 07 BUGS")
print("="*70)

# Load notebook
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"\nLoaded {len(notebook['cells'])} cells")

fixes_applied = 0

# Fix each cell
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        original_source = source

        # FIX 1: Remove display() calls in Cell 8 (IV metrics)
        if 'display(iv_df' in source and 'calculate_enhanced_iv_metrics' in source:
            print(f"\n{i}. Fixing Cell {i}: Removing display() from IV metrics cell")
            # Replace display() with print()
            source = source.replace(
                "display(iv_df[['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d',\n               'iv_trend_20d', 'iv_10d_std', 'iv_5d_change']].head())",
                "print(iv_df[['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d',\n              'iv_trend_20d', 'iv_10d_std', 'iv_5d_change']].head())"
            )
            fixes_applied += 1

        # FIX 2: Ensure entry_dates is properly set from signals_df
        if 'generate_multi_signal_entries' in source and 'signals_df' in source:
            print(f"\n{i}. Fixing Cell {i}: Ensuring entry_dates is set correctly")
            if 'entry_dates = entry_signals' not in source and 'entry_signals = signals_df' not in source:
                # Make sure entry_dates is extracted
                if 'entry_dates' not in source:
                    source = source + "\n\n# Extract entry dates for backtesting\nentry_dates = signals_df[signals_df['entry_signal'] == True]['date'].tolist()"
                    fixes_applied += 1

        # FIX 3: Fix signal_type assignment in backtester
        if 'class DailyStraddleBacktester' in source:
            print(f"\n{i}. Fixing Cell {i}: Ensuring signal_type tracking works properly")

            # Check if we need to fix the signal_type assignment
            if "'signal_type':" in source or '"signal_type":' in source:
                # Already has signal_type, but let's make sure it's correct
                if "straddle.get('signal_type'" not in source:
                    # Need to fix how signal_type is accessed
                    source = source.replace(
                        "'signal_type': signal_type,",
                        "'signal_type': straddle.get('signal_type', 'unknown'),"
                    )
                    fixes_applied += 1
            else:
                # Need to add signal_type tracking
                # Find where trades dict is created and add signal_type
                if "'net_pnl':" in source and "'signal_type':" not in source:
                    lines = source.split('\n')
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        # Add after net_pnl line
                        if "'net_pnl':" in line and 'net_pnl' in line:
                            indent = len(line) - len(line.lstrip())
                            new_lines.append(' ' * indent + "'signal_type': straddle.get('signal_type', 'unknown'),")
                    source = '\n'.join(new_lines)
                    fixes_applied += 1

        # FIX 4: Ensure straddle dictionary has signal_type when created
        if 'def find_atm_straddle' in source or 'atm_straddle = {' in source:
            print(f"\n{i}. Checking Cell {i}: ATM straddle creation")
            # This is OK - signal_type is added later in run_backtest

        # FIX 5: Fix the backtest loop to add signal_type to straddles
        if 'for date in self.dates:' in source and 'if date in entry_dates_set:' in source:
            print(f"\n{i}. Fixing Cell {i}: Adding signal_type to straddles in backtest loop")

            # Check if signal_type is being added to straddle dict
            if "straddle['signal_type']" not in source:
                # Need to add code to assign signal_type from signals_df
                # Find the line after straddle is found
                lines = source.split('\n')
                new_lines = []
                for j, line in enumerate(lines):
                    new_lines.append(line)
                    # After finding straddle, add signal_type
                    if 'straddle = self.find_atm_straddle' in line:
                        # Look ahead to see if there's an 'if straddle:' check
                        indent = len(line) - len(line.lstrip())
                        # Add signal_type assignment
                        new_lines.append(' ' * (indent + 4) + "if straddle and date in signals_df['date'].values:")
                        new_lines.append(' ' * (indent + 8) + "signal_row = signals_df[signals_df['date'] == date].iloc[0]")
                        new_lines.append(' ' * (indent + 8) + "straddle['signal_type'] = signal_row.get('signal_type', 'unknown')")
                source = '\n'.join(new_lines)
                fixes_applied += 1

        # Update cell source if changed
        if source != original_source:
            cell['source'] = [source]

# Save fixed notebook
print(f"\n{'='*70}")
print(f"Saving fixed notebook...")
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"✓ Saved to {NOTEBOOK_PATH}")
print(f"\nFixes applied: {fixes_applied}")
print("="*70)
