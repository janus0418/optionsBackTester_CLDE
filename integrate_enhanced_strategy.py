"""
Integrate enhanced multi-signal strategy into Notebook 07
Modifies the notebook cells to use enhanced functions
"""

import json
import sys
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/07_enhanced_atm_straddle_strategy.ipynb")

print("="*70)
print("INTEGRATING ENHANCED STRATEGY INTO NOTEBOOK 07")
print("="*70)

# Load notebook
print(f"\n1. Loading notebook: {NOTEBOOK_PATH}")
with open(NOTEBOOK_PATH, 'r') as f:
    notebook = json.load(f)

print(f"   ✓ Loaded {len(notebook['cells'])} cells")

# Find cells to modify
cells_modified = 0

# === CELL 8: IV Metrics Calculation ===
# Find cell with calculate_iv_metrics or IV calculation logic
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Look for IV calculation function definition
        if 'def calculate_iv_metrics' in source or ('iv_rank' in source and 'atm_iv' in source and 'def ' in source):
            print(f"\n2. Found IV calculation cell at index {i}")

            # Replace with enhanced version
            new_source = '''# === ENHANCED IV METRICS CALCULATION ===
# Using calculate_enhanced_iv_metrics() for comprehensive IV analysis

from enhanced_straddle_functions import calculate_enhanced_iv_metrics

print("\\nCalculating ENHANCED IV metrics...")
print("  - IV Rank (52-week)")
print("  - IV Trends (10d/20d slopes)")
print("  - Volatility-of-Volatility metrics")
print("  - IV Changes (1d, 5d, 10d)")
print("  - Moving averages and percentiles")

iv_df = calculate_enhanced_iv_metrics(options_data, spot_data, lookback_days=252)

print(f"✓ Calculated enhanced metrics for {len(iv_df)} days")
print(f"  Metrics per day: 21 (vs 8 in original)")

# Display first few rows
print("\\nSample metrics:")
display(iv_df[['date', 'spot', 'atm_iv', 'iv_rank', 'iv_trend_10d',
               'iv_trend_20d', 'iv_10d_std', 'iv_5d_change']].head())
'''
            cell['source'] = [new_source]
            cells_modified += 1
            print(f"   ✓ Replaced with calculate_enhanced_iv_metrics()")
            break

# === CELL 12: Entry Signal Generation ===
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Look for signal generation (IV_RANK_THRESHOLD or generate_entry_signals)
        if 'IV_RANK_THRESHOLD' in source or 'generate_entry_signals' in source or ('entry_signal' in source and 'iv_rank' in source):
            print(f"\n3. Found signal generation cell at index {i}")

            # Replace with multi-signal version
            new_source = '''# === MULTI-SIGNAL ENTRY GENERATION ===
# Three signal types: Spike Fade, Declining Trend, Stagnant IV

from enhanced_straddle_functions import generate_multi_signal_entries, get_signal_summary

print("\\nGenerating entry signals (3 types)...")
signals_df = generate_multi_signal_entries(iv_df)

# Get summary
summary = get_signal_summary(signals_df)

print("\\n" + "="*70)
print("ENTRY SIGNAL SUMMARY")
print("="*70)
print(f"Total Days Analyzed:      {summary['total_days']:4d}")
print(f"")
print(f"Signal Type Breakdown:")
print(f"  Spike Fade:            {summary['spike_fade']:4d}  ({summary.get('spike_fade_pct', 0):5.1f}%)")
print(f"  Declining Trend:       {summary['declining_trend']:4d}  ({summary.get('declining_trend_pct', 0):5.1f}%)")
print(f"  Stagnant IV:           {summary['stagnant_iv']:4d}  ({summary.get('stagnant_iv_pct', 0):5.1f}%)")
print(f"  " + "-"*40)
print(f"  TOTAL Entry Signals:   {summary['total_signals']:4d}  ({summary.get('total_signals_pct', 0):5.1f}%)")

# Extract entry dates
entry_signals = signals_df[signals_df['entry_signal'] == True].copy()
entry_dates = entry_signals['date'].tolist()

print(f"\\nFirst 10 Entry Signals:")
print(f"{'Date':<12} {'Type':<20} {'IV':>7} {'IVR':>5} {'5d Chg':>7}")
print("-"*60)
for idx, row in entry_signals.head(10).iterrows():
    print(f"{row['date'].strftime('%Y-%m-%d'):<12} {row['signal_type']:<20} "
          f"{row['atm_iv']:>6.1%} {row['iv_rank']:>4.0f}% {row['iv_5d_change']:>+6.1%}")
'''
            cell['source'] = [new_source]
            cells_modified += 1
            print(f"   ✓ Replaced with generate_multi_signal_entries()")
            break

# === FIND BACKTESTER CLASS ===
# Look for DailyStraddleBacktester class definition to add signal_type tracking
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        if 'class DailyStraddleBacktester' in source:
            print(f"\n4. Found DailyStraddleBacktester class at index {i}")

            # Check if signal_type tracking is already added
            if 'signal_type' in source and "'signal_type':" in source:
                print(f"   ✓ Signal type tracking already present")
            else:
                # Add signal_type tracking
                # Find the line where trade dict is created and add signal_type
                modified_source = source

                # Add signal_type to trade dictionary
                if "'entry_date': exit_date" in source:
                    modified_source = source.replace(
                        "'entry_date': exit_date,",
                        "'entry_date': exit_date,\n                    'signal_type': straddle.get('signal_type', 'unknown'),"
                    )
                elif "trades.append({" in source:
                    # Find the trades.append section and add signal_type
                    lines = source.split('\n')
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if "'exit_price':" in line or "'net_pnl':" in line:
                            indent = len(line) - len(line.lstrip())
                            new_lines.append(' ' * indent + "'signal_type': straddle.get('signal_type', 'unknown'),")
                            break
                    modified_source = '\n'.join(new_lines)

                cell['source'] = [modified_source]
                cells_modified += 1
                print(f"   ✓ Added signal_type tracking to backtester")
            break

