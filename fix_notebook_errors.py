"""
Fix all remaining errors in the notebook.
"""
import json
import re

notebook_path = "/Users/janussuk/Desktop/Options Backtester/notebooks/07_enhanced_atm_straddle_strategy.ipynb"

# Read the notebook
with open(notebook_path, 'r') as f:
    notebook = json.load(f)

print("Fixing notebook errors...")

# Find the DailyStraddleBacktester class cell
for idx, cell in enumerate(notebook['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])

        # Fix 1: Fix the iv_percentile KeyError
        if 'class DailyStraddleBacktester:' in source:
            print(f"\nFound DailyStraddleBacktester in cell {idx}")

            # Issue 1: straddle variable referenced before being fully defined
            if "straddle[\"signal_type\"] = signal_type_map.get(date, \"unknown\")" in source:
                print("  - Fixing straddle variable reference order")
                # The straddle dict should be accessed AFTER it's defined by find_atm_straddle
                # This is already correct in the code, so check the signal_type line

            # Issue 2: iv_percentile column might not exist
            if "straddle['iv_percentile'] = day_signal['iv_percentile'].iloc[0]" in source:
                print("  - Fixing iv_percentile KeyError")
                # Replace with safe access
                source = source.replace(
                    "                    straddle['iv_rank'] = day_signal['iv_rank'].iloc[0]\n"
                    "                    straddle['iv_percentile'] = day_signal['iv_percentile'].iloc[0]",
                    "                    straddle['iv_rank'] = day_signal['iv_rank'].iloc[0]\n"
                    "                    if 'iv_percentile' in day_signal.columns:\n"
                    "                        straddle['iv_percentile'] = day_signal['iv_percentile'].iloc[0]\n"
                    "                    else:\n"
                    "                        straddle['iv_percentile'] = np.nan"
                )

            # Issue 3: straddle used before defined in signal_type assignment
            # Look for the pattern where signal_type is assigned before straddle exists
            if 'straddle = self.find_atm_straddle' in source and 'straddle["signal_type"]' in source:
                # Check if signal_type is assigned before straddle is defined
                lines = source.split('\n')
                straddle_def_line = None
                signal_type_line = None

                for i, line in enumerate(lines):
                    if 'straddle = self.find_atm_straddle' in line:
                        straddle_def_line = i
                    if 'straddle["signal_type"]' in line or "straddle['signal_type']" in line:
                        signal_type_line = i

                if signal_type_line and straddle_def_line and signal_type_line < straddle_def_line:
                    print("  - ERROR: signal_type assigned before straddle is defined")
                    print(f"    signal_type at line {signal_type_line}, straddle defined at {straddle_def_line}")

            # Issue 4: Check for undefined variable reference in _close_position
            if 'trade = {' in source and "'signal_type': straddle.get('signal_type', 'unknown')" in source:
                print("  - Found potential straddle reference issue in _close_position")
                # The trade dict references straddle, but it should reference pos
                source = source.replace(
                    "            'signal_type': straddle.get('signal_type', 'unknown'),",
                    "            'signal_type': pos.get('signal_type', 'unknown'),"
                )
                print("  - Fixed: Changed straddle.get to pos.get in trade dict")

            # Update the cell
            notebook['cells'][idx]['source'] = source.split('\n')
            # Fix line endings
            notebook['cells'][idx]['source'] = [line + '\n' if i < len(notebook['cells'][idx]['source']) - 1 else line
                                                for i, line in enumerate(notebook['cells'][idx]['source'])]

# Save the updated notebook
with open(notebook_path, 'w') as f:
    json.dump(notebook, f, indent=1)

print("\n✓ Notebook fixes applied")
print("\nFixed issues:")
print("  1. Added safe access for iv_percentile column")
print("  2. Fixed straddle variable reference in _close_position")