# === ADD NEW CELL: Signal Type Performance Analysis ===
# Find the cell after backtest results visualization
insert_index = None
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'Performance Metrics' in source or 'trades_df' in source:
            insert_index = i + 1

if insert_index:
    print(f"\n5. Adding signal type performance analysis cell at index {insert_index}")

    new_cell = {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [],
        'source': ['''# === PERFORMANCE BY SIGNAL TYPE ===

if len(trades_df) > 0 and 'signal_type' in trades_df.columns:
    print("\\n" + "="*70)
    print("PERFORMANCE BY SIGNAL TYPE")
    print("="*70)

    for signal_type in ['spike_fade', 'declining_trend', 'stagnant_iv']:
        signal_trades = trades_df[trades_df['signal_type'] == signal_type]

        if len(signal_trades) > 0:
            win_rate = (signal_trades['net_pnl'] > 0).mean()
            avg_pnl = signal_trades['net_pnl'].mean() * 100
            total_pnl = signal_trades['net_pnl'].sum() * 100
            max_win = signal_trades['net_pnl'].max() * 100
            max_loss = signal_trades['net_pnl'].min() * 100

            print(f"\\n{signal_type.upper().replace('_', ' ')}:")
            print(f"  Trades:         {len(signal_trades):3d}")
            print(f"  Win Rate:       {win_rate:>6.1%}")
            print(f"  Avg P&L:        ${avg_pnl:>7.2f}")
            print(f"  Total P&L:      ${total_pnl:>7.2f}")
            print(f"  Max Win:        ${max_win:>7.2f}")
            print(f"  Max Loss:       ${max_loss:>7.2f}")

    # Visualization: P&L by signal type
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Average P&L by signal type
    signal_summary = trades_df.groupby('signal_type')['net_pnl'].agg(['mean', 'count']).reset_index()
    signal_summary['mean'] *= 100  # Convert to dollars

    ax1 = axes[0]
    bars = ax1.bar(signal_summary['signal_type'], signal_summary['mean'], color=['#e74c3c', '#3498db', '#f39c12'])
    ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax1.set_xlabel('Signal Type')
    ax1.set_ylabel('Average P&L per Trade ($)')
    ax1.set_title('Average P&L by Signal Type')
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'${height:.2f}', ha='center', va='bottom' if height > 0 else 'top')

    # Plot 2: Win rate by signal type
    win_rates = trades_df.groupby('signal_type').apply(lambda x: (x['net_pnl'] > 0).mean() * 100).reset_index()
    win_rates.columns = ['signal_type', 'win_rate']

    ax2 = axes[1]
    bars2 = ax2.bar(win_rates['signal_type'], win_rates['win_rate'], color=['#e74c3c', '#3498db', '#f39c12'])
    ax2.axhline(y=50, color='gray', linestyle='--', linewidth=1, alpha=0.5, label='50% (Random)')
    ax2.set_xlabel('Signal Type')
    ax2.set_ylabel('Win Rate (%)')
    ax2.set_title('Win Rate by Signal Type')
    ax2.set_ylim(0, 100)
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend()

    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom')

    plt.tight_layout()
    plt.show()
else:
    print("\\nNo signal_type column found in trades_df. Run backtest with enhanced signals.")
''']
    }

    notebook['cells'].insert(insert_index, new_cell)
    cells_modified += 1
    print(f"   ✓ Added signal type performance analysis cell")

# === UPDATE TITLE CELL ===
for i, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        if '# Daily Short ATM Straddle' in source or '# Enhanced Multi-Signal ATM Straddle' in source:
            print(f"\n6. Updating title cell at index {i}")

            # Update title if not already updated
            if 'Enhanced Multi-Signal' not in source:
                new_title = source.replace('# Daily Short ATM Straddle', '# Enhanced Multi-Signal ATM Straddle')
                cell['source'] = [new_title]
                cells_modified += 1
                print(f"   ✓ Updated title to Enhanced Multi-Signal")
            else:
                print(f"   ✓ Title already updated")
            break

# Save modified notebook
print(f"\n7. Saving modified notebook...")
with open(NOTEBOOK_PATH, 'w') as f:
    json.dump(notebook, f, indent=1)

print(f"   ✓ Saved to {NOTEBOOK_PATH}")

print(f"\n" + "="*70)
print("INTEGRATION COMPLETE")
print("="*70)
print(f"  Cells modified: {cells_modified}")
print(f"  Total cells: {len(notebook['cells'])}")
print(f"")
print(f"Next steps:")
print(f"  1. Open the notebook in Jupyter")
print(f"  2. Run all cells (Cell -> Run All)")
print(f"  3. Review the enhanced backtest results")
print(f"  4. Analyze performance by signal type")
print("="*70)
